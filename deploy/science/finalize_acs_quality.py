#!/usr/bin/env python3
"""Scan retained ACS quality evidence before exposing a validated diagnostic.

Operator-only: credential values stay in memory and never appear in this output.
This does not approve tasks or start a model, container, or role session.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import tarfile

from evaluation_queue import W, atomic_json, root_file
from read_unified_quality_receipt import STATE, read_private, validate


def credential_patterns():
    if os.geteuid() != 0 or not os.environ.get('OPENAI_API_KEY'):
        raise ValueError('Trusted operator credential environment required')
    values = {'provider': os.environ['OPENAI_API_KEY'].encode()}
    # These are the actual credential stores used by this workspace's ACS route.
    acr = root_file(W / '.config/acr/dptech-sh-pai-acr.env')
    for line in acr.read_text().splitlines():
        line = line.strip().removeprefix('export ')
        if '=' not in line or line.startswith('#'):
            continue
        name, value = line.split('=', 1)
        if any(word in name.upper() for word in ('PASSWORD', 'TOKEN', 'SECRET')):
            parts = shlex.split(value)
            if len(parts) == 1:
                values['acr_' + name] = parts[0].encode()
    import yaml
    kube = yaml.safe_load(read_private(W / '.config/acs/kubeconfig'))
    for index, user in enumerate(kube.get('users', [])):
        for name, value in user.get('user', {}).items():
            if name in ('token', 'client-key-data') and isinstance(value, str):
                values[f'kube_{index}_{name}'] = value.encode()
    docker = json.loads(read_private(W / '.config/docker-shanghai/config.json'))
    for index, value in enumerate(docker.get('auths', {}).values()):
        if value.get('auth'):
            values[f'docker_{index}'] = value['auth'].encode()
            decoded = base64.b64decode(value['auth'])
            if b':' in decoded:
                values[f'docker_password_{index}'] = decoded.split(b':', 1)[1]
    patterns = {}
    for name, value in values.items():
        if len(value) >= 8:
            patterns[name] = value
            patterns[name + '_base64'] = base64.b64encode(value)
    return patterns


def scan_evidence(root, archive, report_raw, patterns):
    """Scan extracted outputs, guard report and original upload members."""
    findings, records = [], []

    def check(name, raw):
        matches = [label for label, needle in patterns.items() if needle in raw]
        if matches:
            findings.append({'path': name, 'labels': matches})

    check('guard-report', report_raw)
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError('Unexpected evidence link or special file')
        if not path.is_file() or path.name in ('exact-secret-audit.json', 'diagnostic-receipt.json'):
            continue
        raw = read_private(path)
        name = path.relative_to(root).as_posix()
        check(name, raw)
        records.append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest()})
    count = 0
    with tarfile.open(root_file(archive)) as bundle:
        for member in bundle:
            if member.isfile():
                count += 1
                check('input:' + member.name, bundle.extractfile(member).read())
    if not records or not count:
        raise ValueError('Missing output or original input evidence')
    return findings, records, count


def finalize(run_id):
    if not re.fullmatch(r'qa-live-[a-f0-9]{10}', run_id):
        raise ValueError('Invalid ACS quality run identity')
    root = STATE / run_id
    report_raw = read_private(STATE / ('acs-quality-live-' + run_id + '.json'))
    report = json.loads(report_raw)
    if report.get('run_id') != run_id or report.get('cleanup', {}).get('confirmed') is not True:
        raise ValueError('Cannot finalize without confirmed resource release')
    patterns = credential_patterns()
    findings, records, count = scan_evidence(root, W / '.tmp' / run_id / 'runtime.tar.gz', report_raw, patterns)
    review = root / 'output/review.json'
    audit = {'run_id': run_id, 'findings': findings, 'secret_encodings_checked': len(patterns),
             'output_files': records, 'input_archive_members_checked': count,
             'review_sha256': hashlib.sha256(read_private(review)).hexdigest() if review.exists() else None,
             'guard_report_sha256': hashlib.sha256(report_raw).hexdigest()}
    atomic_json(root / 'exact-secret-audit.json', audit)
    if findings:
        raise ValueError('Known credential found in retained evidence; diagnostic withheld')
    diagnostic = validate(run_id)  # Includes the original pipeline's report validator.
    atomic_json(root / 'diagnostic-receipt.json', diagnostic)
    return diagnostic


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    receipt = finalize(args.run_id)
    print(json.dumps({'run_id': args.run_id, 'diagnostic_validated': True,
                      'cleanup_confirmed': True, 'scientific_acceptance': False}))
