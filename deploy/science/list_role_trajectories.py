#!/usr/bin/env python3
"""Operator-only index; never prints event contents or credentials."""
import json
from pathlib import Path

W = Path('/mnt/data/zhanglinfeng/workspace')

def main():
    config = json.loads((W / '.state/science-role-broker/config.json').read_text())
    for role, settings in config['roles'].items():
        root = Path(settings['root']) / 'home/role/trajectories'
        for archive in sorted(root.glob('*')):
            if not archive.is_dir():
                continue
            try:
                metadata = json.loads((archive / 'metadata.json').read_text())
            except (OSError, ValueError):
                metadata = {'status': 'interrupted-or-metadata-unavailable'}
            events = archive / 'events.jsonl'
            print(json.dumps({'role': role, 'directory': str(archive),
                              'status': metadata.get('status'),
                              'events_bytes': events.stat().st_size if events.exists() else 0}))

if __name__ == '__main__':
    main()
