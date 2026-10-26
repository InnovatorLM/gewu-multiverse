"""Mock transport integration; requires local private rubric, never calls a model."""
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
import review_registered_task as driver


class Response:
    def __init__(self, value): self.data = io.StringIO(json.dumps(value))
    def __enter__(self): return self.data
    def __exit__(self, *args): self.data.close()


class FakeTools:
    def __init__(self, *args): self.calls = []
    def close(self): pass
    def call(self, call):
        result = {'returncode': 0, 'stdout': 'calculated value = 2.000000', 'stderr': '', 'termination': None, 'cleanup_confirmed': True}
        self.calls.append({'tool_call_id': call['id'], 'command': json.loads(call['function']['arguments'])['command'], **result})
        return result


@unittest.skipUnless(os.geteuid() == 0 and (W / 'repos/unified-evaluator-pipeline').exists(), 'operator integration fixture required')
class DriverTests(unittest.TestCase):
    def test_structured_submission_and_fabricated_evidence(self):
        sys.path.insert(0, str(W / 'repos/unified-evaluator-pipeline'))
        from unified_evaluator.pipelines.quality_review.review import load_rubric
        rubric, _ = load_rubric()
        gate = next(value for value in rubric['gate_statuses'] if value != 'confirmed_blocker')
        review = {'task_id':'robust-sensor-calibration','summary':'Mock report; not scientific evidence','dimensions':{name:{'score':4,'reason':'Mock fixture'} for name in ['science','contract','verifier','integrity','research_work','feasibility']},'gate':{'status':gate,'reason':'Mock fixture'},'difficulty':{'level':2,'confounded':False,'reason':'Mock fixture'},'issues':[],'suggestions':[],'limitations':['Mock transport only'],'tool_evidence':[{'issue_id':'summary','tool_call_id':'mock-shell','quote':'calculated value = 2.000000'}]}
        for fabricated in [False, True]:
            with self.subTest(fabricated=fabricated), tempfile.TemporaryDirectory(dir=W / '.tmp') as temporary:
                output = Path(temporary) / 'review'
                report = json.loads(json.dumps(review))
                if fabricated: report['tool_evidence'][0]['quote'] = 'invented calculation = 9.000000'
                calls = [('review_shell','mock-shell',{'command':'not executed; mock fixture'}), ('submit_review','mock-submit',report)]
                responses = [{'choices':[{'finish_reason':'tool_calls','message':{'role':'assistant','content':None,'tool_calls':[{'id':identifier,'type':'function','function':{'name':name,'arguments':json.dumps(arguments)}}]}}],'usage':{'prompt_tokens':7,'completion_tokens':3}} for name,identifier,arguments in calls]
                if fabricated:
                    responses.append(json.loads(json.dumps(responses[-1])))
                def request(req, **kwargs):
                    body = json.loads(req.data)
                    self.assertEqual(body['model'], 'deepseek-v4.1-flash-1017')
                    return Response(responses.pop(0))
                argv = ['review_registered_task.py','--evaluation-id','calibration-v1','--output',str(output),'--tool-root',str(W / '.state/science-review-tools/root')]
                with patch.object(sys,'argv',argv), patch.dict(os.environ, {'LLM_PROVIDER':'dawnfm','OPENAI_MODEL':'deepseek-v4.1-flash-1017','OPENAI_BASE_URL':'https://dawnfm.gravarc.cn/v1','OPENAI_API_KEY':'mock-not-a-credential'},clear=True), patch('urllib.request.urlopen',request), patch('review_tools.ReviewTools',FakeTools), contextlib.redirect_stdout(io.StringIO()):
                    if fabricated:
                        with self.assertRaises(ValueError): driver.main()
                        self.assertFalse((output / 'review.json').exists())
                    else:
                        driver.main()
                        result = json.loads((output / 'review.json').read_text())
                        self.assertEqual(result['usage'], {'prompt_tokens':14,'completion_tokens':6})
                        self.assertEqual(result['tool_calls'],1)
                        self.assertFalse(result['scientific_acceptance'])
                        self.assertFalse(result['factual_acceptance'])
                self.assertFalse(responses)


if __name__ == '__main__': unittest.main()
