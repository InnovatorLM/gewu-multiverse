"""Reconstruct redacted model requests from full checkpoints and append deltas.

Reads an operator-owned transcript sequentially. Does not contact a model, expose
credentials, or change the original evidence. Output must remain workspace-local.
"""
import argparse
import json
import os
from pathlib import Path

WORKSPACE = Path('/mnt/data/zhanglinfeng/workspace')


def replay(previous, record):
    if not isinstance(record, dict):
        raise ValueError('Request must be a JSON object')
    if record.get('format') != 'gewu.request-delta.v1':
        return record
    if record.get('base') != 'previous_model_request' or not isinstance(previous, dict):
        raise ValueError('Delta has no preceding full request')
    before = previous.get('messages')
    append = record.get('append')
    options = record.get('options')
    if (not isinstance(before, list) or not before or not isinstance(append, list)
            or not isinstance(options, dict) or 'messages' in options
            or not isinstance(record.get('system'), dict)):
        raise ValueError('Invalid request delta')
    if record.get('base_message_count', len(before)) != len(before):
        raise ValueError('Missing or reordered request checkpoint')
    if options != {k: v for k, v in previous.items() if k != 'messages'}:
        raise ValueError('Request options changed without full checkpoint')
    return dict(options, messages=[record['system'], *before[1:], *append])


def requests(events):
    previous = None
    for event in events:
        if event.get('event') != 'model_request':
            continue
        previous = replay(previous, json.loads(event['body']))
        yield dict(turn=event.get('turn'), request=previous)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('transcript', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(WORKSPACE.resolve()):
        raise ValueError('Output must be below the active workspace')
    count = 0
    # Exclusive creation avoids overwriting an existing evidence file or symlink.
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'w') as target, args.transcript.open() as source:
            for row in requests(json.loads(line) for line in source if line.strip()):
                target.write(json.dumps(row, ensure_ascii=False) + '\n')
                count += 1
            target.flush()
            os.fsync(target.fileno())
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    print(json.dumps(dict(requests=count, output=str(output))))


if __name__ == '__main__':
    main()
