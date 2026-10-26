#!/usr/bin/env python3
"""Revalidate private trajectory provenance before any downstream judge reads it."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
from evaluation_queue import W, root_file, validated_template

ROOT = W / '.state/science-private-trajectories'


def read_private(path):
    path = root_file(path)
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError('Private evidence must be mode0600')
    return path.read_bytes()


def validate(directory, entry):
    directory = Path(directory)
    if ROOT.is_symlink() or directory.is_symlink() or directory.parent.resolve() != ROOT.resolve():
        raise ValueError('Private trajectory location refused')
    for path in [ROOT, directory]:
        info = path.stat()
        if info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError('Private trajectory directory ownership/mode refused')
    config = validated_template(entry, {'snapshot_sha256': entry['snapshot_sha256']})
    identity_raw = read_private(directory/'identity.json')
    identity = json.loads(identity_raw)
    retention = json.loads(read_private(directory/'retention.json'))
    binding = json.loads(read_private(directory/'execution-binding.json'))
    if identity.get('snapshot_path') != entry['snapshot'] or identity.get('snapshot_sha256') != entry['snapshot_sha256']:
        raise ValueError('Private trajectory source differs from registration')
    if identity.get('provider') != 'dawnfm' or identity.get('model') != 'deepseek-v4.1-flash-1017':
        raise ValueError('Private trajectory provider/model refused')
    for key in ['runtime_image','verifier_image']:
        if identity.get(key) != config['environment']['kwargs'][key]:
            raise ValueError('Private trajectory image differs from registration')
    if retention.get('snapshot_sha256') != entry['snapshot_sha256'] or binding.get('snapshot_sha256') != entry['snapshot_sha256']:
        raise ValueError('Private trajectory evidence snapshot mismatch')
    if retention.get('review_ready') is not True or binding.get('review_input_eligible') is not True or binding.get('solver_status') != 'solver_complete' or any(binding.get(key) is not True for key in ['snapshot_unchanged_after_run','cleanup_confirmed','trajectory_retained']):
        raise ValueError('Private trajectory run is not eligible for review')
    if retention.get('scientific_acceptance') is not False or binding.get('scientific_acceptance') is not False:
        raise ValueError('Retention cannot grant scientific acceptance')
    files = {'identity_sha256': identity_raw,
             'raw_sha256': read_private(directory/'mini-swe-agent.trajectory.json'),
             'atif_sha256': read_private(directory/'trajectory.json')}
    if any(hashlib.sha256(raw).hexdigest() != retention.get(key) for key,raw in files.items()):
        raise ValueError('Private retained evidence changed')
    atif = json.loads(files['atif_sha256'])
    if atif.get('schema_version') != retention.get('schema_version') or not str(atif.get('schema_version','')).startswith('ATIF') or not atif.get('steps'):
        raise ValueError('Invalid retained ATIF evidence')
    return {'snapshot_sha256': entry['snapshot_sha256'], 'atif_sha256': retention['atif_sha256'],
            'identity_and_file_hashes_verified': True, 'review_input_eligible': True,
            'source_of_provenance': 'operator worker and controlled adapter; not a cryptographic attestation of solver honesty',
            'scientific_acceptance': False, 'release_eligible': False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-id',required=True)
    parser.add_argument('--directory',type=Path,required=True)
    args=parser.parse_args()
    registry=json.loads(root_file(W/'.config/science-evaluation/registry.json').read_text())
    print(json.dumps(validate(args.directory,registry[args.evaluation_id])))


if __name__=='__main__':main()
