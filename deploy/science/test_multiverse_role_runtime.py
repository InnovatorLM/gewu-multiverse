"""Use the actual Rust supervisor + native tool loop, with a mock LLM only."""
import http.server
import json
import os
from pathlib import Path
from install_role_skills import selected
import socket
import subprocess
import sys
import threading
import time

w = Path('/mnt/data/zhanglinfeng/workspace')
base = w / '.state/science-role-broker'
config_path = base / 'config.json'
config = json.loads(config_path.read_text())
binary = w / '.state/cargo-target/debug/gewu-multiverse'
requests = []
live = '--live' in sys.argv
check_command = 'set -e; id -u; git --version; runtime_check=$(mktemp -d ./.gewu-runtime-check.XXXXXX); git -C "$runtime_check" init --quiet; git -C "$runtime_check" -c user.name=Role -c user.email=role@example.invalid commit --allow-empty -m runtime-check --quiet; git -C "$runtime_check" rev-parse --is-inside-work-tree; rm -rf -- "$runtime_check"; python3 -I -c "import json,statistics; print(123)"; test ! -e /proc/1/root; test ! -e /mnt/data/zhanglinfeng/workspace/.config/llm/dawnfm.env; test -z "${OPENAI_API_KEY-}"; printf role-runtime-ok'
if live:
    assert os.environ.get('LLM_PROVIDER') == 'dawnfm'
    assert os.environ.get('OPENAI_MODEL') == 'deepseek-v4.1-flash-1017'
    assert os.environ.get('OPENAI_BASE_URL') == 'https://dawnfm.gravarc.cn/v1'
    assert os.environ.get('OPENAI_API_KEY')


class Model(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        requests.append(data)
        if any(message['role'] == 'tool' for message in data['messages']):
            message = dict(role='assistant', content='Verified role runtime checks completed.')
        else:
            message = dict(role='assistant', content=None, tool_calls=[dict(id='role-check', type='function', function=dict(name='shell', arguments=json.dumps(dict(command=check_command))))])
        answer = dict(id='mock-role-check', model='mock-only', choices=[dict(index=0, message=message, finish_reason='stop')], usage=dict(prompt_tokens=1, completion_tokens=1, total_tokens=2))
        payload = json.dumps(answer).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_):
        pass


http = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Model)
thread = threading.Thread(target=http.serve_forever, daemon=True)
thread.start()
log = (base / 'native-test-broker.log').open('w')
broker = subprocess.Popen([sys.executable, str(Path(__file__).with_name('role_exec.py')), str(config_path)], stdout=log, stderr=log)
try:
    deadline = time.monotonic() + 30
    address = '\0' + config['socket'][1:]
    while True:
        try:
            with socket.socket(socket.AF_UNIX) as probe:
                probe.connect(address)
            break
        except ConnectionRefusedError:
            if broker.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('Broker did not start')
            time.sleep(0.1)
    state = base / (('live' if live else 'mock') + '-native-tests-' + str(time.time_ns()))
    state.mkdir(exist_ok=True)
    os.chown(state, 65534, 65534)
    state.chmod(0o700)
    report = {'model': os.environ['OPENAI_MODEL'] if live else 'mock-only', 'live_model_calls': 0, 'roles': {}, 'state': str(state)}
    for role, entry in config['roles'].items():
        if live and role != 'author-01':
            continue
        run = state / role
        run.mkdir(exist_ok=True)
        os.chown(run, 65534, 65534)
        root = Path(entry['root'])
        instruction = run / 'instruction.md'
        instruction.write_text('Use the shell tool exactly once to execute this runtime check, then report observed results in one sentence. Do not do other work.\n' + check_command)
        instruction.chmod(0o644)
        credential = run / 'credentials.toml'
        key = os.environ['OPENAI_API_KEY'] if live else 'mock-transport-only'
        role_credential = json.loads((w/'.config/universe-roles'/ (role+'.json')).read_text())
        credential.write_text('model_key = ' + json.dumps(key) + '\n[forgejo_agent_tokens]\n' + role + ' = ' + json.dumps(role_credential['token']) + '\n')
        os.chown(credential, 65534, 65534)
        credential.chmod(0o600)
        plan = dict(run_id=role+'-runtime-test', agent=role, workspace=str(root/'workspace'), instruction=str(instruction), skills_dir=str(root/'skills'), endpoint='http://127.0.0.1:'+str(http.server_address[1])+'/v1/chat/completions', model='mock-only', credentials=str(credential), max_turns=3, steps=[], timeout_secs=60, confinement='role-broker', hide=[])
        if live:
            plan.update(endpoint=os.environ['OPENAI_BASE_URL']+'/chat/completions', model=os.environ['OPENAI_MODEL'], timeout_secs=240)
        (run / 'plan.json').write_text(json.dumps(plan))
        request_start = len(requests)
        env = os.environ.copy()
        env.update(GEWU_HARNESS='native', GEWU_ROLE_BROKER_CONFIG=str(config_path), HOME=str(state), TMPDIR=str(w/'.tmp'), NO_PROXY='127.0.0.1,localhost', no_proxy='127.0.0.1,localhost')
        env.pop('OPENAI_API_KEY', None)
        try:
            result = subprocess.run(['/usr/bin/setpriv','--reuid=65534','--regid=65534','--clear-groups',str(binary),'--run-agent',str(run)], env=env, text=True, capture_output=True, timeout=270 if live else 90)
        finally:
            credential.unlink(missing_ok=True)
        logs = (run / 'run.log').read_text()
        assert result.returncode == 0, logs[-2500:]
        assert key not in logs and role_credential['token'] not in logs
        events = [json.loads(line) for line in (run/'transcript.jsonl').read_text().splitlines()]
        assert any(event['event'] == 'tool_result' and event.get('exit_code') == 0 and 'role-runtime-ok' in event.get('output','') for event in events)
        model_requests = requests[request_start:]
        system_parts = [message.get('content', '') for request in model_requests
                        for message in request.get('messages', []) if message['role'] == 'system']
        # Live calls are recorded by the real model loop rather than the mock HTTP handler.
        for event in events:
            if event.get('event') != 'model_request':
                continue
            try:
                payload = json.loads(event.get('body', '{}'))
            except (TypeError, json.JSONDecodeError):
                continue
            system = payload.get('system')
            if isinstance(system, dict):
                system_parts.append(system.get('content', ''))
            for message in payload.get('messages', []):
                if message.get('role') == 'system':
                    system_parts.append(message.get('content', ''))
        assert system_parts, 'the role model request was not captured for skill inspection'
        system_text = '\n'.join(part for part in system_parts if isinstance(part, str))
        for skill in selected(role):
            body = (root/'skills'/skill/'SKILL.md').read_text()
            assert body.strip() in system_text, f'{role} model request omitted skill {skill}'
        if live:
            report['live_model_calls'] += sum(event['event'] == 'model_request_sent' for event in events)
        report['roles'][role] = dict(supervisor_exit_code=result.returncode, shell_and_model_loop_passed=True, credential_redaction_passed=True)
    if live and report['live_model_calls'] < 1:
        raise AssertionError('live model endpoint was not called')
    (w/'.state/harbor-eval'/ ('multiverse-role-runtime-live.json' if live else 'multiverse-role-runtime-mock.json')).write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
finally:
    broker.terminate()
    broker.wait(timeout=10)
    http.shutdown()
    http.server_close()
    log.close()
