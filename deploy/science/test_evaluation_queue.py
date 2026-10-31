import importlib.util,json,os,socket,subprocess,sys,time,uuid
from pathlib import Path
w=Path('/mnt/data/zhanglinfeng/workspace');module_path=w/'gewu-multiverse/deploy/science/evaluation_queue.py';spec=importlib.util.spec_from_file_location('queue',module_path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
config=json.loads((w/'.config/science-evaluation/queue.json').read_text());state=w/('.state/science-evaluation-queue-mock-test-'+str(time.time_ns()));state.mkdir(mode=0o700,exist_ok=True);config['state']=str(state);config['max_jobs_per_day']=3;config.update(config['role_queues'][0]);evaluator_role=config['role'];evaluator_uid=config['evaluator_uid']
broker_config=w/'.state/science-role-broker/config.json';broker_data=json.loads(broker_config.read_text());broker=subprocess.Popen([sys.executable,str(module_path.with_name('role_exec.py')),str(broker_config)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 deadline=time.monotonic()+20
 while True:
  try:
   with socket.socket(socket.AF_UNIX) as probe:probe.connect('\0'+broker_data['socket'][1:])
   break
  except ConnectionRefusedError:
   if broker.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Broker did not start')
   time.sleep(.1)
 def command(role,code):
  with socket.socket(socket.AF_UNIX) as s:
   s.connect('\0'+broker_data['socket'][1:]);s.sendall(json.dumps({'role':role,'cwd':'/workspace','argv':['python3','-c',code],'timeout':20}).encode()+b'\n');return json.loads(s.makefile().readline())
 code="import json,uuid,os;from pathlib import Path;c=json.load(open('/evaluation/catalog.json'))['evaluations'][0];j=uuid.uuid4().hex;p=Path('/evaluation/inbox')/(j+'.json');p.write_text(json.dumps(dict(job_id=j,evaluation_id=c['evaluation_id'],snapshot_sha256=c['snapshot_sha256'])));p.chmod(0o600);print(j)"
 response=command(evaluator_role,code);assert response['returncode']==0 and response['cleanup_confirmed'];jobid=response['stdout'].strip();answer=m.process(config,Path(config['inbox'])/(jobid+'.json'),mock=True);assert answer['status']=='mock_complete' and not answer['quality_acceptance']
 response=command(evaluator_role,"import json;print(json.load(open('/evaluation/results/"+jobid+".json'))['status']);assert not __import__('os').environ.get('OPENAI_API_KEY')");assert response['returncode']==0 and 'mock_complete' in response['stdout']
 for role in ['author-02','curator']:
  response=command(role,"open('/evaluation/catalog.json')");assert response['returncode']!=0
 report={'real_evaluator_submission_and_result_read':True,'author_curator_queue_unavailable':True,'no_provider_key_in_role_env':True,'mock_model_calls':0,'quality_acceptance':False}
 registry=json.loads(Path(config['registry']).read_text());entry=registry['calibration-v1']
 def request(uid=evaluator_uid,**extra):
  j=uuid.uuid4().hex;p=Path(config['inbox'])/(j+'.json');p.write_text(json.dumps(dict(job_id=j,evaluation_id='calibration-v1',snapshot_sha256=entry['snapshot_sha256'],**extra)));os.chown(p,uid,uid);p.chmod(0o600);return p
 for label,uid,extra in [('foreign_uid_refused',21001,{}),('command_injection_field_refused',evaluator_uid,{'argv':['id']}),('model_override_refused',evaluator_uid,{'model':'another-model'})]:
  p=request(uid,**extra)
  try:m.process(config,p,mock=True);raise AssertionError(label)
  except ValueError:report[label]=True
  p.unlink()
 p=request();d=json.loads(p.read_text());d['snapshot_sha256']='0'*64;p.write_text(json.dumps(d))
 try:m.process(config,p,mock=True);raise AssertionError('stale snapshot')
 except ValueError:report['snapshot_mismatch_refused']=True
 p.unlink()
 p=Path(config['inbox'])/(uuid.uuid4().hex+'.json');p.symlink_to('/home/role/git-credential.json')
 try:m.read_request(p,evaluator_uid);raise AssertionError('symlink')
 except OSError:report['request_symlink_refused']=True
 p.unlink()
 for _ in range(2):
  p=request();assert m.process(config,p,mock=True)['status']=='mock_complete'
 p=request()
 try:m.process(config,p,mock=True);raise AssertionError('budget')
 except ValueError:report['durable_daily_budget_enforced']=True
 p.unlink()
 # A template change cannot be smuggled through an operator-registered ID.
 original_registry=config['registry'];clone=json.loads(Path(original_registry).read_text());template=state/'changed-template.json';template.write_bytes(Path(entry['template']).read_bytes()+b' ');template.chmod(0o600);clone['calibration-v1']['template']=str(template);registry_path=state/'registry-copy.json';registry_path.write_text(json.dumps(clone));registry_path.chmod(0o600);config['registry']=str(registry_path)
 p=request()
 try:m.process(config,p,mock=True);raise AssertionError('template change')
 except ValueError as error:assert 'template changed' in str(error);report['template_mutation_refused']=True
 p.unlink();config['registry']=original_registry
 # Cleanup uncertainty blocks further dispatch even when money/turn budget remains.
 config['max_jobs_per_day']=10
 retained=next(state.glob('*/result.json'));prior=json.loads(retained.read_text());prior['cleanup_confirmed']=False;retained.write_text(json.dumps(prior));p=request()
 try:m.process(config,p,mock=True);raise AssertionError('unconfirmed cleanup')
 except ValueError as error:assert 'cleanup is not confirmed' in str(error);report['unconfirmed_cleanup_blocks_new_jobs']=True
 p.unlink()
 (w/'.state/harbor-eval/evaluation-queue-mock.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
finally:
 broker.terminate();broker.wait(timeout=10)
