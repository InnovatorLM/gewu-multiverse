"""Wait for one identified recovery process, then verify actual Universe storage.

No scheduler/model calls. Any missing role verification blocks the final report.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

W=Path('/mnt/data/zhanglinfeng/workspace')

def process_identity(pid):
    try:return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
    except (FileNotFoundError,ProcessLookupError):return None

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--recovery-pid',type=int,required=True)
    args=parser.parse_args()
    identity=process_identity(args.recovery_pid)
    if identity is None:raise SystemExit('Recovery process is not live at verification start')
    out=W/'.state/storage-investigation'
    out.mkdir(parents=True,exist_ok=True)
    report={'passed':False,'state':'waiting_for_recovery','started_at':time.time(),
            'recovery_pid':args.recovery_pid,'recovery_start_identity':identity,'checks':{}}
    def save():
        pending=out/'recovery-verification.pending'
        pending.write_text(json.dumps(report,indent=2)+'\n')
        pending.replace(out/'recovery-verification.json')
    save()
    while process_identity(args.recovery_pid)==identity:
        time.sleep(15)
    try:
        with (W/'.state/universe-maintenance/preinstall.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            cfg=json.loads((W/'.state/science-role-broker/config.json').read_text())
            missing=[]
            for name,r in cfg['roles'].items():
                p=Path(r['root'])/'home/role/.local/env/gewu-preinstalled-v1.json'
                if not p.exists():missing.append(name);continue
                info=p.stat()
                if info.st_uid!=r['uid'] or info.st_mode&0o777!=0o600 or json.loads(p.read_text()).get('imports_and_cpp_verified') is not True:
                    missing.append(name)
            if missing:raise RuntimeError('Missing or invalid environment verification: '+','.join(missing))
            report.update(state='verifying')
            save()
            for filename in ('verify_universe_storage.py','test_session_prepare.py'):
                env=os.environ.copy()
                env.update(TMPDIR=str(W/'.tmp'),PYTHONDONTWRITEBYTECODE='1')
                with (out/(filename+'.log')).open('w') as log:
                    result=subprocess.run([sys.executable,str(Path(__file__).with_name(filename))],env=env,stdout=log,stderr=log,timeout=3600)
                report['checks'][filename]={'returncode':result.returncode}
                save()
                if result.returncode:raise RuntimeError(filename+' failed; inspect its log')
            report.update(passed=True,state='verified',role_count=len(cfg['roles']))
    except Exception as error:
        report.update(state='failed',error=str(error))
    report['finished_at']=time.time()
    save()
    print(json.dumps(report),flush=True)
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
