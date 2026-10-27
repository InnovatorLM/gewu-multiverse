#!/usr/bin/env python3
"""Install a hash-pinned pure Python TOML reader inside isolated role roots.

This supplies syntax parsing only, not Harbor schema validation or acceptance.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import zipfile
from evaluation_queue import W, atomic_json
from role_exec import role_processes

URL = 'https://files.pythonhosted.org/packages/6e/c2/61d3e0f47e2b74ef40a68b9e6ad5984f6241a942f7cd3bbfbdbd03861ea9/tomli-2.2.1-py3-none-any.whl'
SHA256 = 'cb55c73c5f4408779d0cf3eef9f762b9c9f147a77de7b258bef0a5628adc85cc'


def main():
    if os.geteuid() != 0:
        raise ValueError('Operator required')
    config = json.loads((W / '.state/science-role-broker/config.json').read_text())
    if any(role_processes(role['uid']) for role in config['roles'].values()):
        raise ValueError('Stop role processes before runtime changes')
    with urllib.request.urlopen(URL, timeout=30) as response:
        raw = response.read(1024 * 1024)
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError('TOML reader package digest mismatch')
    archive = W / '.cache/role-runtime/tomli-2.2.1-py3-none-any.whl'
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(raw)
    roots = [W / '.state/role-chroot-proof'] + [Path(r['root']) for r in config['roles'].values()]
    installed = []
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        members = [entry for entry in bundle.infolist() if entry.filename.startswith(('tomli/', 'tomli-2.2.1.dist-info/')) and not entry.is_dir()]
        for root in roots:
            target = root / 'usr/local/lib/python3.10'
            for entry in members:
                relative = Path(entry.filename)
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('Unsafe package member')
                path = target / relative
                if path.is_symlink():
                    raise ValueError('Runtime links refused')
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                content = bundle.read(entry)
                if path.exists() and path.read_bytes() != content:
                    raise ValueError('Refuse overwriting different TOML reader')
                path.write_bytes(content)
                os.chown(path, 0, 0)
                path.chmod(0o644)
            installed.append(str(root.relative_to(W)))
    checks = []
    code = 'import tomli; assert tomli.__version__=="2.2.1"; assert tomli.loads("[environment]\\ncpus=2\\nmemory_mb=4096")["environment"]["cpus"]==2; print("PINNED_TOML_READER_OK")'
    for name, role in config['roles'].items():
        result = subprocess.run(['chroot', f'--userspec={role["uid"]}:{role["gid"]}', role['root'],
                                 '/usr/local/bin/python3', '-B', '-c', code], capture_output=True, timeout=15)
        if result.returncode != 0:
            raise ValueError('Actual role TOML parser check failed: ' + name)
        checks.append({'role': name, 'uid': role['uid'], 'parser_check_passed': True})
    proof = {'package': 'tomli', 'version': '2.2.1', 'wheel_sha256': SHA256,
             'installed_roots': installed, 'actual_role_checks': checks,
             'model_calls': 0, 'harbor_schema_validation_claimed': False}
    atomic_json(W / '.state/harbor-eval/role-toml-runtime-proof.json', proof)
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
