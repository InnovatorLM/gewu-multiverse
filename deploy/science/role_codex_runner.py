#!/usr/local/bin/python3
"""Run inside the dedicated role chroot, never directly on the host.

The broker supplies an ephemeral gateway token, not an upstream API key.
Filesystem isolation is supplied by chroot plus dedicated UID/no_new_privs;
Codex's own danger-full-access setting is limited to that existing boundary.
"""
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid

MODEL = 'deepseek-v4.1-flash-1017'


def config(port):
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError('Invalid gateway port')
    return chr(10).join([
        'model = "' + MODEL + '"',
        'model_provider = "dawnfm-role-gateway"',
        'approval_policy = "never"',
        'sandbox_mode = "danger-full-access"',
        'cli_auth_credentials_store = "file"',
        '[shell_environment_policy]',
        'inherit = "none"',
        '[model_providers.dawnfm-role-gateway]',
        'name = "dawnfm role gateway"',
        'base_url = "http://127.0.0.1:' + str(port) + '/v1"',
        'wire_api = "responses"',
        'env_key = "GEWU_ROLE_GATEWAY_TOKEN"',
        '',
    ])


def capture(command, *, prompt, env, cwd, timeout, archive, secrets=()):
    """Stream redacted lines to durable files, including on timeout."""
    archive.mkdir(mode=0o700, parents=True, exist_ok=False)
    def redact(text):
        for secret in secrets:
            if secret:
                text = text.replace(secret, '[REDACTED]')
        return text
    metadata = {'status': 'running', 'started_at': time.time(), 'harness': 'codex',
                'provider': 'dawnfm', 'model': MODEL}
    def save():
        p = archive / 'metadata.json'
        pending = p.with_suffix('.pending')
        pending.write_text(json.dumps(metadata, indent=2)); pending.chmod(0o600)
        pending.replace(p)
    save()
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=env, cwd=cwd, start_new_session=True)
    outputs = {'events': [], 'stderr': []}
    errors = []
    def pump(pipe, name, filename):
        try:
            with (archive / filename).open('w') as target:
                os.chmod(target.name, 0o600)
                for raw in iter(pipe.readline, b''):
                    line = redact(raw.decode('utf-8', errors='replace'))
                    target.write(line); target.flush()
                    outputs[name].append(line)
        except Exception as error:
            errors.append(str(error))
        finally:
            pipe.close()
    threads = [threading.Thread(target=pump, args=(process.stdout, 'events', 'events.jsonl')),
               threading.Thread(target=pump, args=(process.stderr, 'stderr', 'stderr.log'))]
    for thread in threads: thread.start()
    timed_out = False
    try:
        try:
            process.stdin.write(prompt.encode()); process.stdin.close()
        except BrokenPipeError:
            process.stdin.close()
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL); process.wait()
    finally:
        for thread in threads: thread.join()
        metadata.update(status='timeout' if timed_out else 'completed' if process.returncode == 0 else 'failed',
                        exit_code=process.returncode, finished_at=time.time(), capture_errors=errors)
        save()
    if errors:
        raise ValueError('Trajectory persistence failed')
    return {'returncode': 124 if timed_out else process.returncode,
            'events': ''.join(outputs['events']), 'stderr': ''.join(outputs['stderr'])}


def run(request):
    if set(request) != {'role', 'instruction', 'timeout'}:
        raise ValueError('Unexpected run fields')
    role = request['role']
    if role == 'curator':
        expected_uid = 21014
    else:
        match = re.fullmatch(r'(author|evaluator)-(\d{2})', role)
        if not match:
            raise ValueError('Invalid role')
        expected_uid = (21000 + int(match.group(2)) if match.group(1) == 'author'
                        else 21010 + int(match.group(2)))
    if os.getuid() != expected_uid:
        raise ValueError('Dedicated nonroot role required')
    if Path('/proc/1').exists() or Path('/mnt/data/zhanglinfeng/workspace/.config/llm/dawnfm.env').exists():
        raise ValueError('Host files exposed')
    if not isinstance(request['instruction'], str) or len(request['instruction'].encode()) > 90000:
        raise ValueError('Invalid instruction')
    guidance = (
        'You are the ' + role + ' role in an isolated workspace. '
        'Forgejo URL: http://127.0.0.1:3000. Use role-forgejo assigned to list assigned issues; '
        'role-forgejo read --issue N to read an issue; role-forgejo comment --issue N --body-file PATH to post feedback. '
        'These commands replace forgejo_list_assigned_issues and forgejo_read_issue_or_pull named in role instructions. '
        'Use only assigned work; do not print credentials or private review material. '
        'All generated files belong under /workspace or the provided temporary runtime.' + chr(10)
    )
    timeout = request['timeout']
    if type(timeout) is not int or not 1 <= timeout <= 14400:
        raise ValueError('Invalid timeout')
    token = os.environ['GEWU_ROLE_GATEWAY_TOKEN']
    if not re.fullmatch(r'[a-f0-9]{64}', token):
        raise ValueError('Invalid ephemeral gateway token')
    port = int(os.environ['GEWU_ROLE_GATEWAY_PORT'])
    runtime = Path(tempfile.mkdtemp(prefix='role-codex-', dir='/tmp'))
    try:
        for name in ('codex', 'home', 'tmp', 'cache'):
            (runtime / name).mkdir(mode=0o700)
        settings = runtime / 'codex/config.toml'
        settings.write_text(config(port)); settings.chmod(0o600)
        env = {'PATH': '/home/role/.local/bin:/home/role/.local/env/bin:/usr/local/bin:/usr/bin:/bin', 'MAMBA_ROOT_PREFIX': '/home/role/.local/mamba', 'CONDA_PREFIX': '/home/role/.local/env', 'HOME': str(runtime / 'home'),
               'CODEX_HOME': str(runtime / 'codex'), 'TMPDIR': str(runtime / 'tmp'),
               'XDG_CACHE_HOME': str(runtime / 'cache'), 'LANG': 'C.UTF-8',
               'GEWU_ROLE_GATEWAY_TOKEN': token, 'GIT_ASKPASS': '/usr/local/bin/role-askpass',
               'GIT_TERMINAL_PROMPT': '0', 'NO_PROXY': '127.0.0.1,localhost'}
        archive = Path('/home/role/trajectories') / (str(time.time_ns()) + '-' + uuid.uuid4().hex[:10])
        credential = Path('/home/role/git-credential.json')
        git_token = json.loads(credential.read_text()).get('token', '') if credential.exists() else ''
        secrets = (token, git_token)
        completed = capture(['/usr/local/bin/codex', 'exec', '--json',
                             '--sandbox', 'danger-full-access', '--skip-git-repo-check',
                             '-C', '/workspace', '-o', str(runtime / 'last-message.txt'), '-'],
                            prompt=guidance + request['instruction'], env=env, cwd='/workspace',
                            timeout=timeout, archive=archive, secrets=secrets)
        final = runtime / 'last-message.txt'
        final_text = final.read_text() if final.exists() else None
        if final_text is not None:
            for secret in secrets:
                if secret: final_text = final_text.replace(secret, '[REDACTED]')
            saved = archive / 'final-message.txt'
            saved.write_text(final_text); saved.chmod(0o600)
        metadata_path = archive / 'metadata.json'
        metadata = json.loads(metadata_path.read_text()); metadata['role'] = role
        pending_metadata = archive / 'metadata.pending'
        pending_metadata.write_text(json.dumps(metadata, indent=2)); pending_metadata.chmod(0o600)
        pending_metadata.replace(metadata_path)
        report = {'harness': 'codex', 'role': role, 'provider': 'dawnfm', 'model': MODEL,
                  'exit_code': completed['returncode'],
                  'events': completed['events'], 'stderr': completed['stderr'],
                  'trajectory_dir': str(archive), 'final_message': final_text}
        encoded = json.dumps(report, ensure_ascii=False)
        if token in encoded:
            raise ValueError('Gateway token appeared in outputs')
        print(encoded, flush=True)
        return completed['returncode']
    finally:
        shutil.rmtree(runtime)


if __name__ == '__main__':
    sys.exit(run(json.loads(sys.argv[1])))
