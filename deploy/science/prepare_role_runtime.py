"""Provision the three role roots; credentials remain local and scoped."""
import json
import os
from pathlib import Path
import shutil
import subprocess

w = Path('/mnt/data/zhanglinfeng/workspace')
universe = w / 'universes/my-terminal-bench-science'
source = w / '.state/role-chroot-proof'
control = w / '.state/science-role-broker'
control.mkdir(exist_ok=True)
control.chmod(0o755)
config = dict(controller_uid=65534, socket='@' + str(control / 'broker.sock'), roles={})
config_root = universe / '.config/gewu-multiverse'
agents = config_root / 'agents'
agents.mkdir(exist_ok=True)
os.chown(agents, 65534, 65534)
agents.chmod(0o700)
for index, role in enumerate(['author', 'evaluator', 'curator']):
    uid = 21001 + index
    root = agents / role
    root.mkdir(exist_ok=True)
    os.chown(root, 65534, 65534)
    root.chmod(0o755)
    # Immutable system tools can share root-owned inodes, not role-owned state.
    for name in ['bin', 'usr', 'lib', 'lib64', 'etc']:
        if (source / name).exists():
            shutil.copytree(source / name, root / name, dirs_exist_ok=True,
                            copy_function=lambda a, b: os.link(a, b) if not Path(b).exists() else b)
    for name in ['workspace', 'skills', 'home/role', 'tmp', 'dev']:
        target = root / name
        target.mkdir(parents=True, exist_ok=True)
        if name == 'workspace':
            os.chown(target, 65534, uid)
            target.chmod(0o2770)
        elif name in ['home/role', 'tmp']:
            os.chown(target, uid, uid)
            target.chmod(0o700)
        else:
            target.chmod(0o755)
    null = root / 'dev/null'
    if not null.exists():
        null.touch()
    null.chmod(0o666)
    instruction = universe / 'governance' / ('private' if role == 'evaluator' else 'public') / (role + '-instruction.md')
    target = root / 'instruction.md'
    shutil.copyfile(instruction, target)
    os.chown(target, 65534, 65534)
    target.chmod(0o644)
    if role == 'author':
        feedback = universe / 'governance/public/pilot-review-feedback.md'
        if feedback.is_file():
            target = root / 'workspace/PILOT-REVIEW-FEEDBACK.md'
            shutil.copyfile(feedback, target)
            os.chown(target, 0, 0)
            target.chmod(0o644)
    target = root / 'home/role/git-credential.json'
    creds = json.loads((w / '.config/universe-roles' / (role + '.json')).read_text())
    target.write_text(json.dumps({'login': creds['login'], 'token': creds['token']}))
    os.chown(target, uid, uid)
    target.chmod(0o600)
    askpass = root / 'usr/local/bin/role-askpass'
    # Never overwrite a shared tool inode (each role gets a separate askpass file).
    if askpass.exists():
        askpass.unlink()
    askpass.write_text('#!/usr/local/bin/python3\nimport json,sys\nc=json.load(open("/home/role/git-credential.json"))\nprint(c["login"] if "Username" in sys.argv[1] else c["token"])\n')
    askpass.chmod(0o755)
    remote = root / 'usr/lib/git-core/git-remote-https'
    if not remote.exists():
        remote.symlink_to('git-remote-http')
    config['roles'][role] = dict(root=str(root), uid=uid, gid=uid)
path = control / 'config.json'
path.write_text(json.dumps(config, indent=2))
path.chmod(0o644)
print(json.dumps({'config': str(path), 'roles': list(config['roles']), 'provider_key_staged': False}))
