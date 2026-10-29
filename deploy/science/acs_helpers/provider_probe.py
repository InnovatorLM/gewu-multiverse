#!/usr/bin/env python3
"""Bounded live protocol probe. Never prints credentials or raw API errors."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import requests


def settings():
    values = {k: os.environ.get(k, '').strip() for k in
              ('LLM_PROVIDER', 'OPENAI_BASE_URL', 'OPENAI_MODEL', 'OPENAI_API_KEY')}
    missing = [k for k, v in values.items() if not v]
    if missing:
        raise ValueError('Missing explicit settings: ' + ', '.join(missing))
    url = urlsplit(values['OPENAI_BASE_URL'])
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError('API base must be a credential-free HTTPS URL')
    return values


def probe(values, protocol):
    model = values['OPENAI_MODEL']
    if protocol == 'chat':
        path = '/chat/completions'
        body = {'model': model, 'messages': [{'role': 'user', 'content': 'Reply with OK.'}],
                'max_tokens': 256, 'stream': False}
    else:
        path = '/responses'
        body = {'model': model, 'input': 'Reply with OK.', 'max_output_tokens': 256,
                'stream': False, 'store': False}
    result = {'protocol': protocol, 'compatible': False}
    try:
        response = requests.post(values['OPENAI_BASE_URL'].rstrip('/') + path,
                                 headers={'Authorization': 'Bearer ' + values['OPENAI_API_KEY']},
                                 json=body, timeout=(10, 90), allow_redirects=False)
        result['http_status'] = response.status_code
        if not response.ok:
            return result
        data = response.json()
        if not isinstance(data, dict):
            return result
        choices = data.get('choices')
        valid = (isinstance(choices, list) and bool(choices) and isinstance(choices[0], dict) and isinstance(choices[0].get('message'), dict)) if protocol == 'chat' else isinstance(data.get('output'), list)
        result['compatible'] = bool(valid and not data.get('error'))
        if result['compatible']:
            result['reported_model'] = data.get('model')
            # No response text, headers, raw usage object, or error body is logged.
    except (requests.RequestException, ValueError) as exc:
        result['error_type'] = type(exc).__name__
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', choices=['auto', 'chat', 'responses'], default='auto')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    values = settings()
    attempts = []
    for protocol in (['chat', 'responses'] if args.protocol == 'auto' else [args.protocol]):
        attempts.append(probe(values, protocol))
        if attempts[-1]['compatible']:
            break
    selected = next((r['protocol'] for r in attempts if r['compatible']), None)
    report = {'live_api_test': True, 'provider': values['LLM_PROVIDER'],
              'base_url': values['OPENAI_BASE_URL'].rstrip('/'), 'model': values['OPENAI_MODEL'],
              'selected_protocol': selected, 'attempts': attempts,
              'limitation': 'Transport/schema probe only; not a task score or a tool-use evaluation.'}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if selected else 1


if __name__ == '__main__':
    raise SystemExit(main())
