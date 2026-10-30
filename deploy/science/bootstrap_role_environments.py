"""Clone a verified environment into independent same-prefix role roots.

All roles see /home/role/.local/env inside chroot. This preserves that prefix,
never hard-links mutable files across roles, and retains previous environments.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from preinstall_role_runtime import W,install_role,run_owned,PREINSTALL_VERSION
from role_exec import role_processes

def require_stopped(role):
    if role_processes(role['uid']):
        raise ValueError('Refusing to clone or replace an active role environment')

def existing_verified(env):
    return (Path(env)/(PREINSTALL_VERSION+'.json')).is_file()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--donor',default='author-02')
    parser.add_argument('--role',action='append',help='Provision only these configured roles')
    args=parser.parse_args()
    directory=W/'.state/storage-investigation'
    directory.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((W/'.state/science-role-broker/config.json').read_text())
    if args.role and set(args.role)-set(cfg['roles']):raise ValueError('Unknown target role')
    status={'state':'waiting_for_install_lock','roles':{},'started_at':time.time()}
    def save():
        p=directory/'bootstrap-status.pending';p.write_text(json.dumps(status,indent=2)+'\n')
        p.replace(directory/'bootstrap-status.json')
    save()
    with (W/'.state/universe-maintenance/preinstall.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:
            donor=cfg['roles'][args.donor]
            require_stopped(donor)
            install_role(args.donor,donor,install=False)
            archive=directory/'verified-environment.tar'
            pending=archive.with_suffix('.pending')
            pending.touch(mode=0o600,exist_ok=True)
            pending.chmod(0o600)
            status['state']='packing';save()
            source=Path(donor['root'])/'home/role/.local'
            run=run_owned(['tar','--exclude=env/gewu-preinstalled-*.json','-cf',str(pending),'-C',str(source),'env'],timeout=7200)
            if run.returncode:raise RuntimeError('Environment archive failed')
            pending.chmod(0o600);pending.replace(archive)
            digest=hashlib.sha256()
            with archive.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
            status['archive_sha256']=digest.hexdigest();status['state']='deploying';save()
            for name,role in cfg['roles'].items():
                if args.role and name not in args.role:continue
                require_stopped(role)
                root=Path(role['root']);local=root/'home/role/.local';env=local/'env'
                if name==args.donor or existing_verified(env):
                    install_role(name,role,install=False)
                    status['roles'][name]='verified_existing';save();continue
                stage=local/('bootstrap-'+str(time.time_ns()))
                stage.mkdir(mode=0o700);os.chown(stage,role['uid'],role['gid'])
                command=['chroot','--userspec='+str(role['uid'])+':'+str(role['gid']),str(root),
                         '/usr/bin/tar','--no-same-owner','--no-same-permissions','-xf','-',
                         '-C','/home/role/.local/'+stage.name]
                status['roles'][name]='extracting';save()
                with archive.open('rb') as stream:
                    result=run_owned(command,timeout=7200,stdin=stream)
                if result.returncode:raise RuntimeError(name+' archive extraction failed')
                # No file is shared with the donor; GNU tar only links members
                # to other members within this independently extracted archive.
                sample='lib/python3.11/site-packages/numpy/__init__.py'
                before=Path(donor['root'])/'home/role/.local/env'/sample
                after=stage/'env'/sample
                assert (before.stat().st_dev,before.stat().st_ino)!=(after.stat().st_dev,after.stat().st_ino)
                backup=local/('env-before-bootstrap-'+str(time.time_ns()))
                existed=env.exists()
                if existed:env.rename(backup)
                (stage/'env').rename(env)
                try:install_role(name,role,install=False)
                except BaseException:
                    env.rename(local/('env-failed-bootstrap-'+str(time.time_ns())))
                    if existed:backup.rename(env)
                    raise
                stage.rmdir()
                status['roles'][name]='verified_independent_copy';save()
                print(name+' independent environment verified',flush=True)
            status['state']='verified';status['finished_at']=time.time();save()
        except BaseException as error:
            status.update(state='failed',error=str(error),finished_at=time.time());save();raise

if __name__=='__main__':main()
