"""Operator capability probes run as the actual isolated role, without secrets."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from evaluation_queue import W, atomic_json
from install_role_skills import selected

MODULES = ('numpy','scipy','pytest','pydantic','yaml')
TOOLS = ('bash','git','tar','gzip','seq','nohup','curl','role-install','role-forgejo')

PROBE = '''import importlib,json,os,shutil,sys
modules={}
for name in ['numpy','scipy','pytest','pydantic','yaml']:
 try:
  m=importlib.import_module(name);modules[name]={'ok':True,'version':getattr(m,'__version__','unknown')}
 except Exception as e:modules[name]={'ok':False,'error_type':type(e).__name__}
tools={name:shutil.which(name) for name in ['bash','git','tar','gzip','seq','nohup','curl','role-install','role-forgejo']}
print(json.dumps({'python':sys.executable,'uid':os.getuid(),'modules':modules,'tools':tools}))
'''


def inspect(role, entry, runner=subprocess.run):
    root = Path(entry['root']).resolve(strict=True)
    if not root.is_relative_to(W): raise ValueError('Role root outside workspace')
    skills = {}
    for name in selected(role):
        path = root/'skills'/name/'SKILL.md'
        if not path.is_file() or path.is_symlink(): raise ValueError('Missing required skill: '+name)
        skills[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    instruction = root/'instruction.md'
    python = '/home/role/.local/env/bin/python'
    if not (root/python.lstrip('/')).is_file(): raise ValueError('Default scientific environment missing')
    command = ['/usr/bin/setpriv','--no-new-privs','/usr/sbin/chroot',
               '--userspec='+str(entry['uid'])+':'+str(entry['gid']),
               '--groups='+str(entry['gid']),str(root),'/usr/bin/env','-i',
               'HOME=/home/role','PATH=/home/role/.local/bin:/home/role/.local/env/bin:/usr/local/bin:/usr/bin:/bin',
               'LD_LIBRARY_PATH=/home/role/.local/env/lib','PYTHONDONTWRITEBYTECODE=1',python,'-c',PROBE]
    result = runner(command, capture_output=True, text=True, timeout=120)
    if result.returncode: raise ValueError('Isolated capability probe failed; no raw output published')
    observed = json.loads(result.stdout)
    if observed.get('uid') != entry['uid']: raise ValueError('Probe ran under unexpected identity')
    required = ['role-acs-selftest'] if role.startswith('author-') else []
    entrypoints = {name:(root/'usr/local/bin'/name).is_file() for name in required}
    if role.startswith('author-'):
        deployed=root/'usr/local/bin/role-acs-selftest'
        expected=Path(__file__).with_name('role_acs_selftest.py')
        entrypoints['selftest_client_current']=deployed.is_file() and not deployed.is_symlink() and hashlib.sha256(deployed.read_bytes()).digest()==hashlib.sha256(expected.read_bytes()).digest()
    if set(observed.get('modules',{}))!=set(MODULES) or set(observed.get('tools',{}))!=set(TOOLS):
        raise ValueError('Incomplete capability probe response')
    healthy = all(v.get('ok') is True for v in observed['modules'].values()) and all(observed['tools'].values()) and all(entrypoints.values())
    return dict(role=role,observed_at=time.time(),ready=healthy,skills=skills,
                instruction_sha256=hashlib.sha256(instruction.read_bytes()).hexdigest(),
                environment=observed,entrypoints=entrypoints,
                scope='Executable local capability check; cloud queue liveness and model skill use require separate verification')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=W/'.state/science-role-broker/config.json');p.add_argument('--role');p.add_argument('--settings',type=Path,help='Check only roles configured desired=started');args=p.parse_args()
    if os.geteuid()!=0: raise ValueError('Operator required')
    config=json.loads(args.config.read_text());failed=[]
    enabled=None
    if args.settings:
        import tomllib
        settings=tomllib.loads(args.settings.read_text())
        enabled={row['name'] for row in settings['agents'] if row.get('desired')=='started'}
        if enabled-set(config['roles']):raise ValueError('Enabled role absent from broker configuration')
    for role,entry in config['roles'].items():
        if args.role and role!=args.role:continue
        if enabled is not None and role not in enabled:continue
        try:
            receipt=inspect(role,entry)
        except (ValueError,OSError,subprocess.SubprocessError,json.JSONDecodeError) as error:
            receipt=dict(role=role,ready=False,observed_at=time.time(),error_type=type(error).__name__,
                         reason='Capability probe did not complete; inspect operator evidence before scheduling')
        path=Path(entry['root'])/'capabilities.json';atomic_json(path,receipt,0o644)
        print(json.dumps(dict(role=role,ready=receipt['ready'],skills=list(receipt.get('skills',{})))))
        if not receipt['ready']:failed.append(role)
    if args.role and args.role not in config['roles']:raise ValueError('Unknown role')
    if failed:raise SystemExit('Capability checks failed for: '+','.join(failed))


if __name__=='__main__':main()
