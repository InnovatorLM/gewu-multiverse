"""Mock evidence finalization; no LLM calls or new tool execution."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from evaluation_queue import W
import finalize_review_evidence as finalizer
from test_review_driver import Response


@unittest.skipUnless(os.geteuid()==0 and (W/'repos/unified-evaluator-pipeline').exists(), 'requires operator/private rubric fixture')
class FinalizationTests(unittest.TestCase):
    def test_rejected_reference_then_valid_same_evidence(self):
        self.run_finalization(False)

    def test_json_body_uses_same_strict_evidence_checks(self):
        self.run_finalization(True)

    def run_finalization(self, json_body):
        sys.path.insert(0,str(W/'repos/unified-evaluator-pipeline'))
        from unified_evaluator.pipelines.quality_review.review import load_rubric
        rubric,_=load_rubric()
        gate=next(item for item in rubric['gate_statuses'] if item!='confirmed_blocker')
        review={'task_id':'robust-sensor-calibration','summary':'Mock report','dimensions':{name:{'score':4,'reason':'Mock fixture'} for name in ['science','contract','verifier','integrity','research_work','feasibility']},'gate':{'status':gate,'reason':'Mock fixture'},'difficulty':{'level':2,'confounded':False,'reason':'Mock fixture'},'issues':[],'suggestions':[],'limitations':['Mock only'],'tool_evidence':[{'issue_id':'summary','tool_call_id':'actual-call','quote':'actual value 2.000000'}]}
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            source=Path(temporary)/'source';source.mkdir();out=Path(temporary)/'finalized'
            registry=json.loads((W/'.config/science-evaluation/registry.json').read_text())
            (source/'request-metadata.json').write_text(json.dumps({'evaluation_id':'calibration-v1','snapshot_sha256':registry['calibration-v1']['snapshot_sha256']}))
            (source/'tool-evidence.json').write_text(json.dumps([{'tool_call_id':'actual-call','command':'mock calculation','returncode':0,'stdout':'actual value 2.000000','stderr':'','cleanup_confirmed':True}]))
            responses=[]
            for identifier in ['invented-call','actual-call']:
                report=json.loads(json.dumps(review));report['tool_evidence'][0]['tool_call_id']=identifier
                message = {'content':json.dumps(report)} if json_body else {'content':None,'tool_calls':[{'id':'submission-'+identifier,'type':'function','function':{'name':'submit_review','arguments':json.dumps(report)}}]}
                responses.append({'choices':[{'finish_reason':'stop' if json_body else 'tool_calls','message':message}],'usage':{'prompt_tokens':1,'completion_tokens':1}})
            argv=['finalize_review_evidence.py','--source',str(source),'--output',str(out)]
            if json_body: argv.append('--json-body')
            with patch.object(sys,'argv',argv),patch.dict(os.environ,{'LLM_PROVIDER':'dawnfm','OPENAI_MODEL':'deepseek-v4.1-flash-1017','OPENAI_BASE_URL':'https://dawnfm.gravarc.cn/v1','OPENAI_API_KEY':'mock'},clear=True),patch('urllib.request.urlopen',side_effect=lambda *a,**k:Response(responses.pop(0))),contextlib.redirect_stdout(io.StringIO()):
                finalizer.main()
            result=json.loads((out/'review.json').read_text())
            self.assertFalse(result['new_independent_review'])
            self.assertFalse(result['scientific_acceptance'])
            self.assertFalse(result['additional_tool_execution'])
            self.assertEqual(result['source_tool_calls'],1)
            self.assertEqual(len(list(out.glob('response-*.json'))),2)
            self.assertFalse(responses)
            self.assertEqual(result['usage_finalization'],{'prompt_tokens':2,'completion_tokens':2})


if __name__=='__main__':unittest.main()
