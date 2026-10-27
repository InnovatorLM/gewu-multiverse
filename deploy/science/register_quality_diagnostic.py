#!/usr/bin/env python3
"""Register quality-diagnostic dispatch for an existing frozen solver snapshot."""
import argparse
import fcntl
import json
import hashlib
import os
from pathlib import Path
import re
from evaluation_queue import W, atomic_json, evaluation_catalog, digest_tree, root_file, validated_template
from role_exec import trusted


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-evaluation-id',required=True)
    parser.add_argument('--evaluation-id',required=True)
    backend=parser.add_mutually_exclusive_group(required=True)
    backend.add_argument('--review-root',type=Path)
    backend.add_argument('--acs-settings',type=Path)
    args=parser.parse_args()
    if os.geteuid()!=0 or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',args.evaluation_id):
        raise ValueError('Require operator and valid registration ID')
    queue=json.loads(root_file(W/'.config/science-evaluation/queue.json').read_text())
    state=Path(queue['state'])
    with (state/'registration.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        registry_path=root_file(queue['registry']);registry=json.loads(registry_path.read_text())
        if args.evaluation_id in registry:raise ValueError('Registered IDs cannot be overwritten')
        entry=dict(registry[args.source_evaluation_id])
        if entry.get('dispatch','solver')!='solver':raise ValueError('Require an existing solver snapshot registration')
        template=validated_template(entry,{'snapshot_sha256':entry['snapshot_sha256']})
        if args.acs_settings is not None:
            from run_acs_quality import load_settings
            path=root_file(args.acs_settings)
            settings,task=load_settings(path)
            if (settings['task_sha256']!=entry['snapshot_sha256'] or task.resolve()!=Path(entry['snapshot']).resolve()
                    or settings['runtime_image']!=template['environment']['kwargs']['runtime_image']):
                raise ValueError('ACS quality task does not match registered source snapshot')
            entry.update(quality_backend='acs',acs_quality_settings=str(path),
                         acs_quality_settings_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        else:
            root=trusted(args.review_root,directory=True)
            if not root.is_relative_to(W/'.state/science-review-tools') or digest_tree(root/'task')!=entry['snapshot_sha256']:
                raise ValueError('Review root does not match frozen source snapshot')
            entry.update(quality_backend='chroot',review_root=str(root))
        entry.update(dispatch='quality_diagnostic',source_evaluation_id=args.source_evaluation_id)
        registry[args.evaluation_id]=entry
        atomic_json(registry_path,registry)
        catalog=Path(queue['inbox']).parent/'catalog.json'
        atomic_json(catalog,evaluation_catalog(registry),0o644)
    print(json.dumps({'evaluation_id':args.evaluation_id,'dispatch':'quality_diagnostic','scientific_acceptance':False}))


if __name__=='__main__':main()
