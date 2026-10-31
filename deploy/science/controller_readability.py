"""Check recovery inputs as the actual controller, without printing contents."""
import argparse
import os
import re
from pathlib import Path

RECORDS = ('plan.json', 'transcript.jsonl', 'session.pid', 'session.pgid',
           'shell.pid', 'shell.pgid', 'shell.identity', 'shell.capability')


def check(state):
    state = Path(state)
    if not state.exists():
        return
    for role in state.iterdir():
        if not (re.fullmatch(r'(author|evaluator)-[0-9]+', role.name) or role.name == 'curator'):
            continue
        for run in role.iterdir():
            if not run.name.startswith('run-') or not run.is_dir():
                continue
            # Recovery must be able to search and list even an empty run.
            list(run.iterdir())
            for name in RECORDS:
                path = run / name
                try:
                    with path.open('rb') as stream:
                        stream.read(1)
                except FileNotFoundError:
                    continue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state', type=Path)
    args = parser.parse_args()
    try:
        check(args.state)
    except OSError as error:
        raise SystemExit('Controller recovery input is inaccessible: ' +
                         str(error.filename) + ' (' + type(error).__name__ + ')')


if __name__ == '__main__':
    main()
