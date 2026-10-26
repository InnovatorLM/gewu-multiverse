"""Operator-only installed science UI smoke; no role loops are enabled."""
import sys,tomllib
if '--live' not in sys.argv:
    raise SystemExit('Pass --live to start/stop the installed local science controller')
import fcntl,json,os,pty,re,select,signal,struct,subprocess,termios,time
from pathlib import Path
w=Path('/mnt/data/zhanglinfeng/workspace');u=w/'universes/my-terminal-bench-science'
settings=tomllib.loads((u/'.config/gewu-multiverse/multiverse.toml').read_text())
assert all(agent.get('desired')=='stopped' for agent in settings['agents']), 'Stop all roles before this no-model smoke test'
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',24,100,0,0))
env=os.environ.copy();env['TERM']='xterm-256color'
p=subprocess.Popen([str(u/'start')],cwd=u,env=env,stdin=slave,stdout=slave,stderr=slave,start_new_session=True);os.close(slave)
raw=bytearray();start=time.monotonic();stage=0;phase_at=None;deadline=start+90
try:
 while p.poll() is None and time.monotonic()<deadline:
  elapsed=time.monotonic()-start
  rendered=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',raw.decode(errors='replace'))
  if elapsed>2 and stage==0 and '2 repositories' in rendered:
   os.write(master,b'?');stage=1;phase_at=time.monotonic()
  elif stage==1 and time.monotonic()-phase_at>1:
   os.write(master,b'\x1b');stage=2;phase_at=time.monotonic()
  elif stage==2 and time.monotonic()-phase_at>3:
   os.write(master,b'q');stage=3
  if select.select([master],[],[],.1)[0]:
   try:raw.extend(os.read(master,65536))
   except OSError:break
 if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
 p.wait(timeout=15)
finally:
 os.close(master)
text=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',raw.decode(errors='replace'))
capture=w/'.state/harbor-eval/installed-launcher-terminal.raw'
capture.write_bytes(raw);capture.chmod(0o600)
plain=w/'.state/harbor-eval/installed-launcher-terminal.txt'
plain.write_text(text);plain.chmod(0o600)
report={'installed_launcher_exit_code':p.returncode,'ui_two_repositories_rendered':'2 repositories' in text,'roles_stopped_rendered':text.count('stopped')>=3,'interactive_help_and_return':stage>=2,'normal_quit_sent':stage==3,'model_calls_requested':0}
(w/'.state/harbor-eval/installed-launcher-final-smoke.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert p.returncode==0 and report['ui_two_repositories_rendered'] and report['roles_stopped_rendered']
