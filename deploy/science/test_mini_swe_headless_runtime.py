import subprocess,json,pathlib,argparse
from mini_swe_headless import configure_headless_mini_swe
w=pathlib.Path('/mnt/data/zhanglinfeng/workspace')
p=argparse.ArgumentParser(description='Actual mini-SWE runtime regression with fake model; no LLM API.')
p.add_argument('--image',required=True);p.add_argument('--out',type=pathlib.Path,required=True);args=p.parse_args()
args.out.resolve().relative_to(w)
image=args.image
if '@sha256:' not in image:raise ValueError('Use an immutable published runtime digest')
job={'agents':[{'name':'mini-swe-agent-preinstall','kwargs':{'config':{'agent':{'step_limit':1}}}}]}
configure_headless_mini_swe(job)
assert job['agents'][0]['kwargs']['config']['agent']=={'agent_class':'default','step_limit':1}
code="""import builtins,json
from minisweagent.agents import get_agent
class Model:
 def format_message(self,**kw):return kw
 def query(self,messages):return {'role':'assistant','content':'runner fixture','extra':{'actions':[],'cost':0}}
 def format_observation_messages(self,*args):return []
 def serialize(self):return {}
 def get_template_vars(self):return {}
class Env:
 def serialize(self):return {}
 def get_template_vars(self):return {}
 def execute(self,action):raise AssertionError('No task execution expected')
def no_input(*a,**kw):raise EOFError('headless stdin')
builtins.input=no_input
report={}
for kind in ['interactive','default']:
 a=get_agent(Model(),Env(),{'agent_class':kind,'system_template':'runner lifecycle fixture','instance_template':'{{task}}','step_limit':1,'cost_limit':0,'mode':'yolo','confirm_exit':False})
 try:r=a.run('configuration regression only');report[kind]={'exception':None,'exit_status':r['exit_status'],'calls':a.n_calls}
 except EOFError:report[kind]={'exception':'EOFError','calls':a.n_calls}
assert report['interactive']['exception']=='EOFError'
assert report['default']=={'exception':None,'exit_status':'LimitsExceeded','calls':1}
print('RESULT_JSON='+json.dumps(report))
"""
r=subprocess.run(['docker','run','--rm','--network','none',image,'python3','-I','-c',code],capture_output=True,text=True,timeout=30);line=next((x[len('RESULT_JSON='):] for x in r.stdout.splitlines() if x.startswith('RESULT_JSON=')),None);assert r.returncode==0 and line, r.stderr
p=args.out;p.write_text(json.dumps({'scope':'Actual published mini-swe-agent 2.2.8 runtime; fake model, no live LLM, not a benchmark question.','image':image,'results':json.loads(line),'passed':True},indent=2)+'\n');p.chmod(0o600);print(p.read_text())
