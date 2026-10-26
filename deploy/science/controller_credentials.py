"""Read the trusted controller's private credentials without exposing values."""
import os
import stat
import tomllib
from evaluation_queue import W


def load_controller_credentials():
    if os.geteuid() != 0:
        raise ValueError('Operator required')
    path = W / 'universes/my-terminal-bench-science/.config/gewu-multiverse/credentials.toml'
    info = path.lstat()
    parent = path.parent.lstat()
    # The controller runs as65534; its credentials intentionally are not root-owned.
    # Do not relax root_file(), which protects different evaluator-owned assets.
    if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)
            or info.st_uid not in (0, 65534) or stat.S_IMODE(info.st_mode) != 0o600
            or not stat.S_ISDIR(parent.st_mode) or stat.S_ISLNK(parent.st_mode)
            or parent.st_uid not in (0, 65534) or stat.S_IMODE(parent.st_mode) != 0o700
            or not path.resolve().is_relative_to(W)):
        raise ValueError('Controller credential ownership/type/mode refused')
    return tomllib.loads(path.read_text())
