"""Native input validation with synthetic trial; no model/ACS and no key copy."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from evaluation_queue import W
from prepare_private_trial import prepare


@unittest.skipUnless(os.geteuid()==0,'operator evidence fixture')
class TrialPreparationTests(unittest.TestCase):
    def test_native_input_and_cross_run_refusal(self):
        entry=json.loads((W/'.config/science-evaluation/registry.json').read_text())['calibration-v1']
        with tempfile.TemporaryDirectory(dir=W/'.state') as temporary:
            root=Path(temporary);private=root/'trace'/'job';private.mkdir(parents=True);state=root/'queue';job=state/'job';trial=job/'runs'/'run'/'trial';trial.mkdir(parents=True)
            def save(path,value):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));path.chmod(0o600)
            answer={'job_id':'job','evaluation_id':'calibration-v1','snapshot_sha256':entry['snapshot_sha256'],'status':'solver_complete','cleanup_confirmed':True}
            save(job/'result.json',answer);save(job/'report.json',{'cleanup':{'confirmed':True},'harbor_exit_code':0});save(job/'config.json',{'job_name':'run'})
            save(private/'identity.json',{'evaluation_id':'calibration-v1'})
            save(private/'trajectory.json',{'schema_version':'ATIF-v1.7','steps':[{'step_id':1,'source':'agent','message':'Synthetic input only.'}]})
            original={'task':{'path':entry['snapshot']},'agent':{'name':'mini-swe-agent','model_name':'openai/deepseek-v4.1-flash-1017','env':{'OPENAI_API_KEY':'SENTINEL-MUST-NOT-COPY'}}}
            save(trial/'config.json',original);save(trial/'result.json',{'task_name':Path(entry['snapshot']).name,'config':original,'finished_at':'2026-10-26T00:00:00Z','exception_info':None,'verifier_result':{'rewards':{'reward':1}}})
            (trial/'verifier').mkdir();(trial/'verifier/test-stdout.txt').write_text('PASS\n');(trial/'verifier/test-stdout.txt').chmod(0o600)
            with patch('prepare_private_trial.validate',return_value={'review_input_eligible':True}):
                output=root/'prepared';result=prepare(private,entry,state,output)
                self.assertTrue(result['native_input_validation_passed']);self.assertTrue(result['config_sanitized']);self.assertFalse(result['release_eligible'])
                self.assertNotIn('SENTINEL-MUST-NOT-COPY',(output/'config.json').read_text());self.assertNotIn('OPENAI_API_KEY',(output/'config.json').read_text())
                self.assertNotIn('SENTINEL-MUST-NOT-COPY',(output/'result.json').read_text());self.assertNotIn('config',json.loads((output/'result.json').read_text()))
                self.assertFalse(result['artifact_collection_copied'])
                answer['job_id']='foreign-job';save(job/'result.json',answer)
                with self.assertRaises(ValueError):prepare(private,entry,state,root/'foreign')
                answer['job_id']='job';save(job/'result.json',answer);original['task']['path']=str(root/'foreign-task');save(trial/'config.json',original)
                with self.assertRaises(ValueError):prepare(private,entry,state,root/'wrong-task')
                self.assertFalse((root/'foreign').exists());self.assertFalse((root/'wrong-task').exists())


if __name__=='__main__':unittest.main()
