#!/usr/bin/env python3
"""Bind a fixed benchmark corpus to an existing immutable solver task."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
from evaluation_queue import W, atomic_json, evaluation_catalog, root_file, validated_template
from role_exec import trusted
from semantic_comparison import load_corpus


def registered_corpus(entry):
    corpus=trusted(entry['reference_corpus'],directory=True)
    if not corpus.is_relative_to(W):raise ValueError('Corpus must be workspace-local')
    manifest=root_file(corpus/'manifest.json')
    if hashlib.sha256(manifest.read_bytes()).hexdigest()!=entry['corpus_manifest_sha256']:raise ValueError('Registered benchmark manifest changed')
    load_corpus(corpus)
    return corpus


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-evaluation-id',required=True)
    parser.add_argument('--evaluation-id',required=True)
    parser.add_argument('--corpus',type=Path,required=True)
    args=parser.parse_args()
    if os.geteuid()!=0 or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',args.evaluation_id):raise ValueError('Require operator and valid new ID')
    queue=json.loads(root_file(W/'.config/science-evaluation/queue.json').read_text())
    with (Path(queue['state'])/'registration.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        registry_path=root_file(queue['registry']);registry=json.loads(registry_path.read_text())
        if args.evaluation_id in registry:raise ValueError('Registered IDs cannot be overwritten')
        entry=dict(registry[args.source_evaluation_id])
        if entry.get('dispatch','solver')!='solver':raise ValueError('Require solver source registration')
        validated_template(entry,{'snapshot_sha256':entry['snapshot_sha256']})
        corpus=trusted(args.corpus,directory=True)
        entry.update(dispatch='semantic_diagnostic',reference_corpus=str(corpus),corpus_manifest_sha256=hashlib.sha256(root_file(corpus/'manifest.json').read_bytes()).hexdigest(),source_evaluation_id=args.source_evaluation_id)
        registered_corpus(entry)
        registry[args.evaluation_id]=entry;atomic_json(registry_path,registry)
        atomic_json(Path(queue['inbox']).parent/'catalog.json',evaluation_catalog(registry),0o644)
    print(json.dumps({'evaluation_id':args.evaluation_id,'dispatch':'semantic_diagnostic','scientific_acceptance':False}))


if __name__=='__main__':main()
