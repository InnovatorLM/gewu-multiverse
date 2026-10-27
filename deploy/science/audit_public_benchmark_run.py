"""Private post-run audit; outputs metadata only, never secret values or prompts."""
import argparse,base64,collections,json,os,pathlib,shlex
import yaml
W=pathlib.Path('/mnt/data/zhanglinfeng/workspace')
p=argparse.ArgumentParser();p.add_argument('--run-dir',required=True);p.add_argument('--guard-report',required=True);p.add_argument('--out',required=True);args=p.parse_args()
run=pathlib.Path(args.run_dir).resolve();run.relative_to(W/'.state/private-science-runs')
job=json.loads((run/'result.json').read_text())
if not job.get('finished_at'):raise SystemExit('Live run; final audit refused')
guard=json.loads(pathlib.Path(args.guard_report).read_text())
if guard.get('run_id')!=run.name:raise SystemExit('Guard report identity mismatch')
configuration=json.loads((run/'config.json').read_text())
agent=configuration.get('agents',[{}])[0]
expected_model='openai/deepseek-v4.1-flash-1017'
expected_base='https://dawnfm.gravarc.cn/v1'
provider_binding=(agent.get('model_name')==expected_model and
                  agent.get('env',{}).get('LLM_PROVIDER')=='dawnfm' and
                  agent.get('env',{}).get('OPENAI_BASE_URL')==expected_base)
secrets={}
if os.environ.get('OPENAI_API_KEY'):secrets['dawnfm_api_key']=os.environ['OPENAI_API_KEY'].encode()
else:raise SystemExit('Load designated DawnFM env before exact-secret audit')
envfile=W/'.config/acr/dptech-sh-pai-acr.env'
for line in envfile.read_text().splitlines():
 line=line.strip().removeprefix('export ')
 if '=' not in line or line.startswith('#'):continue
 name,value=line.split('=',1)
 if any(word in name.upper() for word in ('PASSWORD','TOKEN','SECRET')):
  parts=shlex.split(value)
  if len(parts)==1 and len(parts[0])>=8:secrets['acr_'+name]=parts[0].encode()
kube=yaml.safe_load((W/'.config/acs/kubeconfig').read_text())
for index,item in enumerate(kube.get('users',[])):
 for name,value in item.get('user',{}).items():
  if name in ('token','client-key-data') and isinstance(value,str):secrets['kube_'+str(index)+'_'+name]=value.encode()
docker=json.loads((W/'.config/docker-shanghai/config.json').read_text())
for index,value in enumerate(docker.get('auths',{}).values()):
 if value.get('auth'):
  secrets['docker_auth_'+str(index)]=value['auth'].encode()
  decoded=base64.b64decode(value['auth'])
  if b':' in decoded:secrets['docker_password_'+str(index)]=decoded.split(b':',1)[1]
needles={}
for label,value in secrets.items():
 if len(value)>=8:
  needles[label]=value;needles[label+'_base64']=base64.b64encode(value)
findings=[];file_count=0
for path in run.rglob('*'):
 if path.is_symlink():raise SystemExit('Unexpected symlink in private run')
 if path.is_dir():path.chmod(0o700);continue
 if not path.is_file():raise SystemExit('Unexpected special file in private run')
 path.chmod(0o600);data=path.read_bytes();file_count+=1
 matches=[name for name,value in needles.items() if value in data]
 if matches:findings.append({'file':path.relative_to(run).as_posix(),'secret_labels':matches})
run.chmod(0o700)
trials=[]
for result in run.glob('*/result.json'):
 d=json.loads(result.read_text());folder=result.parent
 required=['trial.log','agent/mini-swe-agent.trajectory.json','verifier/reward.txt','verifier/test-stdout.txt','verifier/ctrf.json']
 trajectory=folder/'agent/mini-swe-agent.trajectory.json';roles={};metrics={};model_binding=False
 if trajectory.exists():
  trace=json.loads(trajectory.read_text());messages=trace.get('messages',[]) if isinstance(trace,dict) else []
  roles=dict(collections.Counter(m.get('role','unknown') for m in messages))
  metrics={'api_calls':trace.get('info',{}).get('model_stats',{}).get('api_calls'),'tool_calls_requested':sum(len(m.get('tool_calls') or []) for m in messages),'tool_result_messages':sum(m.get('role')=='tool' for m in messages)}
  model_config=trace.get('info',{}).get('config',{}).get('model',{})
  model_binding=model_config.get('model_name')==expected_model and model_config.get('model_kwargs',{}).get('api_base')==expected_base
 ctrf=folder/'verifier/ctrf.json';test_summary=None
 if ctrf.exists():test_summary=json.loads(ctrf.read_text()).get('results',{}).get('summary')
 trials.append({'trial':folder.name,'finished_at':d.get('finished_at'),'exception_type':(d.get('exception_info') or {}).get('exception_type'),'rewards':(d.get('verifier_result') or {}).get('rewards'),'missing_evidence':[name for name in required if not (folder/name).is_file()],'trajectory_role_counts':roles,'model_and_tool_metrics':metrics,'trajectory_model_binding_verified':model_binding,'test_summary':test_summary})
stats=job.get('stats',{});r={'run_id':run.name,'finished_at':job['finished_at'],'n_completed_trials':stats.get('n_completed_trials'),'n_errored_trials':stats.get('n_errored_trials'),'token_usage':{key:stats.get(key) for key in ('n_input_tokens','n_output_tokens','n_cache_tokens')},'trials':trials,'exact_secret_scan':{'files_scanned':file_count,'secret_encodings_checked':len(needles),'findings':findings},'private_file_permissions_enforced':True,'cleanup_confirmed':guard.get('cleanup',{}).get('confirmed') is True,'execution_scope':'bounded procedural validation; not full-budget difficulty calibration','scientific_acceptance':False}
r['provider_binding_verified']=provider_binding
r['procedural_chain_passed']=bool(trials) and stats.get('n_completed_trials')==1 and stats.get('n_errored_trials')==0 and r['cleanup_confirmed'] and not findings and provider_binding and all(not t['exception_type'] and not t['missing_evidence'] and t['rewards'] is not None and t['trajectory_model_binding_verified'] and (t['model_and_tool_metrics'].get('api_calls') or 0)>0 and (t['test_summary'] or {}).get('tests',0)>0 for t in trials)
out=pathlib.Path(args.out);out.write_text(json.dumps(r,indent=2)+'\n');out.chmod(0o600)
print(json.dumps(r,indent=2))
