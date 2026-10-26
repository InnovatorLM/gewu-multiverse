"""Private ATIF retention: real conversion, fake transfer, no model or ACS."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'True'
sys.path.insert(0,str(Path(__file__).parent/'harbor-extensions'))
import private_trajectory as collector
from universe_metrics import MetadataOnlyMiniSwe
from evaluation_queue import W


@unittest.skipUnless(os.geteuid()==0,'private controller ownership required')
class PrivateTrajectoryTests(unittest.TestCase):
    def test_conversion_permissions_secret_refusal_and_default_off(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            root=Path(temporary)
            def destination(name):
                p=root/name;p.mkdir(mode=0o700)
                (p/'identity.json').write_text(json.dumps({'snapshot_sha256':'a'*64,'provider':'dawnfm','model':'deepseek-v4.1-flash-1017'}));(p/'identity.json').chmod(0o600);return p
            source={'info':{'mini_version':'2.2.8','config':{'model':{'model_name':'openai/deepseek-v4.1-flash-1017'}}},'messages':[{'role':'user','content':'Compute the measurement.'},{'role':'assistant','content':'Computed result.'}]}
            class Environment:
                transfers=0
                async def download_file(self,remote,local):
                    self.transfers+=1;Path(local).write_text(json.dumps(source))
                async def exec(self,**kwargs):
                    return SimpleNamespace(return_code=0,stdout=json.dumps({'input_tokens':10,'output_tokens':2,'model_messages':1,'tool_result_messages':0,'native_tool_calls':0}))
            env=Environment()
            with patch.object(collector,'ROOT',root):
                path=destination('success');result=asyncio.run(collector.retain(env,path,secrets=['designated-test-secret']))
                self.assertTrue(result['review_ready']);self.assertTrue(result['schema_version'].startswith('ATIF'))
                self.assertEqual(result['atif_sha256'],hashlib.sha256((path/'trajectory.json').read_bytes()).hexdigest())
                for file in path.iterdir():self.assertEqual(stat.S_IMODE(file.stat().st_mode),0o600)
                source['messages'][1]['content']='designated-test-secret'
                quarantine=destination('quarantine')
                with self.assertRaises(ValueError):asyncio.run(collector.retain(env,quarantine,secrets=['designated-test-secret']))
                self.assertFalse(json.loads((quarantine/'retention.json').read_text())['review_ready']);self.assertFalse((quarantine/'trajectory.json').exists())
                source['messages'][1]['content']='Computed result.'
                agent=object.__new__(MetadataOnlyMiniSwe);agent._private_trajectory_dir=None
                with patch('universe_metrics.MiniSweAgentPreinstall.run',new=AsyncMock()):
                    before=env.transfers;asyncio.run(agent.run('instruction',env,None));self.assertEqual(env.transfers,before)
                context=SimpleNamespace();agent.populate_context_post_run(context)
                self.assertFalse(context.metadata['raw_trajectory_exported']);self.assertNotIn('private_trajectory_dir',context.metadata)
                wrong=destination('wrong-mode');wrong.chmod(0o755)
                with self.assertRaises(ValueError):asyncio.run(collector.retain(env,wrong))
                link=root/'linked';link.symlink_to(path,target_is_directory=True)
                with self.assertRaises(ValueError):asyncio.run(collector.retain(env,link))
                source['info']['config']['model']['model_name']='openai/other-model'
                with self.assertRaises(ValueError):asyncio.run(collector.retain(env,destination('wrong-model')))


if __name__=='__main__':unittest.main()
