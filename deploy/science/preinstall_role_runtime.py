"""Preinstall verified user-space environment separately in every role root."""
import argparse,fcntl,json,os,signal,subprocess,tempfile
from pathlib import Path
W=Path('/mnt/data/zhanglinfeng/workspace')
PACKAGES=['python=3.11','pip','numpy','scipy','pandas','sympy','matplotlib-base','scikit-learn','netcdf4','astropy','h5py','pytest','requests','pyyaml','pillow','cmake','make','pkg-config','c-compiler','cxx-compiler','git','curl','coreutils','findutils','grep','sed','gawk','tar','gzip','bzip2','xz','unzip','ca-certificates']
def run_owned(command,timeout,**kwargs):
    with subprocess.Popen(command,start_new_session=True,**kwargs) as process:
        try:
            stdout,stderr=process.communicate(timeout=timeout)
            return subprocess.CompletedProcess(command,process.returncode,stdout,stderr)
        except BaseException:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait()
            raise

def install_role(name,r,install=True):
    root=Path(r['root']);prefix=root/'home/role/.local/env'
    marker=prefix/'gewu-preinstalled-v1.json'
    if install and not marker.exists():
        command=['chroot','--userspec='+str(r['uid'])+':'+str(r['gid']),str(root),'/usr/bin/env','-i','HOME=/home/role','TMPDIR=/tmp','PATH=/usr/local/bin:/usr/bin:/bin','MAMBA_ROOT_PREFIX=/home/role/.local/mamba','/usr/local/bin/role-install',*PACKAGES]
        log=W/'.state/universe-maintenance'/('preinstall-'+name+'.log')
        with log.open('w') as out:
            result=run_owned(command,stdout=out,stderr=out,timeout=7200)
        if result.returncode:raise RuntimeError(name+' preinstall failed; inspect private log')
    probe=['chroot','--userspec='+str(r['uid'])+':'+str(r['gid']),str(root),'/usr/bin/env','-i','HOME=/home/role','TMPDIR=/tmp','PATH=/home/role/.local/env/bin:/usr/local/bin:/usr/bin:/bin','LD_LIBRARY_PATH=/home/role/.local/env/lib','/bin/bash','-o','pipefail','-c',
           'set -e; python -c "import numpy,scipy,pandas,sympy,matplotlib,sklearn,netCDF4,astropy,h5py,pytest,requests,yaml,PIL; assert numpy.arange(5).sum()==10"; command -v cmake; command -v make; command -v curl; command -v seq; command -v nohup; printf "#include <iostream>\\nint main(){std::cout << 42;}\\n" > /tmp/gewu-preinstall.cpp; compiler=$(find /home/role/.local/env/bin -maxdepth 1 -name "*-conda-linux-gnu-c++" -print -quit); test -n "$compiler"; "$compiler" /tmp/gewu-preinstall.cpp -o /tmp/gewu-preinstall; test "$(/tmp/gewu-preinstall)" = 42; rm /tmp/gewu-preinstall.cpp /tmp/gewu-preinstall']
    result=run_owned(probe,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=600)
    log=W/'.state/universe-maintenance'/('verify-'+name+'.log')
    log.write_text(result.stdout+'\n'+result.stderr)
    if result.returncode:raise RuntimeError(name+' environment verification failed')
    payload=json.dumps({'packages':PACKAGES,'imports_and_cpp_verified':True},sort_keys=True)+'\n'
    fd,tmp=tempfile.mkstemp(prefix='.gewu-preinstalled-',dir=prefix)
    try:
        with os.fdopen(fd,'w') as f:f.write(payload);f.flush();os.fsync(f.fileno())
        os.chown(tmp,r['uid'],r['gid']);os.chmod(tmp,0o600);os.replace(tmp,marker)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    print(name+' installed and verified',flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--role');parser.add_argument('--verify-only',action='store_true');parser.add_argument('--wait-lock',action='store_true');args=parser.parse_args()
    cfg=json.loads((W/'.state/science-role-broker/config.json').read_text())
    if args.role and args.role not in cfg['roles']:raise ValueError('Unknown role')
    names=[args.role] if args.role else list(cfg['roles'])
    lock_path=W/'.state/universe-maintenance/preinstall.lock'
    lock_path.parent.mkdir(parents=True,exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|(0 if args.wait_lock else fcntl.LOCK_NB))
        for name in names:install_role(name,cfg['roles'][name],install=not args.verify_only)
if __name__=='__main__':main()
