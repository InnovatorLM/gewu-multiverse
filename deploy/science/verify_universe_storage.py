"""Operator-only, credential-free persistence checks in actual Universe roots.

Runs separate write/read processes as each configured role UID. It never starts
the scheduler or cleans a role's processes, so a live installation is unaffected.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

W=Path('/mnt/data/zhanglinfeng/workspace')

def main():
    if os.geteuid()!=0:raise SystemExit('Operator UID required')
    cfg=json.loads((W/'.state/science-role-broker/config.json').read_text())
    identifier='storage-validation-'+uuid.uuid4().hex
    results=[]
    identities={}
    for name,role in cfg['roles'].items():
        root=Path(role['root'])
        directory=root/'home/role/.state'/identifier
        payload=hashlib.sha256((identifier+name).encode()).hexdigest()
        prefix=['chroot','--userspec='+str(role['uid'])+':'+str(role['gid']),str(root),
                '/usr/bin/env','-i','HOME=/home/role','TMPDIR=/tmp',
                'PATH=/usr/local/bin:/usr/bin:/bin','/usr/local/bin/python3','-c']
        relative='/home/role/.state/'+identifier
        write=("import os; from pathlib import Path; p=Path("+repr(relative)+
               "); p.mkdir(parents=True,mode=0o700); f=(p/'pending').open('w'); "
               "f.write("+repr(payload)+"); f.flush(); os.fsync(f.fileno()); "
               "f.close(); (p/'pending').rename(p/'committed')")
        read=("from pathlib import Path; assert (Path("+repr(relative)+
              ")/'committed').read_text()=="+repr(payload))
        started=time.monotonic()
        for program in (write,read):
            result=subprocess.run(prefix+[program],capture_output=True,text=True,timeout=120)
            if result.returncode:raise RuntimeError(name+' persistence check failed: '+result.stderr[-500:])
        info=directory.stat()
        assert info.st_uid==role['uid'] and info.st_mode&0o777==0o700
        identities[name]=(info.st_dev,info.st_ino)
        results.append({'role':name,'uid':role['uid'],'write_fsync_rename':True,
                        'fresh_process_read':True,'private_directory':True,
                        'seconds':round(time.monotonic()-started,3)})
    assert len(set(identities.values()))==len(identities)
    names=list(cfg['roles'])
    for index,name in enumerate(names):
        role=cfg['roles'][name]
        peer=Path(cfg['roles'][names[(index+1)%len(names)]]['root'])/'home/role/.state'/identifier/'committed'
        code='import os; assert not os.access('+repr(str(peer))+',os.R_OK)'
        result=subprocess.run(['setpriv','--reuid='+str(role['uid']),'--regid='+str(role['gid']),
                               '--clear-groups','/usr/local/bin/python3','-c',code],
                               capture_output=True,text=True,timeout=30)
        assert result.returncode==0,(name,result.stderr)
        results[index]['peer_read_denied']=True
    report={'passed':True,'checked_at':time.time(),'validation_id':identifier,
            'scope':'Actual Universe role UIDs/chroots; separate processes; no model or scheduler',
            'roles':results,'distinct_storage_directories':True}
    output=W/'.state/storage-investigation/universe-persistence.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
