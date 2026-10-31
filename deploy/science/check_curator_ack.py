#!/usr/bin/env python3
"""Read authenticated Forgejo acknowledgments; never approve, merge or infer science quality."""
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from configure_review_protection import matches
from evaluation_queue import W, atomic_json, root_file
from prepare_review_packet import validate
from controller_credentials import load_controller_credentials

API = os.environ.get('GEWU_FORGEJO_URL', 'http://127.0.0.1:3000').rstrip('/') + '/api/v1'
REPO = '/repos/team/terminal-bench-science'
ACTORS = ('science-evaluator', 'owner')


def inspect(pull, reviews, protection, users, inventory_sha256, expected_head):
    if not re.fullmatch(r'[0-9a-f]{40}', expected_head):
        raise ValueError('Full target commit required')
    if not re.fullmatch(r'[0-9a-f]{64}', inventory_sha256):
        raise ValueError('Exact inventory hash required')
    reasons = []
    if pull.get('state') != 'open' or pull.get('merged') is not False:
        reasons.append('pull_not_open')
    if pull.get('head', {}).get('sha') != expected_head:
        reasons.append('target_commit_changed')
    if pull.get('base', {}).get('ref') != 'main':
        reasons.append('wrong_base_branch')
    if not matches(protection):
        reasons.append('review_protection_mismatch')
    ids = {name: users[name]['id'] for name in ACTORS}
    if len(set(ids.values())) != len(ACTORS) or any(type(i) is not int for i in ids.values()):
        raise ValueError('Distinct authenticated actor IDs required')
    if any(users[name].get('login') != name for name in ACTORS):
        raise ValueError('Unexpected authenticated actor')
    if pull.get('user', {}).get('id') in ids.values():
        reasons.append('reviewer_is_pull_author')
    marker = 'science-review-inventory-sha256:' + inventory_sha256
    acknowledgments = {}
    seen = set()
    for review in reviews:
        rid = review['id']
        if type(rid) is not int or rid in seen:
            raise ValueError('Duplicate or invalid review ID')
        seen.add(rid)
        if review.get('state') == 'REQUEST_CHANGES' and review.get('dismissed') is False:
            reasons.append('unresolved_change_request')
    for name, uid in ids.items():
        decisive = [r for r in reviews if r.get('user', {}).get('id') == uid
                    and r.get('state') in ('APPROVED', 'REQUEST_CHANGES')]
        latest = max(decisive, key=lambda r: r['id'], default={})
        valid = (latest.get('state') == 'APPROVED' and latest.get('official') is True
                 and latest.get('dismissed') is False and latest.get('commit_id') == expected_head
                 and marker in (latest.get('body') or '').splitlines())
        if not valid:
            reasons.append('missing_current_bound_ack:' + name)
        acknowledgments[name] = {'authenticated_user_id': uid,
                                'review_id': latest.get('id'), 'valid': valid}
    return {'schema_version': 1, 'kind': 'forgejo_inventory_ack_check',
            'target_commit': expected_head, 'inventory_sha256': inventory_sha256,
            'acknowledgments': acknowledgments,
            'acknowledgments_verified': not reasons, 'blocking_reasons': sorted(set(reasons)),
            'scientific_acceptance': False, 'first_pilot_user_approval_verified': False,
            'release_eligible': False, 'merged_any_task': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pull', required=True, type=int)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--inventory', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if os.geteuid() != 0 or args.pull <= 0 or args.output.exists() or not args.output.resolve().is_relative_to(W):
        raise ValueError('Operator, positive pull ID and fresh workspace output required')
    inventory = root_file(args.inventory)
    raw = inventory.read_bytes()
    packet = json.loads(raw)
    validate(packet)
    session = requests.Session()
    session.trust_env = False
    session.headers['Authorization'] = 'token ' + load_controller_credentials()['forgejo_admin_token']

    def get(path):
        response = session.get(API + path, timeout=30, allow_redirects=False)
        if response.status_code != 200:
            raise ValueError('Forgejo read failed: HTTP ' + str(response.status_code))
        return response.json()

    path = REPO + '/pulls/' + str(args.pull)
    pull = get(path)
    def read_reviews():
        reviews = []
        for page in range(1, 1001):
            batch = get(path + '/reviews?limit=50&page=' + str(page))
            if not isinstance(batch, list):
                raise ValueError('Invalid review page')
            if not batch:
                return reviews
            reviews.extend(batch)
        raise ValueError('Review pagination did not terminate')

    reviews = read_reviews()
    protection = get(REPO + '/branch_protections/main')
    users = {name: get('/users/' + name) for name in ACTORS}
    report = inspect(pull, reviews, protection, users, hashlib.sha256(raw).hexdigest(), args.expected_head)
    # Observational check only: a later mutation always requires another check.
    if (get(path) != pull or read_reviews() != reviews
            or get(REPO + '/branch_protections/main') != protection
            or any(get('/users/' + name) != users[name] for name in ACTORS)):
        raise ValueError('Server state changed during acknowledgment check')
    validate(packet)
    if inventory.read_bytes() != raw:
        raise ValueError('Inventory changed during acknowledgment check')
    report.update({'pull_number': args.pull, 'source_commit': packet['source_commit'],
                   'snapshot_sha256': packet['snapshot_sha256'],
                   'checked_at': datetime.now(timezone.utc).isoformat(),
                   'safe_for_publication': False})
    atomic_json(args.output, report)
    print(json.dumps({'acknowledgments_verified': report['acknowledgments_verified'],
                      'blocking_reasons': report['blocking_reasons'], 'release_eligible': False}))


if __name__ == '__main__':
    main()
