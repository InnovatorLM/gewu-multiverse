"""Explicit deployment identity; never silently select another universe."""
import os
from pathlib import Path
WORKSPACE=Path('/mnt/data/zhanglinfeng/workspace')

def universe_root(workspace=WORKSPACE):
    workspace=Path(workspace).resolve()
    configured=os.environ.get('GEWU_UNIVERSE_ROOT')
    path=Path(configured) if configured else workspace/'universes/my-terminal-bench-science'
    if not path.is_absolute() or not path.resolve().is_relative_to(workspace) or path.resolve()==workspace:
        raise ValueError('Universe root must be an absolute directory below workspace')
    return path.resolve()
