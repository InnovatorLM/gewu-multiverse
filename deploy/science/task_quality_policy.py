"""Inject current shared policy into both controller and isolated role instructions."""
from pathlib import Path
import re

BEGIN='<!-- BEGIN TASK QUALITY POLICY -->'
END='<!-- END TASK QUALITY POLICY -->'


def update(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Missing or linked role instruction')
    text=path.read_text()
    if BEGIN in text:
        start=text.index(BEGIN);end=text.index(END,start)+len(END)
        text=text[:start]+text[end:]
    policy=Path(__file__).with_name('task-quality-policy.md').read_text()
    path.write_text(BEGIN+'\n'+policy+END+'\n\n'+text.lstrip())


def install(config, universe):
    for role,entry in config['roles'].items():
        if not re.fullmatch(r'(author|evaluator)-[0-9]+',role):continue
        for path in [Path(universe)/'.config/gewu-multiverse/agents'/role/'instruction.md',Path(entry['root'])/'instruction.md']:
            update(path)
