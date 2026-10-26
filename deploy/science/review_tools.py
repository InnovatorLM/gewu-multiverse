"""Independent reviewer calculation tools; no host/model credentials in commands."""
import fcntl
import json
import os
import shutil
import signal
import socket

from evaluation_queue import W, digest_tree
from role_exec import execute, role_processes, trusted

UID = 21012
TOOL = {'type': 'function', 'function': {'name': 'review_shell', 'description': 'Execute a calculation or inspect task files inside a credential-free nonroot chroot. Read-only task at /task; writable scratch /tmp. Network permitted. Python standard library available.', 'parameters': {'type': 'object', 'properties': {'command': {'type': 'string'}}, 'required': ['command'], 'additionalProperties': False}}}


class ReviewTools:
    def __init__(self, root, snapshot_hash):
        if os.geteuid() != 0:
            raise ValueError('Operator/root required')
        self.root = trusted(root, directory=True)
        state = trusted(W / '.state/science-review-tools', directory=True)
        if not self.root.is_relative_to(state) or self.root == state:
            raise ValueError('Review root must be inside private reviewer state')
        if (self.root / 'proc/1').exists() or (self.root / 'proc/self/root').exists():
            raise ValueError('Host proc exposed')
        if digest_tree(self.root / 'task') != snapshot_hash:
            raise ValueError('Tool task does not match registered snapshot')
        self.lock = os.fdopen(os.open(state / 'session.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600), 'a')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if role_processes(UID):
                raise ValueError('Review UID already has live processes')
            scratch = self.root / 'tmp'
            if scratch.is_symlink() or not scratch.is_dir():
                raise ValueError('Scratch must be a real directory')
            shutil.rmtree(scratch)
            scratch.mkdir(mode=0o700)
            os.chown(scratch, UID, UID)
        except BlockingIOError as error:
            self.lock.close()
            raise ValueError('Review session already active') from error
        except BaseException:
            self.lock.close()
            raise
        self.calls = []

    def close(self):
        self.lock.close()

    def call(self, call):
        if len(self.calls) >= 10:
            raise ValueError('Review shell-call allowance exhausted')
        if call.get('type') != 'function' or call['function']['name'] != 'review_shell':
            raise ValueError('Unknown review tool')
        arguments = json.loads(call['function']['arguments'])
        if set(arguments) != {'command'} or not isinstance(arguments['command'], str) or len(arguments['command']) > 32000:
            raise ValueError('Invalid shell arguments')
        if not isinstance(call.get('id'), str) or call['id'] in {item['tool_call_id'] for item in self.calls}:
            raise ValueError('Duplicate or invalid tool-call ID')
        config = {'controller_uid': 65534, 'roles': {'evaluator': {'root': str(self.root), 'uid': UID, 'gid': UID}}}
        reader, writer = socket.socketpair()
        pid = os.fork()
        if pid == 0:
            # Parent process-group termination must leave EOF cleanup alive.
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            writer.close()
            try:
                result = execute(config, {'role': 'evaluator', 'cwd': '/task', 'argv': ['/bin/bash', '-lc', arguments['command']], 'timeout': 120}, reader)
                reader.sendall(json.dumps(result).encode() + b'\n')
            except BaseException:
                pass
            finally:
                reader.close()
                os._exit(0)
        reader.close()
        writer.settimeout(135)
        chunks = bytearray()
        try:
            while not chunks.endswith(b'\n'):
                block = writer.recv(65536)
                if not block:
                    raise ValueError('Reviewer executor disconnected without a result')
                chunks.extend(block)
                if len(chunks) > 8 * 1024 * 1024:
                    raise ValueError('Reviewer executor response oversized')
            result = json.loads(chunks)
        finally:
            # EOF also cleans tools when the controller crashes or is killed.
            writer.close()
            os.waitpid(pid, 0)
        self.calls.append({'tool_call_id': call['id'], 'command': arguments['command'], **result})
        if not result['cleanup_confirmed']:
            raise ValueError('Reviewer command cleanup unconfirmed')
        # Full results remain private. Explicitly mark any model-context clipping.
        return {**result, 'tool_call_id': call['id'], 'stdout': result['stdout'][:24000], 'stderr': result['stderr'][:8000], 'context_clipped': len(result['stdout']) > 24000 or len(result['stderr']) > 8000}


def validate_evidence(review, calls):
    references = review.get('tool_evidence')
    if not isinstance(references, list) or not calls:
        raise ValueError('Tool-backed review requires actual tools and evidence references')
    completed = {item['tool_call_id']: item for item in calls if item['returncode'] == 0 and item['cleanup_confirmed']}
    issue_ids = {issue['id'] for issue in review['issues']}
    covered = set()
    for ref in references:
        if not isinstance(ref, dict) or set(ref) != {'issue_id', 'tool_call_id', 'quote'}:
            raise ValueError('Invalid evidence reference')
        call = completed.get(ref['tool_call_id'])
        if call is None or ref['issue_id'] not in issue_ids | {'summary'}:
            raise ValueError('Evidence must cite an actual successful call and known issue')
        quote = ref['quote']
        if not isinstance(quote, str) or len(quote.strip()) < 8 or not any(quote in call[key] for key in ['stdout', 'stderr']):
            raise ValueError('Evidence quote absent from actual output')
        covered.add(ref['issue_id'])
    if not issue_ids <= covered or not references:
        raise ValueError('Every issue requires a tool-output citation')


def replay_for_finalization(responses, calls):
    """Continue one interrupted review, never count a new independent review."""
    known = {call['tool_call_id']: call for call in calls}
    seen = set()
    messages = []
    usage = {'prompt_tokens': 0, 'completion_tokens': 0}
    for response in responses:
        for field in usage:
            value = (response.get('usage') or {}).get(field)
            if type(value) is not int or value < 0:
                raise ValueError('Invalid retained usage')
            usage[field] += value
        choice = response['choices'][0]
        message = choice['message']
        requested = message.get('tool_calls')
        if choice.get('finish_reason') != 'tool_calls' or not isinstance(requested, list) or not requested:
            raise ValueError('Only unfinished tool reviews may be finalized')
        messages.append({'role': 'assistant', 'content': message.get('content'), 'tool_calls': requested})
        for call in requested:
            identifier = call['id']
            if identifier in seen:
                raise ValueError('Duplicate retained call ID')
            seen.add(identifier)
            if identifier in known:
                saved = known[identifier]
                if saved['command'] != json.loads(call['function']['arguments'])['command']:
                    raise ValueError('Retained command mismatch')
                result = {key: saved[key] for key in ['returncode', 'stdout', 'stderr', 'termination', 'cleanup_confirmed']}
                result.update(stdout=saved['stdout'][:24000], stderr=saved['stderr'][:8000], context_clipped=len(saved['stdout']) > 24000 or len(saved['stderr']) > 8000)
            else:
                if len(known) != 10 or not set(known) <= seen:
                    raise ValueError('Missing command output before allowance exhaustion')
                result = {'not_executed': True, 'reason': 'Tool allowance exhausted; finalize from existing evidence'}
            messages.append({'role': 'tool', 'tool_call_id': identifier, 'content': json.dumps(result)})
    if not known or not set(known) <= seen:
        raise ValueError('Retained evidence was not requested by this session')
    return messages, usage


def submission_tool(gate_statuses):
    """Give the provider the actual report shape, not only a prose contract."""
    def obj(properties):
        return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}
    text = {'type': 'string', 'minLength': 1}
    dimension = obj({'score': {'type': ['integer', 'null'], 'minimum': 0, 'maximum': 4}, 'reason': text})
    issue = obj({'id': text, 'dimension': {'type': 'string', 'enum': ['science', 'contract', 'verifier', 'integrity', 'research_work', 'feasibility']}, 'severity': {'type': 'string', 'enum': ['blocker', 'major', 'minor']}, 'certainty': {'type': 'string', 'enum': ['confirmed', 'suspected']}, 'path': text, 'description': text})
    suggestion = obj({'issue_id': text, 'change': text, 'acceptance_check': text})
    parameters = obj({'task_id': text, 'summary': text, 'dimensions': obj({name: dimension for name in ['science', 'contract', 'verifier', 'integrity', 'research_work', 'feasibility']}), 'gate': obj({'status': {'type': 'string', 'enum': list(gate_statuses)}, 'reason': text}), 'difficulty': obj({'level': {'type': ['integer', 'null'], 'minimum': 1, 'maximum': 5}, 'confounded': {'type': 'boolean'}, 'reason': text}), 'issues': {'type': 'array', 'items': issue}, 'suggestions': {'type': 'array', 'items': suggestion}, 'limitations': {'type': 'array', 'items': text}, 'tool_evidence': {'type': 'array', 'items': obj({'issue_id': text, 'tool_call_id': text, 'quote': text})}})
    return {'type': 'function', 'function': {'name': 'submit_review', 'description': 'Submit the final evidence-backed review using exactly this schema. All scientific claims must be supported by actual tool evidence. This is not release acceptance.', 'parameters': parameters}}
