#!/usr/bin/env python3
"""Summarize retained review evidence without granting scientific acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

from evaluation_queue import W, atomic_json, root_file


def diagnostic_status(directory):
    directory = Path(directory).resolve(strict=True)
    if not directory.is_relative_to(W):
        raise ValueError('Evidence must be workspace-local')
    review_path = directory / 'review.json'
    audit_path = directory / 'factual-audit.json'
    status = {'report_validated':False,'factual_audit_present':False,'scientific_acceptance':False,'quality_acceptance':False,'release_eligible':False,'role_queue_dispatch_verified':False}
    if review_path.exists():
        path = root_file(review_path)
        data = json.loads(path.read_text())
        # Only read reports which explicitly deny acceptance. Missing/ambiguous
        # fields cannot be promoted to a favorable state.
        if data.get('scientific_acceptance') is not False or data.get('factual_acceptance') is not False:
            raise ValueError('Diagnostic report acceptance fields inconsistent')
        review = data['review']
        status.update(report_validated=True, report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), snapshot_sha256=data['snapshot_sha256'], diagnostic_score=review['quality_score'], diagnostic_gate=review['gate']['status'])
    if audit_path.exists():
        path = root_file(audit_path)
        audit = json.loads(path.read_text())
        if audit.get('factual_acceptance') is not False or audit.get('scientific_acceptance') is not False:
            raise ValueError('Diagnostic factual audit must not authorize acceptance')
        status.update(factual_audit_present=True, factual_audit_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    status['state'] = 'diagnostic_audited' if status['report_validated'] and status['factual_audit_present'] else 'diagnostic_unverified'
    return status


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not args.output.resolve().is_relative_to(W) or args.output.exists():
        raise ValueError('Require a fresh workspace result path')
    atomic_json(args.output,diagnostic_status(args.directory))


if __name__=='__main__':main()
