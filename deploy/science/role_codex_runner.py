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
import subprocess
import sys
import tempfile

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


def run(request):
    if set(request) != {'role', 'instruction', 'timeout'}:
        raise ValueError('Unexpected run fields')
    role = request['role']
    if role not in {'author', 'evaluator', 'curator'}:
        raise ValueError('Invalid role')
    if os.getuid() != {'author': 21001, 'evaluator': 21002, 'curator': 21003}[role]:
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
    if type(timeout) is not int or not 1 <= timeout <= 1740:
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
        env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': str(runtime / 'home'),
               'CODEX_HOME': str(runtime / 'codex'), 'TMPDIR': str(runtime / 'tmp'),
               'XDG_CACHE_HOME': str(runtime / 'cache'), 'LANG': 'C.UTF-8',
               'GEWU_ROLE_GATEWAY_TOKEN': token, 'GIT_ASKPASS': '/usr/local/bin/role-askpass',
               'GIT_TERMINAL_PROMPT': '0', 'NO_PROXY': '127.0.0.1,localhost'}
        completed = subprocess.run(['/usr/local/bin/codex', 'exec', '--json',
                                    '--sandbox', 'danger-full-access', '--skip-git-repo-check',
                                    '-C', '/workspace', '-o', str(runtime / 'last-message.txt'), '-'],
                                   input=guidance + request['instruction'], text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=timeout, env=env, cwd='/workspace')
        final = runtime / 'last-message.txt'
        report = {'harness': 'codex', 'role': role, 'provider': 'dawnfm', 'model': MODEL,
                  'exit_code': completed.returncode,
                  'events': completed.stdout, 'stderr': completed.stderr,
                  'final_message': final.read_text() if final.exists() else None}
        encoded = json.dumps(report, ensure_ascii=False)
        if token in encoded:
            raise ValueError('Gateway token appeared in outputs')
        print(encoded, flush=True)
        return completed.returncode
    finally:
        shutil.rmtree(runtime)


if __name__ == '__main__':
    sys.exit(run(json.loads(sys.argv[1])))
