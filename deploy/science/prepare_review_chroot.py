import json, os, shutil, subprocess, stat
from pathlib import Path

w = Path('/mnt/data/zhanglinfeng/workspace')
root = w / '.state/role-chroot-proof'
root.mkdir(parents=True, exist_ok=True)
codex = root / 'usr/local/bin/codex'
codex.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2('/opt/codex-pkg/bin/codex', codex)
# Static executable lookup only; never expose the host proc filesystem.
proc_self = root / 'proc/self'
proc_self.mkdir(parents=True, exist_ok=True)
if not (proc_self / 'exe').exists():
    (proc_self / 'exe').symlink_to('/usr/local/bin/codex')
for binary in ['/bin/bash', '/bin/ls', '/bin/cat', '/usr/bin/find', '/usr/bin/head', '/usr/bin/wc', '/usr/bin/sed', '/usr/bin/grep', '/usr/bin/env', '/usr/bin/id', '/usr/bin/timeout', '/usr/bin/diff', '/usr/bin/awk', '/usr/local/bin/python3.10']:
    source = Path(binary)
    if not source.exists():
        continue
    target = root / binary.lstrip('/')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    result = subprocess.run(['ldd', binary], capture_output=True, text=True)
    for token in result.stdout.split():
        if token.startswith('/') and Path(token).is_file():
            dest = root / token.lstrip('/')
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(token, dest)
# Standard library only: no host site-packages, credentials or startup hooks.
stdlib = Path('/usr/local/lib/python3.10')
shutil.copytree(stdlib, root / 'usr/local/lib/python3.10', dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('site-packages', '__pycache__', 'test', 'tests'))
python = root / 'usr/local/bin/python3'
if not python.exists():
    python.symlink_to('python3.10')
for name in ['/etc/resolv.conf', '/etc/hosts', '/etc/nsswitch.conf', '/etc/ssl/certs/ca-certificates.crt']:
    target = root / name.lstrip('/')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(name, target)
(root / 'etc/passwd').write_text('review:x:21002:21002:review:/home/review:/bin/bash\n')
(root / 'etc/group').write_text('review:x:21002:\n')
for name in ['home/review', 'runtime', 'tmp']:
    target = root / name
    target.mkdir(parents=True, exist_ok=True)
    os.chown(target, 21002, 21002)
    target.chmod(0o700)
(root / 'dev').mkdir(exist_ok=True)
devices = {}
for name, minor in [('null', 3), ('zero', 5), ('random', 8), ('urandom', 9)]:
    target = root / 'dev' / name
    try:
        if not target.exists():
            os.mknod(target, stat.S_IFCHR | 0o666, os.makedev(1, minor))
        devices[name] = 'ready'
    except OSError as exc:
        devices[name] = type(exc).__name__
# This environment forbids device creation. Non-PTY exec requires a writable
# sink at /dev/null; this is a regular bounded-by-run-lifetime file, not a device.
null = root / 'dev/null'
if not null.exists():
    null.touch(mode=0o666)
    null.chmod(0o666)
    devices['null'] = 'regular-file-fallback-no-pty'
task = w / 'universes/my-terminal-bench-science/workspaces/author/candidates/robust-sensor-calibration'
dest = root / 'task'
if dest.exists():
    shutil.rmtree(dest)
shutil.copytree(task, dest, symlinks=False)
for item in [dest, *dest.rglob('*')]:
    os.chown(item, 0, 0)
    item.chmod(0o555 if item.is_dir() else 0o444)
config = (w / '.config/ue-dawnfm-flash/config.toml').read_text()
config = 'sandbox_mode = "danger-full-access"\napproval_policy = "never"\nproject_doc_max_bytes = 0\nmodel_reasoning_effort = "low"\n' + config
config += '\n[shell_environment_policy]\ninherit = "none"\nset = { PATH = "/usr/local/bin:/usr/bin:/bin", HOME = "/home/review", TMPDIR = "/tmp" }\n'
target = root / 'home/review/config.toml'
target.write_text(config)
os.chown(target, 21002, 21002)
target.chmod(0o600)
print(json.dumps({'root': str(root), 'devices': devices, 'task_files': len(list(dest.rglob('*'))), 'credentials_copied': False}))
