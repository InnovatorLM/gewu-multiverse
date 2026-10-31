#!/usr/bin/env python3
"""Assign the local author startup task; no scientific approval or external message."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import requests
from evaluation_queue import W, atomic_json, root_file
from controller_credentials import load_controller_credentials

BASE = os.environ.get('GEWU_FORGEJO_URL', 'http://127.0.0.1:3000').rstrip('/') + '/api/v1'
REPO = '/repos/team/terminal-bench-science'
MARKER = '<!-- science-universe-author-proposal-bootstrap:v1 -->'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or args.output.exists() or not args.output.resolve().is_relative_to(W):
        raise ValueError('Operator and fresh workspace output required')
    body = (Path(__file__).resolve().parents[2] / 'docs/science-universe/proposal-startup-task.md').read_text()
    credentials = load_controller_credentials()
    session = requests.Session()
    session.trust_env = False
    session.headers['Authorization'] = 'token ' + credentials['forgejo_admin_token']

    def call(method, path, expected=200, data=None):
        response = session.request(method, BASE + path, json=data, timeout=30, allow_redirects=False)
        if response.status_code != expected:
            raise ValueError('Local task operation failed: HTTP ' + str(response.status_code))
        return response.json()

    owner = call('GET', '/user')
    if owner['login'] != 'owner':
        raise ValueError('Unexpected operator identity')
    found = []
    for page in range(1, 1001):
        batch = call('GET', REPO + '/issues?state=open&type=issues&limit=50&page=' + str(page))
        if not isinstance(batch, list):
            raise ValueError('Invalid issue page')
        if not batch:
            break
        found.extend(i for i in batch if MARKER in (i.get('body') or ''))
    else:
        raise ValueError('Issue pagination did not terminate')
    if len(found) > 1:
        raise ValueError('Duplicate startup tasks require operator inspection')
    created = False
    if found:
        issue = found[0]
    elif args.apply:
        issue = call('POST', REPO + '/issues', expected=201, data={
            'title': '[启动任务] 提交一份可独立审查的新科学提案',
            'body': body, 'assignees': ['science-author']})
        created = True
    else:
        raise ValueError('No assigned startup task; use --apply to create the documented local task')
    path = REPO + '/issues/' + str(issue['number'])
    issue = call('GET', path)
    if (issue.get('body') != body or issue.get('user', {}).get('id') != owner['id']
            or 'science-author' not in [a['login'] for a in issue.get('assignees') or []]):
        raise ValueError('Startup task author, content or assignment mismatch')
    role = json.loads(root_file(W / '.config/universe-roles/author.json').read_text())
    session.headers['Authorization'] = 'token ' + role['token']
    if call('GET', path)['number'] != issue['number']:
        raise ValueError('Assigned author cannot read task')
    result = {'issue_number': issue['number'], 'created': created,
              'assignee': 'science-author', 'author_visibility_verified': True,
              'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
              'scientific_acceptance': False}
    atomic_json(args.output, result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
