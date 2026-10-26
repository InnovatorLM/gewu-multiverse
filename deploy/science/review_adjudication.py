#!/usr/bin/env python3
"""Validate operator factual adjudication provenance, never infer factual truth."""
import argparse
import hashlib
import json
from pathlib import Path
from evaluation_queue import W, atomic_json, root_file


def claim_ids(report):
    review = report['review']
    result = {'summary', 'gate', 'difficulty'}
    issues = [issue['id'] for issue in review.get('issues', [])]
    if len(set(issues)) != len(issues):
        raise ValueError('Duplicate review issue IDs')
    result.update('issue:' + identifier for identifier in issues)
    result.update('dimension:' + name for name in review.get('dimensions', {}))
    for field in ['suggestions', 'limitations']:
        result.update(field + ':' + str(index) for index, _ in enumerate(review.get(field, [])))
    return result


def validate_adjudication(report_path, audit):
    report_path = root_file(report_path)
    report = json.loads(report_path.read_text())
    if audit.get('schema_version') != 1 or audit.get('report_sha256') != hashlib.sha256(report_path.read_bytes()).hexdigest() or audit.get('snapshot_sha256') != report['snapshot_sha256']:
        raise ValueError('Adjudication must bind this exact report and task snapshot')
    if audit.get('scientific_acceptance') is not False or audit.get('factual_acceptance') is not False:
        raise ValueError('Adjudication records cannot authorize acceptance')
    if not isinstance(audit.get('operator'), str) or not audit['operator'].strip():
        raise ValueError('Require an attributed operator judgment')
    decisions = audit['decisions']
    if not isinstance(decisions, list) or any(not isinstance(item, dict) for item in decisions):
        raise ValueError('Require a decision list')
    ids = [item['claim_id'] for item in decisions]
    if len(ids) != len(set(ids)) or set(ids) != claim_ids(report):
        raise ValueError('Every report claim needs exactly one decision, including unresolved claims')
    counts = {'supported': 0, 'refuted': 0, 'unresolved': 0}
    for item in decisions:
        verdict = item.get('verdict')
        if verdict not in counts or not isinstance(item.get('rationale'), str) or not item['rationale'].strip():
            raise ValueError('Require verdict and operator rationale')
        refs = item.get('evidence')
        if not isinstance(refs, list) or (verdict != 'unresolved' and not refs):
            raise ValueError('Supported/refuted judgments require actual evidence')
        for ref in refs:
            relative = Path(ref['path'])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Evidence paths must be workspace-relative')
            path = root_file(W / relative)
            raw = path.read_bytes()
            if ref.get('sha256') != hashlib.sha256(raw).hexdigest():
                raise ValueError('Adjudication evidence changed')
            quote = ref.get('quote')
            if not isinstance(quote, str) or not quote.strip() or quote not in raw.decode('utf-8'):
                raise ValueError('Evidence quotation is not present')
        counts[verdict] += 1
    return {'report_sha256': audit['report_sha256'], 'snapshot_sha256': report['snapshot_sha256'],
            'claim_counts': counts, 'claim_coverage_complete': True,
            'all_claims_adjudicated': counts['unresolved'] == 0,
            'all_claims_supported': counts['refuted'] == counts['unresolved'] == 0,
            'evidence_linkage_verified': True, 'machine_factual_verification': False,
            'operator_attestation_independently_authenticated': False,
            'scientific_acceptance': False, 'factual_acceptance': False, 'release_eligible': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or not args.output.resolve().is_relative_to(W):
        raise ValueError('Require a fresh workspace output')
    result = validate_adjudication(args.report, json.loads(root_file(args.audit).read_text()))
    atomic_json(args.output, result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
