#!/usr/bin/env python3
"""Validate an operator-retained ACS quality review; never grant acceptance.

This does not launch a model, post a review, or export controller transcripts.
The caller must supply the completed run's exact-secret audit separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys

W = Path('/mnt/data/zhanglinfeng/workspace')
STATE = W / '.state/harbor-eval/unified-harness-integration'
SOURCE = W / 'repos/unified-evaluator-pipeline'


def read_private(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Expected a regular private evidence file')
    info = path.stat()
    if info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600:
        raise ValueError('Private evidence must be operator-owned mode0600')
    return path.read_bytes()


def validate(run_id):
    if not re.fullmatch(r'qa-live-[a-f0-9]{10}', run_id):
        raise ValueError('Invalid ACS quality run identity')
    run = STATE / run_id
    if run.is_symlink() or not run.is_dir():
        raise ValueError('Missing private run directory')
    raw_report = read_private(STATE / ('acs-quality-live-' + run_id + '.json'))
    report = json.loads(raw_report)
    if report.get('run_id') != run_id or report.get('evidence_dir') != str(run):
        raise ValueError('Run report identity mismatch')
    result = report.get('result', {})
    if (report.get('controller_exit_code') != 0
            or result.get('exit_code') != 0
            or result.get('valid_review_exists') is not True
            or result.get('task_unchanged') is not True
            or result.get('secret_findings_before_redaction') != []):
        raise ValueError('Quality review did not complete with unchanged task inputs')
    if (result.get('provider') != 'dawnfm'
            or result.get('endpoint') != 'https://dawnfm.gravarc.cn/v1'
            or result.get('model') != 'deepseek-v4.1-flash-1017'):
        raise ValueError('Designated provider/model binding mismatch')
    cleanup = report.get('cleanup', {})
    snapshots = cleanup.get('two_snapshots', [])
    kinds = {'pods', 'sandboxsets', 'sandboxclaims', 'sandboxes'}
    if (cleanup.get('confirmed') is not True
            or cleanup.get('known_pod_404') is not True or len(snapshots) != 2
            or any(set(s) != kinds or any(s.values()) for s in snapshots)):
        raise ValueError('ACS cleanup is incomplete or unproven')
    audit = json.loads(read_private(run / 'exact-secret-audit.json'))
    if (audit.get('run_id') != run_id or audit.get('findings') != []
            or type(audit.get('secret_encodings_checked')) is not int
            or audit['secret_encodings_checked'] <= 0):
        raise ValueError('Missing or failed exact-secret audit')
    if audit.get('guard_report_sha256') != hashlib.sha256(raw_report).hexdigest():
        raise ValueError('Secret audit is stale for the run report')
    manifest_path = STATE / ('quality-live-input-manifest-' + run_id + '.json')
    manifest_raw = read_private(manifest_path)
    manifest = json.loads(manifest_raw)
    if manifest.get('run_id') != run_id:
        raise ValueError('Input manifest identity mismatch')
    # Verify the current implementation before importing its validator. Never
    # label a modified source checkout solely by the original commit ID.
    checked_paths = set()
    for item in manifest['files']:
        name = item['path']
        if not name.startswith('source/unified_evaluator/'):
            continue
        relative = Path(name).relative_to('source')
        path = SOURCE / relative
        if path.is_symlink() or not path.resolve().is_relative_to(SOURCE.resolve()):
            raise ValueError('Source path escapes trusted checkout')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Validator source differs from executed source')
        if relative.as_posix() in checked_paths:
            raise ValueError('Duplicate evaluator source entry')
        checked_paths.add(relative.as_posix())
    expected_paths = {
        path.relative_to(SOURCE).as_posix()
        for path in (SOURCE / 'unified_evaluator').rglob('*')
        if path.is_file() and '__pycache__' not in path.parts
        and path.suffix != '.pyc'
    }
    if not checked_paths or checked_paths != expected_paths:
        raise ValueError('Input manifest does not cover the full evaluator implementation')
    review_raw = read_private(run / 'output/review.json')
    if audit.get('review_sha256') != hashlib.sha256(review_raw).hexdigest():
        raise ValueError('Secret audit is stale for the final review')
    sys.path.insert(0, str(SOURCE))
    from unified_evaluator.pipelines.quality_review.review import load_rubric, validate_and_score
    review = json.loads(review_raw)
    validate_and_score(review, manifest['task'], load_rubric()[0])
    metadata = review.get('review_metadata', {})
    if (metadata.get('model') != result['model']
            or type(metadata.get('successful_shell_commands')) is not int
            or metadata['successful_shell_commands'] <= 0):
        raise ValueError('No successful reviewer tool execution proven')
    # A role sees only standard report fields, with known task paths relocated.
    fields = ['task_id', 'summary', 'dimensions', 'gate', 'difficulty', 'issues',
              'suggestions', 'limitations', 'quality_score', 'coverage', 'score_range']
    task_path = metadata.get('workspace')
    if not isinstance(task_path, str) or not task_path:
        raise ValueError('Missing reviewer task workspace binding')
    sanitized = json.loads(json.dumps({k: review[k] for k in fields})
                           .replace(task_path, '/task').replace(str(W), '[workspace]'))
    return {'run_id': run_id, 'status': 'quality_diagnostic_complete',
            'review': sanitized, 'cleanup_confirmed': True,
            'input_manifest_sha256': hashlib.sha256(manifest_raw).hexdigest(),
            'review_sha256': hashlib.sha256(review_raw).hexdigest(),
            'quality_acceptance': False, 'scientific_acceptance': False,
            'release_eligible': False, 'raw_trajectory_exported': False,
            'usage': metadata.get('usage'),
            'successful_shell_commands': metadata['successful_shell_commands']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.run_id), ensure_ascii=False))


if __name__ == '__main__':
    main()
