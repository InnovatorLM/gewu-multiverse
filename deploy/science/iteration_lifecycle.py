"""Operator-side reconciliation of author clocks with verified model runners."""
import datetime
import fcntl
import json
import os
from pathlib import Path
import stat
import time
from author_iteration_clock import reconcile_session
from command_watchdog import process_info


def runner_state(run,uid):
    try:
        pid=int((run/'session.pid').read_text())
        info=process_info(pid)
        argv=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(bytes([0]))
        return info['uid']==uid and info['state']!='Z' and b'--run-agent' in argv and str(run).encode() in argv
    except (OSError,ValueError):return False


def terminal_time(run):
    try:
        with (run/'transcript.jsonl').open('rb') as stream:
            stream.seek(0,2);size=stream.tell();stream.seek(max(0,size-16384));data=stream.read()
        for line in reversed(data.splitlines()):
            try:event=json.loads(line)
            except (ValueError,UnicodeError):continue
            if event.get('event')=='run_finished':
                return datetime.datetime.fromisoformat(event['ts'].replace('Z','+00:00')).timestamp()
    except (OSError,ValueError,KeyError):pass
    return None


def scan_clocks(config):
    errors=[]
    for name,entry in config['roles'].items():
        try:
            _scan_clocks(dict(controller_uid=config['controller_uid'],roles={name:entry}))
        except (OSError,ValueError,KeyError,TypeError) as error:
            # No ledger contents or arbitrary role-controlled error text in logs.
            errors.append(dict(role=name,error_type=type(error).__name__))
    if errors:print(json.dumps(dict(event='iteration_clock_reconciliation_failed',roles=errors)),flush=True)
    return errors


def _scan_clocks(config):
    for name,entry in config['roles'].items():
        if not name.startswith('author-'):continue
        root=Path(entry['root']);directory=root/'home/role/.state/author-iteration'
        if not directory.exists():continue
        # Refuse role-created path escapes before privileged file operations.
        if directory.resolve()!=directory or not directory.resolve().is_relative_to(root.resolve()):
            raise ValueError('Unsafe author clock directory')
        path=directory/'ledger.json'
        if not path.exists():continue
        lockfd=os.open(directory/'clock.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            os.fchown(lockfd,entry['uid'],entry['gid'])
            fcntl.flock(lockfd,fcntl.LOCK_EX)
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            with os.fdopen(fd,'r') as stream:
                info=os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size>1024*1024:raise ValueError('Invalid author ledger')
                state=json.load(stream)
            universe=root.parents[3]
            runs=list((universe/'.state/gewu-multiverse'/name).glob('run-*'))
            live=any(runner_state(run,config['controller_uid']) for run in runs)
            end=terminal_time(max(runs,key=lambda p:p.stat().st_mtime)) if runs and not live else None
            before=json.dumps(state,sort_keys=True)
            reconcile_session(state,live,time.time(),end)
            if json.dumps(state,sort_keys=True)!=before:
                pending=directory/('lifecycle-'+str(os.getpid())+'.pending')
                out=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                with os.fdopen(out,'w') as stream:json.dump(state,stream,ensure_ascii=False,indent=2)
                os.chown(pending,entry['uid'],entry['gid']);pending.replace(path)
        finally:os.close(lockfd)
