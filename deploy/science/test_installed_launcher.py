"""Operator-only installed science UI smoke; no role loops are enabled."""
import sys
if '--live' not in sys.argv:
    raise SystemExit('Pass --live to start/stop the installed local science controller')
import fcntl,json,os,pty,select,signal,struct,subprocess,termios,time,tomllib
from pathlib import Path
import pyte

w=Path('/mnt/data/zhanglinfeng/workspace');u=w/'universes/my-terminal-bench-science'
settings=tomllib.loads((u/'.config/gewu-multiverse/multiverse.toml').read_text())
assert all(agent.get('desired')=='stopped' for agent in settings['agents']), 'Stop all roles before this no-model smoke test'
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',24,100,0,0))
env=os.environ.copy();env['TERM']='xterm-256color'
p=subprocess.Popen([str(u/'start')],cwd=u,env=env,stdin=slave,stdout=slave,stderr=slave,start_new_session=True);os.close(slave)
screen=pyte.Screen(100,24);stream=pyte.ByteStream(screen)
raw=bytearray();start=time.monotonic();stage=0;phase_at=None;deadline=start+90
repositories=False;stopped=False;help_seen=False;returned=False;snapshots={}
try:
 while p.poll() is None and time.monotonic()<deadline:
  if select.select([master],[],[],.1)[0]:
   try:block=os.read(master,65536)
   except OSError:break
   raw.extend(block);stream.feed(block)
  rendered='\n'.join(screen.display)
  ready='2 repositories' in rendered and 'team/terminal-bench-science' in rendered and 'team/workspace' in rendered
  repositories|=ready;stopped|=rendered.count('stopped')>=3
  if stage==1 and 'Keys' in rendered and 'esc close' in rendered:
   help_seen=True;snapshots.setdefault('help',rendered)
  if stage==2 and ready and 'esc close' not in rendered:
   returned=True;snapshots.setdefault('returned',rendered)
  if stage==0 and ready and stopped:
   snapshots['ready']=rendered;os.write(master,b'?');stage=1;phase_at=time.monotonic()
  elif stage==1 and help_seen and time.monotonic()-phase_at>1:
   os.write(master,b'\x1b');stage=2;phase_at=time.monotonic()
  elif stage==2 and returned and time.monotonic()-phase_at>3:
   os.write(master,b'q');stage=3
 if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
 p.wait(timeout=15)
finally:
 os.close(master)
for name,data in [('installed-launcher-terminal.raw',bytes(raw)),('installed-launcher-screen-snapshots.json',json.dumps(snapshots,indent=2).encode())]:
 capture=w/'.state/harbor-eval'/name;capture.write_bytes(data);capture.chmod(0o600)
report={'installed_launcher_exit_code':p.returncode,'ui_two_repositories_rendered':repositories,'roles_stopped_rendered':stopped,'interactive_help_and_return':help_seen and returned,'normal_quit_sent':stage==3,'model_calls_requested':0,'terminal_decoder':'pyte0.8.2'}
(w/'.state/harbor-eval/installed-launcher-final-smoke.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert p.returncode==0 and repositories and stopped and help_seen and returned and stage==3
