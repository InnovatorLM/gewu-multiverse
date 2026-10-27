#!/usr/bin/env python3
"""Register an immutable public-task ACS diagnostic without inventing build labels.

This registration never grants solver eligibility, scientific acceptance or launch
approval. It binds task bytes directly to an existing local Git commit archive.
"""
import argparse
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile

from evaluation_queue import W, atomic_json, digest_tree, evaluation_catalog, root_file
from run_acs_quality import load_settings


def source_inventory(repo, commit, task_path):
    repo = Path(repo).resolve(strict=True)
    parts = PurePosixPath(task_path)
    if (not repo.is_relative_to(W) or not re.fullmatch('[a-f0-9]{40}', commit)
            or parts.is_absolute() or '..' in parts.parts or not parts.parts):
        raise ValueError('Require workspace repository and immutable source identity')
    # Run Git as the checkout's owner; do not change global safe.directory policy.
    owner = repo.stat().st_uid
    prefix = [] if owner == os.geteuid() else ['setpriv', '--reuid=' + str(owner),
                                             '--regid=' + str(repo.stat().st_gid), '--clear-groups']
    command = prefix + ['/usr/bin/git', '-C', str(repo)]
    env = os.environ.copy()
    env.update(XDG_CONFIG_HOME=str(W / '.config'), GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
    actual = subprocess.check_output(command + ['rev-parse', commit + '^{commit}'], text=True, env=env).strip()
    if actual != commit:
        raise ValueError('Source commit mismatch')
    raw = subprocess.check_output(command + ['archive', '--format=tar', commit, '--', task_path], env=env)
    records = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as bundle:
        for member in bundle:
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts or not (member.isdir() or member.isfile()):
                raise ValueError('Source archive links or special files refused')
            if member.isfile() and parts in name.parents:
                relative = name.relative_to(parts).as_posix()
                if relative in records:
                    raise ValueError('Duplicate source member')
                records[relative] = hashlib.sha256(bundle.extractfile(member).read()).hexdigest()
    if not records:
        raise ValueError('No source task files')
    return records


def task_inventory(task):
    digest_tree(task)  # Refuse links and special files before reading.
    return {path.relative_to(task).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(task.rglob('*')) if path.is_file()}


def validate_registration(entry, request):
    if (entry.get('registration_kind') != 'source_bound_quality_v1'
            or entry.get('dispatch') != 'quality_diagnostic' or entry.get('quality_backend') != 'acs'
            or request['snapshot_sha256'] != entry['snapshot_sha256']):
        raise ValueError('ACS quality registration identity mismatch')
    settings_path = root_file(entry['acs_quality_settings'])
    if hashlib.sha256(settings_path.read_bytes()).hexdigest() != entry['acs_quality_settings_sha256']:
        raise ValueError('ACS quality settings changed')
    settings, task = load_settings(settings_path)
    if (str(task.resolve()) != entry['snapshot'] or settings['task_sha256'] != entry['snapshot_sha256']
            or settings['runtime_image'] != entry['runtime_image']):
        raise ValueError('Registered task or runtime differs')
    provenance_raw = root_file(entry['quality_provenance']).read_bytes()
    if hashlib.sha256(provenance_raw).hexdigest() != entry['quality_provenance_sha256']:
        raise ValueError('Source provenance changed')
    provenance = json.loads(provenance_raw)
    if (provenance.get('source_commit') != entry['source_commit']
            or provenance.get('source_task_path') != entry['source_task_path']
            or provenance.get('snapshot_sha256') != entry['snapshot_sha256']
            or provenance.get('scientific_acceptance') is not False
            or task_inventory(task) != provenance.get('source_files')):
        raise ValueError('Source provenance does not match task bytes')
    return settings, task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-id', required=True)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--task-path', required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}', args.evaluation_id):
        raise ValueError('Operator and valid evaluation ID required')
    settings_path = root_file(args.settings)
    settings, task = load_settings(settings_path)
    source = source_inventory(args.repo, args.commit, args.task_path)
    if source != task_inventory(task):
        raise ValueError('Task differs from original public source commit')
    queue = json.loads(root_file(W / '.config/science-evaluation/queue.json').read_text())
    state = Path(queue['state'])
    with (state / 'registration.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        registry_path = root_file(queue['registry'])
        registry = json.loads(registry_path.read_text())
        if args.evaluation_id in registry:
            raise ValueError('Immutable evaluation ID already registered')
        directory = state / 'registered' / args.evaluation_id
        directory.mkdir(mode=0o700)
        provenance = directory / 'quality-provenance.json'
        atomic_json(provenance, {'source_commit': args.commit, 'source_task_path': args.task_path,
                    'source_repository': str(args.repo.resolve()), 'source_files': source,
                    'snapshot_sha256': settings['task_sha256'], 'scientific_acceptance': False})
        entry = {'registration_kind': 'source_bound_quality_v1', 'dispatch': 'quality_diagnostic',
                 'quality_backend': 'acs', 'snapshot': str(task.resolve()),
                 'snapshot_sha256': settings['task_sha256'], 'runtime_image': settings['runtime_image'],
                 'acs_quality_settings': str(settings_path),
                 'acs_quality_settings_sha256': hashlib.sha256(settings_path.read_bytes()).hexdigest(),
                 'source_commit': args.commit, 'source_task_path': args.task_path,
                 'quality_provenance': str(provenance),
                 'quality_provenance_sha256': hashlib.sha256(provenance.read_bytes()).hexdigest(), 'enabled': True}
        validate_registration(entry, {'snapshot_sha256': entry['snapshot_sha256']})
        registry[args.evaluation_id] = entry
        atomic_json(registry_path, registry)
        atomic_json(Path(queue['inbox']).parent / 'catalog.json', evaluation_catalog(registry), 0o644)
    print(json.dumps({'evaluation_id': args.evaluation_id, 'source_files_verified': len(source),
                      'scientific_acceptance': False, 'solver_registered': False}))


if __name__ == '__main__':
    main()
