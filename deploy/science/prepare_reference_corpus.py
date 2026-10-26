#!/usr/bin/env python3
"""Freeze official benchmark instructions from explicit local Git commits.

Contains no model judgments. A complete instruction corpus is not proof of
semantic novelty, and must not be represented as a completed novelty review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from evaluation_queue import W, atomic_json


def corpus(repo, commit, dataset, scope="active"):
    if scope not in {"active", "all"}:
        raise ValueError("Unknown corpus selection scope")
    repo = Path(repo).resolve(strict=True)
    if not repo.is_relative_to(W) or not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Require workspace repository and full commit')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args])
    if git('rev-parse', commit + '^{commit}').decode().strip() != commit:
        raise ValueError('Invalid commit')
    records = []
    for item in git('ls-tree', '-rz', '--full-tree', commit).split(b'\0'):
        if not item:
            continue
        metadata, raw_path = item.split(b'\t', 1)
        path = raw_path.decode('utf-8')
        if not path.endswith('/instruction.md') or (scope == 'active' and not path.startswith('tasks/')):
            continue
        mode, kind, oid = metadata.decode().split()
        if kind != 'blob' or mode not in {'100644', '100755'}:
            raise ValueError('Instruction must be a regular Git blob')
        data = git('cat-file', 'blob', oid)
        records.append({'dataset': dataset, 'commit': commit, 'path': path, 'git_blob': oid, 'sha256': hashlib.sha256(data).hexdigest(), 'instruction': data.decode('utf-8')})
    if not records:
        raise ValueError('No benchmark instructions found')
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tb4-commit', required=True)
    parser.add_argument('--science-commit', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--scope', choices=['active','all'], default='active', help='Default: only tasks/; all includes fixtures, templates and history')
    args = parser.parse_args()
    output = Path(args.output)
    if not output.resolve().is_relative_to(W) or output.exists():
        raise ValueError('Require a fresh private workspace output directory')
    records = []
    counts = {}
    for name, commit in [('terminal-bench-4.0', args.tb4_commit), ('terminal-bench-science-v0.1', args.science_commit)]:
        rows = corpus(W / 'datasets' / name, commit, name, args.scope)
        records.extend(rows)
        counts[name] = len(rows)
    output.mkdir(mode=0o700)
    atomic_json(output / 'instructions.json', records)
    atomic_json(output / 'manifest.json', {'sources': counts, 'instructions_sha256': hashlib.sha256((output / 'instructions.json').read_bytes()).hexdigest(), 'scientific_acceptance': False, 'semantic_review_performed': False, 'selection_scope': args.scope, 'scope': 'tracked tasks/**/instruction.md at explicit source commits' if args.scope == 'active' else 'all tracked instructions including fixtures/templates/history'})
    print(json.dumps({'counts': counts, 'semantic_review_performed': False}))


if __name__ == '__main__':
    main()
