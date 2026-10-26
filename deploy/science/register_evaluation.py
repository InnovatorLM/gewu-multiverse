#!/usr/bin/env python3
"""Operator-only immutable registration from a Git commit; never builds images."""
import argparse
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile

from evaluation_queue import W, atomic_json, digest_tree, root_file, validated_template


def freeze(repo, commit, task_path, destination):
    repo = Path(repo).resolve(strict=True)
    destination = Path(destination)
    if not repo.is_relative_to(W) or not destination.resolve().is_relative_to(W):
        raise ValueError('Paths must remain in workspace')
    parts = PurePosixPath(task_path)
    if parts.is_absolute() or '..' in parts.parts or not parts.parts:
        raise ValueError('Require a relative task directory')
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Require a full immutable Git commit hash')
    resolved = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', commit + '^{commit}'], text=True).strip()
    if resolved != commit:
        raise ValueError('Commit mismatch')
    data = subprocess.check_output(['git', '-C', str(repo), 'archive', '--format=tar', commit, '--', task_path])
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members = archive.getmembers()
        selected = []
        total = 0
        for item in members:
            name = PurePosixPath(item.name)
            if name.is_absolute() or '..' in name.parts or not (item.isdir() or item.isfile()):
                raise ValueError('Git archive links/special paths refused')
            if name == parts or parts in name.parents:
                relative = name.relative_to(parts)
                if relative.parts:
                    selected.append((item, relative))
                    total += item.size
        if total > 128 * 1024 * 1024 or len(selected) > 10000:
            raise ValueError('Task exceeds registration size limit')
        files = {str(relative) for item, relative in selected if item.isfile()}
        if not {'instruction.md', 'task.toml', 'environment/Dockerfile', 'tests/test.sh', 'solution/solve.sh'} <= files:
            raise ValueError('Missing standard Harbor task files')
        destination.mkdir(mode=0o700)
        try:
            for item, relative in selected:
                target = destination.joinpath(*relative.parts)
                if item.isdir():
                    target.mkdir(parents=True, exist_ok=True, mode=0o700)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    with archive.extractfile(item) as source, target.open('xb') as output:
                        shutil.copyfileobj(source, output)
                    target.chmod(0o700 if item.mode & 0o111 else 0o600)
            return digest_tree(destination)
        except BaseException:
            shutil.rmtree(destination)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['evaluation-id', 'repo', 'commit', 'task-path', 'template']:
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Operator/root required')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', args.evaluation_id):
        raise ValueError('Invalid evaluation ID')
    settings = W / '.config/science-evaluation'
    config = json.loads(root_file(settings / 'queue.json').read_text())
    state = Path(config['state'])
    with (state / 'registration.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        registry_path = root_file(config['registry'])
        registry = json.loads(registry_path.read_text())
        if args.evaluation_id in registry:
            raise ValueError('Evaluation ID is already registered')
        parent = state / 'registered' / args.evaluation_id
        parent.mkdir(mode=0o700)
        try:
            name = PurePosixPath(args.task_path).name
            snapshot = parent / name
            sha = freeze(args.repo, args.commit, args.task_path, snapshot)
            template = json.loads(root_file(args.template).read_text())
            template['datasets'] = [{'path': str(parent), 'task_names': [name]}]
            template_path = parent / 'template.json'
            atomic_json(template_path, template)
            entry = {'snapshot': str(snapshot), 'snapshot_sha256': sha, 'template': str(template_path), 'template_sha256': hashlib.sha256(template_path.read_bytes()).hexdigest(), 'source_commit': args.commit, 'source_task_path': args.task_path}
            validated_template(entry, {'snapshot_sha256': sha})
            atomic_json(parent / 'provenance.json', {**entry, 'scientific_acceptance': False})
            registry[args.evaluation_id] = entry
            atomic_json(registry_path, registry)
        except BaseException:
            shutil.rmtree(parent)
            raise
        catalog = Path(config['inbox']).parent / 'catalog.json'
        atomic_json(catalog, {'evaluations': [{'evaluation_id': key, 'snapshot_sha256': value['snapshot_sha256'], 'purpose': 'registered solver evidence; not scientific acceptance'} for key, value in sorted(registry.items())]}, 0o644)
    print(json.dumps({'evaluation_id': args.evaluation_id, 'snapshot_sha256': sha, 'scientific_acceptance': False}))


if __name__ == '__main__':
    main()
