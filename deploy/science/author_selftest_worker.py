"""Operator-owned author selftest queue: frozen upload -> ACR -> ACS oracle/nop."""
import json,os,re,subprocess,tarfile,hashlib,time,fcntl
from pathlib import Path,PurePosixPath
from evaluation_queue import W,atomic_json
from check_harbor_task import inspect_task
from selftest_lifecycle import owned_run, recover_interrupted, install_stop_handlers
from build_task_images import validate_dockerfile
STATE=W/'.state/science-author-selftest'
PYTHON=W/'acs-harbor-test/.venv/bin/python'
BASE='public.ecr.aws/docker/library/python@sha256:b7a9e5f6a93d6d4a31f129bbd4bdee69efccb6ded0fb230d78aafaf37af98377'
def unpack(archive,destination):
 with tarfile.open(archive) as t:
  members=t.getmembers()
  if len(members)>10000 or sum(m.size for m in members)>128*1024*1024:raise ValueError('Archive too large')
  for m in members:
   p=PurePosixPath(m.name)
   if p.is_absolute() or '..' in p.parts or not(m.isfile() or m.isdir()):raise ValueError('Unsafe task archive')
  destination.mkdir(parents=True)
  for m in members:
   p=destination/m.name
   if m.isdir():p.mkdir(parents=True,exist_ok=True)
   else:
    p.parent.mkdir(parents=True,exist_ok=True)
    with t.extractfile(m) as src,p.open('xb') as out:__import__('shutil').copyfileobj(src,out)
    p.chmod(0o700 if m.mode&0o111 else 0o600)
def process(role,entry,request):
 job=request.stem
 if not re.fullmatch('[a-f0-9]{32}',job):return
 root=Path(entry['root']);result=root/'selftest/results'/(job+'.json');work=STATE/job
 def publish(payload):
  atomic_json(result,payload);os.chown(result,0,entry['gid']);result.chmod(0o640)
 if recover_interrupted(work,result,publish):return
 work.mkdir(mode=0o700);status={'job_id':job,'role':role,'status':'validating','quality_acceptance':False}
 def save():
  status['updated_at']=time.time();publish(status);atomic_json(work/'status.json',status)
 save()
 try:
  if request.is_symlink() or request.stat().st_uid!=entry['uid'] or request.stat().st_size>16384:raise ValueError('Invalid request owner/size')
  q=json.loads(request.read_text());name=q['task_name'];archive=request.with_suffix('.tar')
  if q['job_id']!=job or not re.fullmatch('[a-z0-9][a-z0-9._-]{0,90}',name) or not re.fullmatch('[a-f0-9]{40}',q['source_commit']):raise ValueError('Invalid request identity')
  if archive.is_symlink() or archive.stat().st_uid!=entry['uid'] or archive.stat().st_size>140*1024*1024:raise ValueError('Invalid archive')
  frozen=work/'upload.tar';__import__('shutil').copyfile(archive,frozen)
  if hashlib.sha256(frozen.read_bytes()).hexdigest()!=q['archive_sha256']:raise ValueError('Upload changed')
  repo=work/'source';task=repo/name;unpack(frozen,task);atomic_json(work/'mechanical.json',inspect_task(task))
  for dockerfile in [task/'environment/Dockerfile',task/'tests/Dockerfile']:
   if dockerfile.is_file():
    validate_dockerfile(dockerfile,BASE)
  for args in [['init','-q'],['config','user.email','operator@localhost'],['config','user.name','operator'],['add','.'],['commit','-qm','Frozen author upload']]:subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True)
  commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip();status.update(status='building',source_commit=q['source_commit']);save()
  env=os.environ.copy();env.update(TMPDIR=str(W/'.tmp'),PYTHONDONTWRITEBYTECODE='1',HOME=str(W/'.state/harbor-home'))
  with (work/'build.log').open('w') as log:
   r=owned_run([str(PYTHON),str(Path(__file__).with_name('build_task_images.py')),'--repo',str(repo),'--commit',commit,'--task-path',name,'--output',str(work/'build'),'--python-base',BASE,'--harness','mini-swe-agent','--publish'],env=env,stdout=log,stderr=log,timeout=3600)
  if r.returncode:raise RuntimeError('Image build failed; operator evidence: '+str(work/'build.log'))
  images=json.loads((work/'build/receipt.json').read_text())['images'];status['images']={k:v['published_digest'] for k,v in images.items()};status['trials']=[]
  for agent in ['oracle','nop']:
   status['status']='running_'+agent;save();c=json.loads((W/'.config/harbor-api/template.json').read_text());run='tbs-universe-linfeng-selftest-'+job[:12]+'-'+agent
   c.update(job_name=run,jobs_dir=str(work/'runs'),n_attempts=1,n_concurrent_trials=1,datasets=[{'path':str(repo),'task_names':[name]}],agents=[{'name':agent,'override_timeout_sec':14400}]);c['retry']={'max_retries':0};c['environment']['delete']=True;c['environment']['import_path']=None;c['environment']['override_cpus']=4;c['environment']['override_memory_mb']=8192
   kw=c['environment']['kwargs'];kw.update(use_sandbox_claim=False,runtime_image=images['official']['published_digest'],verifier_image=images['verifier']['published_digest']);kw.pop('verifier_image_manifest',None)
   spec=kw['pod_overrides']['spec'];spec.update(nodeName='virtual-kubelet-cn-beijing-i',activeDeadlineSeconds=14400);kw['pod_overrides'].setdefault('metadata',{}).setdefault('labels',{})['evaluation-run']=run
   for container in spec['containers']:
    container['image']=images['official']['published_digest']
    for k in ['requests','limits']:container['resources'][k].update(cpu='4',memory='8Gi')
   cfg=work/(agent+'.json');atomic_json(cfg,c);report=work/(agent+'-report.json')
   with (work/(agent+'.log')).open('w') as log:r=owned_run([str(Path(__file__).with_name('run-acs-evaluation')),str(cfg),str(report)],env=env,stdout=log,stderr=log,timeout=15000)
   d=json.loads(report.read_text()) if report.exists() else {};trials=[]
   if d.get('result_path'):
    for f in Path(d['result_path']).parent.glob('*/result.json'):
     t=json.loads(f.read_text());trials.append({'rewards':(t.get('verifier_result') or {}).get('rewards'),'exception_type':(t.get('exception_info') or {}).get('exception_type')})
   status['trials'].append({'agent':agent,'exit_code':r.returncode,'cleanup_confirmed':d.get('cleanup',{}).get('confirmed',False),'results':trials});save()
  def valid(t,reward):return t['exit_code']==0 and t['cleanup_confirmed'] and len(t['results'])==1 and not t['results'][0]['exception_type'] and (t['results'][0]['rewards'] or {}).get('reward')==reward
  status['status']='selftest_passed' if valid(status['trials'][0],1) and valid(status['trials'][1],0) else 'selftest_failed'
  status['note']='Author selftest only; iteration/rerun and independent evaluation still required.'
 except KeyboardInterrupt:
  status.update(status='interrupted',error='Worker stopped; inspect preserved logs and cloud cleanup.');save();raise
 except Exception as e:status.update(status='failed',error=str(e)[:600])
 save()
def main():
 install_stop_handlers()
 STATE.mkdir(mode=0o700,parents=True,exist_ok=True)
 with (STATE/'worker.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while True:
   roles=json.loads((W/'.state/science-role-broker/config.json').read_text())['roles']
   for role,entry in roles.items():
    if role.startswith('author-'):
     for q in sorted((Path(entry['root'])/'selftest/inbox').glob('*.json')):process(role,entry,q)
   time.sleep(10)
if __name__=='__main__':main()
