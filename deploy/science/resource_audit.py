#!/usr/bin/env python3
"""Read-only ACS resource audit. Never deletes resources or prints credentials."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

WORKSPACE = Path('/mnt/data/zhanglinfeng/workspace')
KINDS = ('pods', 'sandboxsets', 'sandboxclaims', 'sandboxes')


def summarize(snapshot):
    result = {}
    for kind in KINDS:
        result[kind] = []
        for obj in snapshot.get(kind, []):
            meta = obj.get('metadata', {})
            result[kind].append({
                'name': meta.get('name'), 'uid': meta.get('uid'),
                'run_id': meta.get('labels', {}).get('evaluation-run'),
                'created_at': meta.get('creationTimestamp'),
                'deleting': bool(meta.get('deletionTimestamp')),
                'phase': obj.get('status', {}).get('phase'),
            })
    return result


def inventory(cluster, kind):
    from kubernetes.client.exceptions import ApiException
    result, token = [], ''
    while True:
        query = [('limit', 200)]
        if token:
            query.append(('continue', token))
        try:
            data = cluster.call(cluster.path(kind), query=query)
        except ApiException as exc:
            if kind != 'pods' and exc.status == 404:
                return []
            raise
        result.extend(data.get('items', []))
        token = data.get('metadata', {}).get('continue', '')
        if not token:
            return result


def bounded_path(raw):
    path = Path(raw).resolve()
    if not path.is_relative_to(WORKSPACE):
        raise ValueError('All paths must be inside workspace')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kubeconfig', default=str(WORKSPACE / '.config/acs/kubeconfig'))
    parser.add_argument('--namespace', default='default')
    parser.add_argument('--run-id', action='append', default=[])
    parser.add_argument('--out', required=True)
    parser.add_argument('--watch', action='store_true', help='Repeat until interrupted; never cleans automatically')
    parser.add_argument('--interval', type=int, default=300)
    args = parser.parse_args()
    if args.interval < 30:
        parser.error('interval must be >=30 seconds')
    out = bounded_path(args.out)
    kubeconfig = bounded_path(args.kubeconfig)
    spec = importlib.util.spec_from_file_location('acs_guard', WORKSPACE / '.agents/skills/acs-harbor-eval/scripts/run_guard.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    status = 0
    try:
        while True:
            report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
                      'read_only': True, 'namespace': args.namespace, 'confirmed': False}
            try:
                cluster = module.Cluster(str(kubeconfig), args.namespace)
                if args.run_id:
                    snapshots = {run: summarize(cluster.snapshot(run)) for run in args.run_id}
                else:
                    # Inventory is read-only. An unlabeled/other job is never cleanup-authorized.
                    snapshots = {'inventory': summarize({kind: inventory(cluster, kind) for kind in KINDS})}
                    report['scope'] = 'all namespace resources; read-only; unrelated resources are never cleanup-authorized'
                report['resources'] = snapshots
                report['confirmed'] = True
                report['empty'] = not any(items for snap in snapshots.values() for items in snap.values())
                status = 0 if report['empty'] else 2
            except Exception as exc:
                report['error_type'] = type(exc).__name__
                status = 1
            temp = out.with_name(out.name + '.new')
            with temp.open('w') as f:
                os.chmod(temp, 0o600)
                json.dump(report, f, indent=2)
            temp.replace(out)
            print(json.dumps({'report': str(out), 'confirmed': report['confirmed'], 'empty': report.get('empty'), 'exit_status': status}), flush=True)
            if not args.watch:
                return status
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return status


if __name__ == '__main__':
    sys.exit(main())
