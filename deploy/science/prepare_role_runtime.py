"""Provision isolated role roots for the science universe."""
import json
import os
from pathlib import Path
import shutil
import subprocess

w = Path('/mnt/data/zhanglinfeng/workspace')
universe = w / 'universes/my-terminal-bench-science'
source = w / '.state/role-chroot-proof'
# Python package installation is role-local: vendor pip into the immutable
# runtime source, while each role receives its own user site and cache.
host_pip = Path('/usr/local/lib/python3.10/site-packages/pip')
host_pip_info = Path('/usr/local/lib/python3.10/site-packages/pip-23.0.1.dist-info')
if host_pip.is_dir():
    shutil.copytree(host_pip, source / 'usr/local/lib/python3.10/site-packages/pip', dirs_exist_ok=True)
if host_pip_info.is_dir():
    shutil.copytree(host_pip_info, source / 'usr/local/lib/python3.10/site-packages/pip-23.0.1.dist-info', dirs_exist_ok=True)
pip_launcher = source / 'usr/local/bin/pip'
pip_launcher.write_text('#!/bin/sh\nexec /usr/local/bin/python3 -m pip \"$@\"\n')
pip_launcher.chmod(0o755)
control = w / '.state/science-role-broker'
control.mkdir(exist_ok=True)
control.chmod(0o755)
config = dict(controller_uid=65534, socket='@' + str(control / 'broker.sock'), roles={})
config_root = universe / '.config/gewu-multiverse'
agents = config_root / 'agents'
agents.mkdir(exist_ok=True)
os.chown(agents, 65534, 65534)
agents.chmod(0o700)
roles = ([f'author-{i:02d}' for i in range(1, 11)] +
         [f'evaluator-{i:02d}' for i in range(1, 4)] + ['curator'])
for index, role in enumerate(roles):
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
    kind = ('evaluator' if role.startswith('evaluator') else
            'author' if role.startswith('author-') else role)
    instruction_name = 'evaluator-instruction.md' if kind == 'evaluator' else 'author-instruction.md'
    instruction = universe / 'governance' / ('private' if kind == 'evaluator' else 'public') / instruction_name
    target = root / 'instruction.md'
    shutil.copyfile(instruction, target)
    os.chown(target, 65534, 65534)
    target.chmod(0o644)
    if kind == 'author':
        feedback = universe / 'governance/public/pilot-review-feedback.md'
        if feedback.is_file():
            target = root / 'workspace/PILOT-REVIEW-FEEDBACK.md'
            shutil.copyfile(feedback, target)
            os.chown(target, 0, 0)
            target.chmod(0o644)
    target = root / 'home/role/git-credential.json'
    credential_name = role + '.json'
    if not (w / '.config/universe-roles' / credential_name).is_file():
        credential_name = kind + '.json'
    creds = json.loads((w / '.config/universe-roles' / credential_name).read_text())
    target.write_text(json.dumps({'login': creds['login'], 'token': creds['token']}))
    os.chown(target, uid, uid)
    target.chmod(0o600)
    askpass = root / 'usr/local/bin/role-askpass'
    # Never overwrite a shared tool inode (each role gets a separate askpass file).
    if askpass.exists():
        askpass.unlink()
    askpass.write_text('#!/usr/local/bin/python3\nimport json,sys\nc=json.load(open("/home/role/git-credential.json"))\nprint(c["login"] if "Username" in sys.argv[1] else c["token"])\n')
    askpass.chmod(0o755)
    for filename, executable in [('role_codex_runner.py', 'role-codex-runner'), ('role_forgejo.py', 'role-forgejo')]:
        target = root / 'usr/local/bin' / executable
        target.unlink(missing_ok=True)
        shutil.copyfile(Path(__file__).with_name(filename), target)
        target.chmod(0o755)
    proc_self = root / 'proc/self'
    proc_self.mkdir(parents=True, exist_ok=True)
    proc_self.chmod(0o755)
    executable = proc_self / 'exe'
    executable.unlink(missing_ok=True)
    executable.symlink_to('/usr/local/bin/codex')
    if (root / 'proc/1').exists() or (proc_self / 'root').exists():
        raise ValueError('Host proc exposure refused')
    remote = root / 'usr/lib/git-core/git-remote-https'
    if not remote.exists():
        remote.symlink_to('git-remote-http')
    config['roles'][role] = dict(root=str(root), uid=uid, gid=uid)
path = control / 'config.json'
path.write_text(json.dumps(config, indent=2))
path.chmod(0o644)
print(json.dumps({'config': str(path), 'roles': list(config['roles']), 'provider_key_staged': False}))
