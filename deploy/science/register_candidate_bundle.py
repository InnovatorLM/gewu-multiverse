#!/usr/bin/env python3
"""Operator handoff of one frozen author task to all three diagnostic routes.

Consumes existing source-bound build publication; does not build or run models,
accept tasks, or merge. Registry publication is one atomic replacement.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys

from evaluation_queue import W, atomic_json, digest_tree, evaluation_catalog, root_file, validated_template
from register_evaluation import freeze
from build_task_images import validate_build_receipt
from register_semantic_diagnostic import registered_corpus
from role_exec import trusted
from check_harbor_task import inspect_task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['evaluation-id', 'repo', 'commit', 'task-path', 'template', 'build-receipt', 'corpus']:
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--disabled', action='store_true', help='Register without enabling dispatch; omit all three routes from catalog')
    args = parser.parse_args()
    if os.geteuid() != 0 or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,51}', args.evaluation_id):
        raise ValueError('Require operator and a short immutable bundle ID')
    def interrupted(signum, frame):
        raise InterruptedError('Candidate handoff interrupted')
    for signum in [signal.SIGTERM, signal.SIGINT]:
        signal.signal(signum, interrupted)
    queue = json.loads(root_file(W / '.config/science-evaluation/queue.json').read_text())
    state = trusted(queue['state'], directory=True)
    ids = [args.evaluation_id, args.evaluation_id + '-quality', args.evaluation_id + '-semantic']
    reviews = trusted(W / '.state/science-review-tools', directory=True)
    review_root = reviews / ('bundle-' + args.evaluation_id)
    parent = state / 'registered' / args.evaluation_id
    with (state / 'registration.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        registry_path = root_file(queue['registry'])
        registry = json.loads(registry_path.read_text())
        if any(key in registry for key in ids) or parent.exists() or review_root.exists():
            raise ValueError('Bundle IDs and destinations must be fresh')
        corpus = trusted(args.corpus, directory=True)
        semantic = {'reference_corpus': str(corpus), 'corpus_manifest_sha256': hashlib.sha256(root_file(corpus / 'manifest.json').read_bytes()).hexdigest()}
        registered_corpus(semantic)
        parent.mkdir(mode=0o700)
        persisted = False
        try:
            snapshot = parent / Path(args.task_path).name
            sha = freeze(args.repo, args.commit, args.task_path, snapshot)
            atomic_json(parent / 'mechanical-check.json', inspect_task(snapshot))
            template = json.loads(root_file(args.template).read_text())
            template['datasets'] = [{'path': str(parent), 'task_names': [snapshot.name]}]
            receipt = json.loads(root_file(args.build_receipt).read_text())
            validate_build_receipt(receipt, snapshot, args.commit, args.task_path, template)
            atomic_json(parent / 'template.json', template)
            atomic_json(parent / 'build-receipt.json', receipt)
            entry = {'snapshot': str(snapshot), 'snapshot_sha256': sha, 'template': str(parent / 'template.json'), 'template_sha256': hashlib.sha256((parent / 'template.json').read_bytes()).hexdigest(), 'source_commit': args.commit, 'source_task_path': args.task_path, 'build_receipt_sha256': hashlib.sha256((parent / 'build-receipt.json').read_bytes()).hexdigest(), 'enabled': not args.disabled}
            entry['mechanical_check_sha256'] = hashlib.sha256((parent / 'mechanical-check.json').read_bytes()).hexdigest()
            validated_template(entry, {'snapshot_sha256': sha})
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_review_chroot.py')), '--tools-only', '--uid', '21012', '--root', str(review_root), '--task', str(snapshot)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
            (parent / 'review-root-preparation.log').write_bytes(result.stdout + b'\n' + result.stderr)
            (parent / 'review-root-preparation.log').chmod(0o600)
            if result.returncode or digest_tree(review_root / 'task') != sha:
                raise ValueError('Credential-free review root preparation failed')
            # Recheck all inputs after the potentially slow preparation step.
            validated_template(entry, {'snapshot_sha256': sha})
            registered_corpus(semantic)
            entries = {ids[0]: entry,
                       ids[1]: {**entry, 'dispatch': 'quality_diagnostic', 'review_root': str(review_root), 'source_evaluation_id': ids[0]},
                       ids[2]: {**entry, **semantic, 'dispatch': 'semantic_diagnostic', 'source_evaluation_id': ids[0]}}
            atomic_json(parent / 'provenance.json', {**entry, 'bundle_ids': ids, 'scientific_acceptance': False})
            registry.update(entries)
            # A handled signal between rename and persisted=True must not delete
            # evidence already referenced by the durable registry.
            previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM, signal.SIGINT})
            try:
                atomic_json(registry_path, registry)
                persisted = True
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            # If this projection fails, keep registered evidence for catalog repair.
            atomic_json(Path(queue['inbox']).parent / 'catalog.json', evaluation_catalog(registry), 0o644)
        except BaseException:
            if not persisted:
                shutil.rmtree(parent)
                if review_root.exists():
                    shutil.rmtree(review_root)
            raise
    print(json.dumps({'evaluation_ids': ids, 'snapshot_sha256': sha, 'enabled': not args.disabled, 'scientific_acceptance': False, 'model_calls': 0, 'acs_launched': False}))


if __name__ == '__main__':
    main()
