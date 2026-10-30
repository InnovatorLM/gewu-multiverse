"""Real controller -> SessionSpawner -> isolated Git clone/fetch; no LLM calls."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

w = Path('/mnt/data/zhanglinfeng/workspace')
base = w / '.state/science-role-broker'
config = base / 'config.json'
data = json.loads(config.read_text())
parser=argparse.ArgumentParser()
parser.add_argument('--role',action='append',choices=list(data['roles']))
args=parser.parse_args()
selected=args.role or list(data['roles'])
state = base / ('prepare-check-' + str(time.time_ns()))
state.mkdir(mode=0o700)
os.chown(state,65534,65534)
log = (base/'prepare-check-broker.log').open('w')
broker = subprocess.Popen([sys.executable,str(Path(__file__).with_name('role_exec.py')),str(config)],stdout=log,stderr=log)
try:
    deadline=time.monotonic()+15
    address='\0'+data['socket'][1:]
    while True:
        try:
            with socket.socket(socket.AF_UNIX) as stream:
                stream.connect(address)
            break
        except ConnectionRefusedError:
            if broker.poll() is not None or time.monotonic()>deadline:
                raise RuntimeError('Broker did not start')
            time.sleep(.1)
    env=os.environ.copy()
    env.update(GEWU_ROLE_BROKER_CONFIG=str(config),GEWU_HARNESS='native',TMPDIR=str(w/'.tmp'),HOME=str(state),NO_PROXY='127.0.0.1,localhost',no_proxy='127.0.0.1,localhost')
    report={}
    for role in selected:
        # Second preparation exercises reuse/fetch, with all Git operations
        # inside the same role boundary as model-requested commands.
        for attempt in [1,2]:
            result=subprocess.run(['/usr/bin/setpriv','--reuid=65534','--regid=65534','--clear-groups',str(w/'.state/cargo-target/debug/examples/science-role-session-check'),role,str(state),str(w/'.state/cargo-target/debug/gewu-multiverse')],env=env,text=True,capture_output=True,timeout=1900)
            if result.returncode:
                raise RuntimeError(role+' preparation failed: '+result.stderr[-1000:])
        report[role]={'real_session_prepare':True,'clone_or_reuse':True,'subsequent_fetch':True,'model_calls':0}
    (w/'.state/harbor-eval/role-real-session-prepare.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
finally:
    broker.terminate()
    broker.wait(timeout=10)
    log.close()
