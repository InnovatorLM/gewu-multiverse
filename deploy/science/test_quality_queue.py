"""Mock quality dispatch integration; does not call LLM or create ACS resources."""
import json
import os
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest.mock import patch
from evaluation_queue import W, process


@unittest.skipUnless(os.geteuid()==0 and (W/'.config/science-evaluation/registry.json').exists(), 'requires operator registry fixture')
class QualityQueueTests(unittest.TestCase):
    def test_quality_route_and_missing_report(self):
        for report_present in [True,False]:
            with self.subTest(report_present=report_present),tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
                base=Path(temporary)
                for name in ['inbox','results','state']: (base/name).mkdir(mode=0o700)
                entry=json.loads((W/'.config/science-evaluation/registry.json').read_text())['calibration-v1']
                entry.update(dispatch='quality_diagnostic',review_root=str(W/'.state/science-review-tools/root'))
                registry=base/'registry.json';registry.write_text(json.dumps({'quality-test':entry}));registry.chmod(0o600)
                config={'registry':str(registry),'state':str(base/'state'),'results':str(base/'results'),'inbox':str(base/'inbox'),'evaluator_uid':21002,'max_jobs_per_day':3}
                identifier=uuid.uuid4().hex
                request=base/'inbox'/f'{identifier}.json';request.write_text(json.dumps({'job_id':identifier,'evaluation_id':'quality-test','snapshot_sha256':entry['snapshot_sha256']}));os.chown(request,21002,21002)
                captured=[]
                class FakeChild:
                    pid=99999999
                    def __init__(self,command,**kwargs):
                        captured.append(command)
                        assert command[0].endswith('/run-quality-diagnostic')
                        assert '--root' in command and 'quality-test' in command
                        job=Path(command[command.index('--job')+1]);job.mkdir()
                        if report_present:
                            (job/'summary.json').write_text(json.dumps({'status':'quality_diagnostic_complete','cleanup_confirmed':True,'quality_acceptance':False,'scientific_acceptance':False,'release_eligible':False,'factual_verification_required':True,'acs_launched':False,'diagnostic':{'review':{'summary':'Mock diagnostic'}}}))
                    def wait(self,timeout=None):return 0
                    def poll(self):return 0
                with patch('evaluation_queue.subprocess.Popen',FakeChild):
                    result=process(config,request,mock=False)
                self.assertEqual(len(captured),1)
                self.assertEqual(result['status'],'quality_diagnostic_complete' if report_present else 'quality_diagnostic_failed')
                self.assertTrue(result['cleanup_confirmed'])
                self.assertTrue(result['factual_verification_required'])
                self.assertFalse(result['quality_acceptance'])
                self.assertFalse(result['scientific_acceptance'])
                self.assertFalse(result['release_eligible'])
                self.assertNotIn('reward',result)
                retained=json.loads((base/'results'/f'{identifier}.json').read_text())
                self.assertEqual(result,retained)

    def test_unknown_dispatch_refused_before_job_claim(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            base=Path(temporary);(base/'state').mkdir()
            entry=json.loads((W/'.config/science-evaluation/registry.json').read_text())['calibration-v1'];entry['dispatch']='run-arbitrary-command'
            registry=base/'registry.json';registry.write_text(json.dumps({'test':entry}))
            identifier=uuid.uuid4().hex;request=base/f'{identifier}.json';request.write_text(json.dumps({'job_id':identifier,'evaluation_id':'test','snapshot_sha256':entry['snapshot_sha256']}));os.chown(request,21002,21002)
            with self.assertRaises(ValueError):process({'registry':str(registry),'state':str(base/'state'),'results':str(base),'evaluator_uid':21002},request)
            self.assertFalse((base/'state'/identifier).exists())


if __name__=='__main__':unittest.main()
