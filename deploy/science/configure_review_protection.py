#!/usr/bin/env python3
"""Operator-only: require independent evaluator and owner approval for pilot merges.

Read the controller's local admin credential; never accept a token on argv or
print response bodies. This configures protection, not an approval or a merge.
"""
import argparse
import json
import os
from pathlib import Path
import tomllib
import requests

POLICY = {
    'enable_push': False,
    'enable_push_whitelist': False,
    'enable_merge_whitelist': True,
    'merge_whitelist_usernames': ['science-curator'],
    'required_approvals': 2,
    'enable_approvals_whitelist': True,
    'approvals_whitelist_username': ['science-evaluator', 'owner'],
    'block_on_rejected_reviews': True,
    'block_on_outdated_branch': True,
    'dismiss_stale_approvals': True,
    'ignore_stale_approvals': False,
    'apply_to_admins': True,
}


def matches(actual):
    for field, expected in POLICY.items():
        value = actual.get(field)
        if isinstance(expected, list):
            if not isinstance(value, list) or sorted(value) != sorted(expected):
                return False
        elif value != expected:
            return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--credentials', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    credentials = tomllib.loads(args.credentials.read_text())
    session = requests.Session()
    session.trust_env = False
    session.headers['Authorization'] = 'token ' + credentials['forgejo_admin_token']
    base = os.environ.get('GEWU_FORGEJO_URL', 'http://127.0.0.1:3000').rstrip('/')
    url = base + '/api/v1/repos/team/terminal-bench-science/branch_protections/main'
    if not args.check_only:
        response = session.patch(url, json=POLICY, timeout=15)
        if response.status_code != 200:
            raise SystemExit('Protection update failed: HTTP ' + str(response.status_code))
    response = session.get(url, timeout=15)
    if response.status_code != 200:
        raise SystemExit('Protection read-back failed: HTTP ' + str(response.status_code))
    actual = response.json()
    report = {'branch': 'main', 'policy': {key: actual.get(key) for key in POLICY},
              'verified': matches(actual), 'approved_or_merged_any_task': False}
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    if not report['verified']:
        raise SystemExit('Protection read-back did not match requested policy')


if __name__ == '__main__':
    main()
