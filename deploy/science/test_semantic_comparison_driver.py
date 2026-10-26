"""Mock full-corpus coverage/resume; no live API calls."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from evaluation_queue import W
import semantic_comparison as driver
from test_review_driver import Response


@unittest.skipUnless(os.geteuid()==0 and (W/'.config/science-evaluation/queue.json').exists(),'operator registry fixture required')
class DriverTests(unittest.TestCase):
    def test_every_source_cited_and_resume_makes_no_new_calls(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            base=Path(temporary);corpus=base/'corpus';corpus.mkdir();output=base/'comparison'
            records=[]
            for i,name in enumerate(['terminal-bench-4.0','terminal-bench-science-v0.1']):
                text='Infer physical parameters from observations.' if i else 'Repair a command line scientific tool.'
                records.append({'dataset':name,'commit':'a'*40,'path':'tasks/mock/instruction.md','git_blob':'b'*40,'sha256':hashlib.sha256(text.encode()).hexdigest(),'instruction':text})
            raw=json.dumps(records).encode();(corpus/'instructions.json').write_bytes(raw)
            (corpus/'manifest.json').write_text(json.dumps({'instructions_sha256':hashlib.sha256(raw).hexdigest(),'sources':{r['dataset']:1 for r in records}}))
            comparisons=[{'reference_id':i,'relation':'unrelated','difficulty_comparison':'unknown','reason':'Mock only','reference_quote_index':0,'candidate_quote_index':0} for i in range(2)]
            response={'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'comparisons':comparisons})}}],'usage':{'prompt_tokens':20,'completion_tokens':10}}
            argv=['semantic_comparison.py','--evaluation-id','calibration-v1','--corpus',str(corpus),'--output',str(output)]
            environment={'LLM_PROVIDER':'dawnfm','OPENAI_MODEL':'deepseek-v4.1-flash-1017','OPENAI_BASE_URL':'https://dawnfm.gravarc.cn/v1','OPENAI_API_KEY':'mock-not-a-credential'}
            with patch.object(sys,'argv',argv),patch.dict(os.environ,environment,clear=True),patch('urllib.request.urlopen',return_value=Response(response)) as api,contextlib.redirect_stdout(io.StringIO()):
                driver.main()
                self.assertEqual(api.call_count,1)
            report=json.loads((output/'report.json').read_text())
            self.assertEqual(report['coverage'],1)
            self.assertEqual(len(report['comparisons']),2)
            self.assertFalse(report['scientific_acceptance'])
            self.assertFalse(report['quality_acceptance'])
            self.assertTrue(report['factual_verification_required'])
            self.assertEqual(report['usage'],{'prompt_tokens':20,'completion_tokens':10})
            argv.append('--resume')
            with patch.object(sys,'argv',argv),patch.dict(os.environ,environment,clear=True),patch('urllib.request.urlopen',side_effect=AssertionError('resume must not call model')),contextlib.redirect_stdout(io.StringIO()):driver.main()
            saved=json.loads((output/'batch-000.json').read_text());saved['comparisons'][0]['reference_quote']='invented quotation';(output/'batch-000.json').write_text(json.dumps(saved))
            with patch.object(sys,'argv',argv),patch.dict(os.environ,environment,clear=True),patch('urllib.request.urlopen',side_effect=AssertionError('invalid retained result must not call model')),self.assertRaises(ValueError):driver.main()


if __name__=='__main__':unittest.main()
