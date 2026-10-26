import json
import shlex
from harbor.agents.installed.mini_swe_agent_preinstall import MiniSweAgentPreinstall

class MetadataOnlyMiniSwe(MiniSweAgentPreinstall):
    async def run(self, instruction, environment, context):
        await super().run(instruction, environment, context)
        code = '''import json
d=json.load(open('/logs/agent/mini-swe-agent.trajectory.json'))
messages=d.get('messages',[])
usage=[]
for m in messages:
 u=((m.get('extra') or {}).get('response') or {}).get('usage') or m.get('usage')
 if isinstance(u,dict): usage.append(u)
def total(a,b):
 vals=[u.get(a,u.get(b)) for u in usage]
 return sum(v for v in vals if isinstance(v,int)) if any(isinstance(v,int) for v in vals) else None
print(json.dumps(dict(input_tokens=total('prompt_tokens','input_tokens'),output_tokens=total('completion_tokens','output_tokens'),model_messages=sum(m.get('role')=='assistant' for m in messages),tool_result_messages=sum(m.get('role') in ('tool','observation') for m in messages),native_tool_calls=sum(len(m.get('tool_calls') or []) for m in messages))))
'''
        result = await environment.exec(command='python3 -c ' + shlex.quote(code))
        if result.return_code != 0:
            raise ValueError('Metadata extraction failed')
        data=json.loads(result.stdout)
        keys={'input_tokens','output_tokens','model_messages','tool_result_messages','native_tool_calls'}
        if set(data)!=keys or any(v is not None and (not isinstance(v,int) or v<0) for v in data.values()):
            raise ValueError('Invalid aggregate metadata')
        self._aggregate_metrics=data

    def populate_context_post_run(self, context):
        data=getattr(self,'_aggregate_metrics',None)
        if data is None:
            return
        context.n_input_tokens=data['input_tokens']
        context.n_output_tokens=data['output_tokens']
        context.metadata={'aggregate_metrics':data,'raw_trajectory_exported':False}
