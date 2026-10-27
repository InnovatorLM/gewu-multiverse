#!/usr/bin/env python3
"""Trusted Pod-side unified quality driver; key arrives only through stdin.

The operator supplies a fixed task bundle and runtime. This worker does not
create Pods, choose models, publish results, or authorize scientific acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

WORKSPACE = Path('/mnt/data/zhanglinfeng/workspace')
MODEL = 'deepseek-v4.1-flash-1017'
ENDPOINT = 'https://dawnfm.gravarc.cn/v1'


def inventory(task):
    result = {}
    for path in sorted(task.rglob('*')):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError('Task links and special files are refused')
        if path.is_file():
            result[path.relative_to(task).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    required = {'instruction.md', 'task.toml', 'environment/Dockerfile',
                'solution/solve.sh', 'tests/test.sh'}
    if not required <= result.keys():
        raise ValueError('Missing standard Harbor task inputs')
    return result


def contract(root, task_name):
    root = Path(root)
    if (not root.is_absolute() or root.is_symlink()
            or not re.fullmatch(r'qa-live-[a-f0-9]{10}', root.name)
            or root.parent.resolve() != WORKSPACE / '.state'):
        raise ValueError('Worker root must be an exact operator run directory')
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,127}', task_name):
        raise ValueError('Invalid task identity')
    task = root / 'tasks' / task_name
    if task.is_symlink() or not task.is_dir() or task.resolve() != task:
        raise ValueError('Task escaped the supplied bundle')
    return task, inventory(task)


def command(root, task):
    return ['python3', '-m', 'unified_evaluator.pipelines.quality_review', str(task),
            '--codex-bin', str(root / 'runtime/bin/codex'),
            '--codex-home', str(root / 'provider'), '--model', MODEL,
            '--env-file', str(root / 'provider/no-credential-file'),
            '--runtime-root', str(root / 'active'), '--log-dir', str(root / 'logs'),
            '--output', str(root / 'output/review.json'), '--timeout', '1800']


def run(root, task_name, key):
    task, before = contract(root, task_name)
    if os.geteuid() != 0 or not key or len(key) > 16384 or '\n' in key or '\r' in key:
        raise ValueError('Require trusted root worker and one stdin credential')
    uid = 21012
    for name in ['home', 'provider', 'tmp', 'output', 'logs', 'active', 'runtime/codex-path']:
        path = root / name
        if path.is_symlink() or path.exists():
            raise ValueError('Worker state must be fresh')
        path.mkdir(parents=True, mode=0o700 if name != 'runtime/codex-path' else 0o755)
    (root / 'runtime/codex-path/codex-linux-sandbox').symlink_to('../bin/codex')
    config = ('model = "' + MODEL + '"\nmodel_provider = "dawnfm"\n'
              'model_reasoning_effort = "medium"\n[model_providers.dawnfm]\n'
              'name = "dawnfm"\nbase_url = "' + ENDPOINT + '"\n'
              'wire_api = "responses"\nenv_key = "OPENAI_API_KEY"\n')
    provider = root / 'provider/config.toml'
    provider.write_text(config)
    provider.chmod(0o600)
    os.chown(provider, uid, uid)
    for name in ['home', 'provider', 'tmp', 'output', 'logs', 'active']:
        os.chown(root / name, uid, uid)
    env = {'PATH': str(root / 'runtime/codex-path') + ':/usr/local/bin:/usr/bin:/bin',
           'HOME': str(root / 'home'), 'TMPDIR': str(root / 'tmp'), 'LANG': 'C.UTF-8',
           'PYTHONPATH': str(root / 'source'), 'PYTHONDONTWRITEBYTECODE': '1',
           'CODEX_HOME': str(root / 'provider'), 'OPENAI_API_KEY': key,
           'OPENAI_MODEL': MODEL, 'LLM_PROVIDER': 'dawnfm', 'OPENAI_BASE_URL': ENDPOINT,
           'XDG_CONFIG_HOME': str(root / 'home'), 'XDG_CACHE_HOME': str(root / 'tmp')}

    def drop():
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)

    child = None
    cancelled = False

    def stop(_signum, _frame):
        nonlocal cancelled
        cancelled = True
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)

    previous = {sig: signal.signal(sig, stop) for sig in [signal.SIGTERM, signal.SIGINT]}
    started = time.monotonic()
    error_type = None
    exit_code = None
    try:
        with (root / 'driver.log').open('x') as log:
            child = subprocess.Popen(command(root, task), env=env, cwd=root / 'source',
                                     stdout=log, stderr=log, preexec_fn=drop,
                                     start_new_session=True, stdin=subprocess.DEVNULL)
            if cancelled:
                stop(None, None)
            try:
                exit_code = child.wait(timeout=1840)
            except subprocess.TimeoutExpired:
                error_type = 'WorkerTimeout'
    finally:
        if child is not None:
            # Also terminate descendants after the leader has exited.
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            if child.poll() is None:
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=5)
            # A descendant may survive its leader or ignore TERM. This worker
            # owns the fresh process group; never target another run's group.
            time.sleep(0.1)
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    findings = []
    for path in [root / 'driver.log', *(root / 'active').rglob('*'),
                 *(root / 'logs').rglob('*'), *(root / 'output').rglob('*')]:
        if path.is_symlink():
            raise ValueError('Unexpected link in retained outputs')
        if path.is_file():
            data = path.read_bytes()
            if key.encode() in data:
                findings.append(path.relative_to(root).as_posix())
                path.write_bytes(data.replace(key.encode(), b'[REDACTED]'))
            path.chmod(0o600)
    result = {'exit_code': exit_code, 'error_type': error_type, 'cancelled': cancelled,
              'elapsed_seconds': round(time.monotonic() - started, 2),
              'task_unchanged': inventory(task) == before, 'task_files': len(before),
              'provider': 'dawnfm', 'endpoint': ENDPOINT, 'model': MODEL, 'uid': uid,
              'valid_review_exists': (root / 'output/review.json').is_file(),
              'secret_findings_before_redaction': findings,
              'scientific_acceptance': False}
    path = root / 'result.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    path.chmod(0o600)
    return result


def main():
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--task-name', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.task_name, sys.stdin.read(16385).strip())))


if __name__ == '__main__':
    main()
