#!/usr/bin/env python3
"""Source-bound operator controller for ACS unified quality; integration in progress."""
import argparse,datetime,hashlib,json,os,pathlib,signal,subprocess,sys,tarfile,time,uuid
from kubernetes import client,config
from kubernetes.stream import stream
from kubernetes.client.exceptions import ApiException

W=pathlib.Path('/mnt/data/zhanglinfeng/workspace')
def pipeline_digest():
 entries=[]
 base=W/'repos/unified-evaluator-pipeline/unified_evaluator'
 for path in sorted(base.rglob('*')):
  if '__pycache__' in path.parts or path.suffix=='.pyc':continue
  if path.is_symlink():raise ValueError('Pipeline links refused')
  if path.is_file():entries.append((path.relative_to(base).as_posix(),hashlib.sha256(path.read_bytes()).hexdigest()))
 return hashlib.sha256(json.dumps(entries).encode()).hexdigest()

def load_settings(path):
 sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
 from evaluation_queue import root_file,digest_tree
 settings=json.loads(root_file(path).read_text())
 required={'task','task_sha256','runtime_image','codex_binary','codex_sha256','bundled_bwrap','bwrap_sha256','boundary_receipt','worker_sha256','pipeline_sha256'}
 if set(settings)!=required:raise ValueError('Require exact operator ACS quality settings')
 if pipeline_digest()!=settings['pipeline_sha256']:raise ValueError('Unified pipeline changed')
 task=pathlib.Path(settings['task'])
 if not task.resolve().is_relative_to(W) or digest_tree(task)!=settings['task_sha256']:raise ValueError('Task source changed')
 import re
 if not re.fullmatch(r'dptech-sh-pai-acr-registry\.cn-shanghai\.cr\.aliyuncs\.com/terminal-bench-universe/[a-z0-9._/-]+@sha256:[a-f0-9]{64}',settings['runtime_image']):raise ValueError('Require digest-pinned project image')
 for key,hashkey in [('codex_binary','codex_sha256'),('bundled_bwrap','bwrap_sha256')]:
  p=root_file(settings[key])
  if hashlib.sha256(p.read_bytes()).hexdigest()!=settings[hashkey]:raise ValueError('Runtime changed: '+key)
 worker=pathlib.Path(__file__).with_name('acs_quality_worker.py')
 if hashlib.sha256(root_file(worker).read_bytes()).hexdigest()!=settings['worker_sha256']:raise ValueError('Worker changed')
 receipt=json.loads(root_file(settings['boundary_receipt']).read_text())
 if receipt.get('cleanup',{}).get('confirmed') is not True or not any(x.get('boundary_passed') is True for x in receipt.get('tool_probe',[])):raise ValueError('Boundary smoke missing')
 if receipt.get('binary_sha256')!=settings['codex_sha256'] or receipt.get('image')!=settings['runtime_image']:raise ValueError('Boundary smoke runtime differs')
 return settings,task

def cleanup_owned(api, custom, run, expected_uid=None):
 """Reconcile one exact run; preserve unknown status instead of losing report."""
 errors=[];gone=False;checks=[]
 try:
  pod=api.read_namespaced_pod(run,'default',_request_timeout=15)
  labels=pod.metadata.labels or {}
  if labels.get('evaluation-run')!=run or (expected_uid is not None and pod.metadata.uid!=expected_uid):
   raise ValueError('Cleanup ownership mismatch')
  api.delete_namespaced_pod(run,'default',grace_period_seconds=0,_request_timeout=20)
 except ApiException as exc:
  if exc.status==404:gone=True
  else:errors.append({'phase':'delete','error_type':'ApiException','status':exc.status})
 except Exception as exc:errors.append({'phase':'delete','error_type':type(exc).__name__})
 if not errors and not gone:
  for _ in range(45):
   try:api.read_namespaced_pod(run,'default',_request_timeout=15)
   except ApiException as exc:
    if exc.status==404:gone=True;break
    errors.append({'phase':'known-pod','error_type':'ApiException','status':exc.status});break
   except Exception as exc:
    errors.append({'phase':'known-pod','error_type':type(exc).__name__});break
   time.sleep(1)
 for i in range(2):
  snapshot={}
  try:
   snapshot['pods']=[p.metadata.name for p in api.list_namespaced_pod('default',label_selector='evaluation-run='+run,_request_timeout=20).items]
   for kind in ['sandboxsets','sandboxclaims','sandboxes']:
    snapshot[kind]=[x['metadata']['name'] for x in custom.list_namespaced_custom_object('agents.kruise.io','v1alpha1','default',kind,label_selector='evaluation-run='+run,_request_timeout=20)['items']]
  except ApiException as exc:errors.append({'phase':'snapshot','error_type':'ApiException','status':exc.status})
  except Exception as exc:errors.append({'phase':'snapshot','error_type':type(exc).__name__})
  checks.append(snapshot)
  if i==0:time.sleep(2)
 kinds={'pods','sandboxsets','sandboxclaims','sandboxes'}
 return {'known_pod_404':gone,'two_snapshots':checks,'errors':errors,
         'confirmed':gone and not errors and all(set(s)==kinds and all(not v for v in s.values()) for s in checks)}

def main():
 parser=argparse.ArgumentParser(description='Operator-only ACS quality controller; role supplies only registered IDs through its dispatcher.')
 parser.add_argument('--settings',required=True,type=pathlib.Path)
 parser.add_argument('--validate-only',action='store_true')
 args=parser.parse_args()
 settings,task=load_settings(args.settings)
 if args.validate_only:
  print(json.dumps({'settings_valid':True,'model_calls':0,'cloud_resources_created':0}));return

 if os.geteuid()!=0:raise ValueError('Operator/root controller required')
 if os.environ.get('LLM_PROVIDER')!='dawnfm' or os.environ.get('OPENAI_MODEL')!='deepseek-v4.1-flash-1017' or os.environ.get('OPENAI_BASE_URL')!='https://dawnfm.gravarc.cn/v1' or not os.environ.get('OPENAI_API_KEY'):raise ValueError('Designated provider environment required')
 out=W/'.state/harbor-eval/unified-harness-integration'; run='qa-live-'+uuid.uuid4().hex[:10]; work=W/'.tmp'/run;work.mkdir(mode=0o700);config.load_kube_config(str(W/'.config/acs/kubeconfig'));api=client.CoreV1Api();custom=client.CustomObjectsApi();image=settings['runtime_image'];r={'run_id':run,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'image':image,'model_calls':'pending_actual_trace'};created=False
 sys.path.insert(0,str(W/'repos/unified-evaluator-pipeline'))
 from unified_evaluator.runtime.core import agent_config
 remote=W/'.state'/run
 source=pathlib.Path(settings['codex_binary'])
 (work/'config.toml').write_text(agent_config(remote/'task',{'model_provider':'dawnfm','model_providers':{'dawnfm':{'name':'dawnfm','base_url':'https://dawnfm.gravarc.cn/v1','wire_api':'responses','env_key':'OPENAI_API_KEY'}}},'deepseek-v4.1-flash-1017',remote/'runtime/bin/codex',remote/'scratch'))
 archive=work/'runtime.tar.gz'
 with tarfile.open(archive,'w:gz',compresslevel=1) as tf:
  tf.add(pathlib.Path(settings['bundled_bwrap']),arcname='runtime/codex-resources/bwrap')
  for name in ['libselinux.so.1','libcap.so.2','libpcre2-8.so.0']:
   tf.add(pathlib.Path('/lib/x86_64-linux-gnu',name).resolve(),arcname='runtime/codex-resources/lib/'+name)
  tf.add(source,arcname='runtime/bin/codex');tf.add(work/'config.toml',arcname='config.toml')
  tf.add(W/'gewu-multiverse/deploy/science/acs_quality_worker.py',arcname='live-review.py')
  tf.add(task,arcname='tasks/'+task.name)
  tf.add(W/'repos/unified-evaluator-pipeline/unified_evaluator',arcname='source/unified_evaluator',filter=lambda i:None if '__pycache__' in i.name or i.name.endswith('.pyc') else i)
  tf.add(W/'acs-harbor-test/.venv/lib/python3.12/site-packages/yaml',arcname='source/yaml',filter=lambda i:None if '__pycache__' in i.name or i.name.endswith(('.pyc','.so')) else i)
 r['worker_sha256']=hashlib.sha256((W/'gewu-multiverse/deploy/science/acs_quality_worker.py').read_bytes()).hexdigest();r['binary_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();r['archive_bytes']=archive.stat().st_size
 records=[]
 with tarfile.open(archive) as packed:
  for item in packed:
   if item.isfile():records.append({'path':item.name,'bytes':item.size,'sha256':hashlib.sha256(packed.extractfile(item).read()).hexdigest()})
 manifest={'run_id':run,'task':task.name,'files':records,'settings_sha256':hashlib.sha256(args.settings.read_bytes()).hexdigest(),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'worker_sha256':settings['worker_sha256'],'scientific_acceptance':False}
 manifest_path=out/('quality-live-input-manifest-'+run+'.json');manifest_path.write_text(json.dumps(manifest,indent=2)+'\n');manifest_path.chmod(0o600)
 load_settings(args.settings) # Recheck sources after packaging, before cloud mutation.
 print(json.dumps({'phase':'archive_ready','run_id':run,'bytes':r['archive_bytes']}),flush=True)
 def ex(command,timeout=45):return stream(api.connect_get_namespaced_pod_exec,run,'default',command=command,stdout=True,stderr=True,stdin=False,tty=False,_request_timeout=timeout)
 def stop(_sig,_frame):
  r['cancelled']=True
  raise SystemExit('ACS quality controller cancelled; deleting owned Pod')
 signal.signal(signal.SIGTERM,stop)
 signal.signal(signal.SIGINT,stop)
 try:
  body={'apiVersion':'v1','kind':'Pod','metadata':{'name':run,'labels':{'evaluation-run':run,'alibabacloud.com/acs':'true'}},'spec':{'restartPolicy':'Never','activeDeadlineSeconds':2100,'automountServiceAccountToken':False,'imagePullSecrets':[{'name':'acr-shanghai-universe-trial'}],'containers':[{'name':'main','image':image,'command':['sleep','2100'],'resources':{'requests':{'cpu':'2','memory':'4Gi','ephemeral-storage':'30Gi'},'limits':{'cpu':'2','memory':'4Gi','ephemeral-storage':'30Gi'}},'securityContext':{'allowPrivilegeEscalation':False}}]}}
  pod=api.create_namespaced_pod('default',body,_request_timeout=20);created=True;r['pod_uid']=pod.metadata.uid
  for _ in range(90):
   pod=api.read_namespaced_pod(run,'default',_request_timeout=15)
   if pod.status.phase=='Running':break
   if pod.status.phase in ['Failed','Succeeded']:raise RuntimeError('Pod terminal before exec')
   time.sleep(1)
  else:raise RuntimeError('Pod readiness deadline')
  r['node_region']=api.read_node(pod.spec.node_name,_request_timeout=15).metadata.labels.get('topology.kubernetes.io/region')
  ex(['mkdir','-p',str(remote)])
  cmd=[str(W/'.local/bin/kubectl'),'--kubeconfig',str(W/'.config/acs/kubeconfig'),'exec','-i','-n','default',run,'--','tar','-xzf','-','-C',str(remote)]
  with archive.open('rb') as f:
   result=subprocess.run(cmd,stdin=f,capture_output=True,timeout=150)
  if result.returncode:raise RuntimeError('Upload failed')
  print(json.dumps({'phase':'uploaded','run_id':run}),flush=True)
  # Launch only after an independently recorded zero-model boundary smoke.
  smoke=json.loads(pathlib.Path(settings['boundary_receipt']).read_text())
  assert smoke['cleanup']['confirmed'] and any(x.get('boundary_passed') for x in smoke['tool_probe'])
  r['boundary_smoke_run']=smoke['run_id']
  key=os.environ['OPENAI_API_KEY'];assert os.environ['LLM_PROVIDER']=='dawnfm' and os.environ['OPENAI_MODEL']=='deepseek-v4.1-flash-1017' and os.environ['OPENAI_BASE_URL']=='https://dawnfm.gravarc.cn/v1'
  command=[str(W/'.local/bin/kubectl'),'--kubeconfig',str(W/'.config/acs/kubeconfig'),'exec','-i','-n','default',run,'--','python3','-I',str(remote/'live-review.py'),'--root',str(remote),'--task-name',task.name]
  result=subprocess.run(command,input=key.encode(),capture_output=True,timeout=1900)
  r['controller_exit_code']=result.returncode
  r['remote_stdout']=result.stdout.decode(errors='replace').replace(key,'[REDACTED]')[-3000:]
  r['remote_stderr']=result.stderr.decode(errors='replace').replace(key,'[REDACTED]')[-3000:]
  print(json.dumps({'phase':'review_finished','run_id':run,'controller_exit_code':result.returncode}),flush=True)
  target=out/run;target.mkdir(mode=0o700)
  command=[str(W/'.local/bin/kubectl'),'--kubeconfig',str(W/'.config/acs/kubeconfig'),'exec','-n','default',run,'--','tar','-czf','-','-C',str(remote),'result.json','driver.log','output','logs','active']
  collected=subprocess.run(command,capture_output=True,timeout=60)
  if collected.returncode:raise RuntimeError('Result collection failed')
  artifact=target/'private-evidence.tar.gz';artifact.write_bytes(collected.stdout);artifact.chmod(0o600)
  with tarfile.open(artifact,'r:gz') as tf:tf.extractall(target,filter='data')
  for path in target.rglob('*'):path.chmod(0o700 if path.is_dir() else 0o600)
  r['result']=json.loads((target/'result.json').read_text())
  r['evidence_dir']=str(target)
  if (target/'output/review.json').is_file():
   review=json.loads((target/'output/review.json').read_text());r['review_summary']={'gate':review['gate'],'quality_score':review['quality_score'],'metadata':review['review_metadata']}

 except Exception as exc:r['error_type']=type(exc).__name__;r['error_message']=str(exc)[:300] if not isinstance(exc,ApiException) else str(exc.status)
 finally:
  # A second signal must not interrupt the bounded release/reconciliation pass.
  signal.signal(signal.SIGTERM,signal.SIG_IGN)
  signal.signal(signal.SIGINT,signal.SIG_IGN)
  r['cleanup']=cleanup_owned(api,custom,run,r.get('pod_uid'))
  p=out/('acs-quality-live-'+run+'.json');p.write_text(json.dumps(r,indent=2)+'\n');p.chmod(0o600)
  print(json.dumps(r),flush=True)
  if not r['cleanup']['confirmed']:raise RuntimeError('ACS resource cleanup unconfirmed; do not start another run')

if __name__=='__main__':
 main()
