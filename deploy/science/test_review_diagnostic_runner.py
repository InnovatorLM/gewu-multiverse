"""Diagnostic orchestration with mocked subprocess stages; no model/ACS calls."""
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from evaluation_queue import W
import run_review_diagnostic as runner


@unittest.skipUnless(os.geteuid()==0 and (W/'.config/science-evaluation/registry.json').exists(),'operator registered quality fixture required')
class RunnerTests(unittest.TestCase):
    def test_failed_first_stage_uses_same_evidence_then_no_acceptance(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            job=Path(temporary)/'job';entry=json.loads((W/'.config/science-evaluation/registry.json').read_text())['calibration-quality-v1']
            called=[]
            def run(command,**kwargs):
                script=Path(command[1]).name;called.append(script)
                output=Path(command[command.index('--output')+1]);output.mkdir()
                if script=='review_registered_task.py':
                    (output/'tool-evidence.json').write_text('[]')
                    return SimpleNamespace(returncode=1)
                self.assertEqual(script,'finalize_review_evidence.py')
                self.assertIn('--json-body',command)
                (output/'review.json').write_text(json.dumps({'scientific_acceptance':False,'factual_acceptance':False,'snapshot_sha256':entry['snapshot_sha256'],'new_independent_review':False,'source_tool_calls':2,'review':{'summary':'Mock diagnostic'},'usage_finalization':{'prompt_tokens':5,'completion_tokens':2},'usage_source_review':{'prompt_tokens':40,'completion_tokens':8}}))
                return SimpleNamespace(returncode=0)
            argv=['run_review_diagnostic.py','--evaluation-id','calibration-quality-v1','--root',entry['review_root'],'--job',str(job)]
            with patch.object(sys,'argv',argv),patch('run_review_diagnostic.subprocess.run',run),patch('run_review_diagnostic.role_processes',return_value=[]):runner.main()
            result=json.loads((job/'summary.json').read_text())
            self.assertEqual(result['status'],'quality_diagnostic_complete')
            self.assertEqual(called,['review_registered_task.py','finalize_review_evidence.py'])
            self.assertFalse(result['quality_acceptance'])
            self.assertFalse(result['release_eligible'])
            self.assertTrue(result['factual_verification_required'])
            self.assertFalse(result['acs_launched'])
            self.assertFalse(result['diagnostic']['new_independent_review'])
            self.assertEqual(result['attempts'][0]['exit_code'],1)
            self.assertEqual(result['diagnostic']['usage_source_review'],{'prompt_tokens':40,'completion_tokens':8})


if __name__=='__main__':unittest.main()
