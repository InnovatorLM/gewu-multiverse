"""Real broker/chroot regression, no model or cloud API calls."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

w = Path('/mnt/data/zhanglinfeng/workspace')
base = w / '.state/science-broker-test'
base.mkdir(exist_ok=True)
base.chmod(0o755)
source = w / '.state/role-chroot-proof'
script = Path(__file__).with_name('role_exec.py')
config = {'controller_uid': 65534, 'socket': '@' + str(base / 'broker.sock'), 'roles': {}}
for index, role in enumerate(['author-01', 'evaluator-01', 'curator']):
    uid = 21101 + index
    root = base / role
    root.mkdir(exist_ok=True)
    root.chmod(0o755)
    # Tools are root-owned immutable copies, hard-linked for bounded staging I/O.
    for name in ['bin', 'usr', 'lib', 'lib64', 'etc']:
        if (source / name).exists() and not (root / name).exists():
            shutil.copytree(source / name, root / name, copy_function=os.link)
    for name in ['workspace', 'home/role', 'tmp']:
        path = root / name
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o700)
        os.chown(path, uid, uid)
    (root / 'workspace/own-input').write_text(role)
    config['roles'][role] = {'root': str(root), 'uid': uid, 'gid': uid}
path = base / 'config.json'
path.write_text(json.dumps(config))
path.chmod(0o600)
log = (base / 'broker.log').open('w')
broker = subprocess.Popen([sys.executable, str(script), str(path)], stdout=log, stderr=log)
try:
    deadline = time.monotonic() + 60
    address = '\0' + config['socket'][1:]
    while True:
        try:
            with socket.socket(socket.AF_UNIX) as probe:
                probe.connect(address)
            break
        except (ConnectionRefusedError, FileNotFoundError):
            pass
        if broker.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError('Broker did not start')
        time.sleep(0.1)
    def connect(request, disconnect=False):
        with socket.socket(socket.AF_UNIX) as sock:
            sock.connect(address)
            sock.sendall(json.dumps(request).encode() + b'\n')
            if disconnect:
                return
            return json.loads(sock.makefile('rb').readline())
    def request(role, command, timeout=10):
        return dict(role=role, cwd='/workspace', argv=['/bin/bash', '-c', command], timeout=timeout)
    report = {}
    for role in config['roles']:
        result = connect(request(role, 'id -u; cat own-input; test ! -e /mnt/data/zhanglinfeng/workspace/.config/llm/dawnfm.env; test ! -e /proc/1/root; test ! -e /../evaluator/workspace; test -z "${OPENAI_API_KEY-}"; test -z "${HOME_HOST-}"'))
        assert result['returncode'] == 0 and result['cleanup_confirmed'], result
        assert result['stdout'].splitlines()[0] == str(config['roles'][role]['uid'])
        report[role] = {'uid': config['roles'][role]['uid'], 'filesystem_and_env_check': True}
    refused = connect(dict(role='author-01', cwd='/../../', argv=['/bin/cat', '/etc/passwd'], timeout=10))
    assert 'error' in refused
    report['traversal_refused'] = True
    # Regression: real repository packs exceed the old 64 MiB file limit.
    result = connect(request('author-01', "python3 -c \"from pathlib import Path; p=Path('large-pack-check'); f=p.open('wb'); f.seek(65*1024*1024); f.write(b'x'); f.close(); assert p.stat().st_size > 64*1024*1024; p.unlink()\""))
    assert result['returncode'] == 0 and result['cleanup_confirmed'], result
    report['large_git_pack_file_supported'] = True
    result = connect(request('author-01', 'sleep 30', timeout=0.3))
    # Add a sleep binary to fixture if the minimal tool set lacks it.
    if result['returncode'] == 127:
        target = Path(config['roles']['author-01']['root']) / 'bin/sleep'
        shutil.copy2('/bin/sleep', target)
        result = connect(request('author-01', 'sleep 30', timeout=0.3))
    assert result['termination'] == 'timeout' and result['cleanup_confirmed'], result
    report['timeout_cleanup'] = True
    connect(request('author-01', 'sleep 30'), disconnect=True)
    time.sleep(0.5)
    result = connect(request('author-01', 'echo ready'))
    assert result['returncode'] == 0 and result['cleanup_confirmed'], result
    report['disconnect_cleanup'] = True
    root = Path(config['roles']['author-01']['root'])
    shutil.copy2('/usr/bin/setsid', root / 'usr/bin/setsid')
    result = connect(request('author-01', 'setsid sleep 30 > /workspace/background.log 2>&1 &'))
    assert result['cleanup_confirmed'], result
    report['detached_child_cleanup'] = True
    # An untrusted role UID can reach an abstract socket name, but is rejected
    # through SO_PEERCRED before any command is accepted.
    code = 'import socket,json; s=socket.socket(socket.AF_UNIX); s.connect(' + repr(address) + '); s.sendall(b"{}\\n"); print(s.recv(4096).decode())'
    denied = subprocess.run(['/usr/bin/setpriv', '--reuid=21101', '--regid=21101', '--clear-groups', sys.executable, '-c', code], text=True, capture_output=True, timeout=10)
    assert denied.returncode == 0 and 'error' in denied.stdout, denied.stderr
    report['untrusted_uid_refused'] = True
    spec = importlib.util.spec_from_file_location('role_exec', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert all(not module.role_processes(value['uid']) for value in config['roles'].values())
    report['all_role_processes_released'] = True
    (w / '.state/harbor-eval/role-broker-proof.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
finally:
    broker.terminate()
    broker.wait(timeout=10)
    log.close()
