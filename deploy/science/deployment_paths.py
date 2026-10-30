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

def deployment_state_root(root=None):
    """State owned by one deployment; never share mutable state across universes."""
    root=Path(root) if root is not None else universe_root()
    root=root.resolve()
    if not root.is_relative_to(WORKSPACE.resolve()) or root==WORKSPACE.resolve():
        raise ValueError('Deployment state root must be inside workspace')
    return root/'.state/gewu-multiverse'

def require_isolated_service_config(root=None, workspace=WORKSPACE):
    """Fail closed until each universe has its own broker and evaluator services."""
    root=Path(root) if root is not None else universe_root(workspace)
    state=deployment_state_root(root)
    required={
        'role broker': state/'role-broker/config.json',
        'evaluation queue': root/'.config/science-evaluation/queue.json',
        'review dispatcher': state/'review-dispatcher/config.json',
        'author selftest worker': state/'author-selftest/config.json',
        'command watchdog': state/'command-watchdog/config.json',
    }
    missing=[name for name,path in required.items() if not path.is_file() or path.is_symlink()]
    if missing:
        raise RuntimeError('Universe services are not isolated/configured: '+', '.join(missing))
    return state
