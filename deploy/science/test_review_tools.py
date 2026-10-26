"""Actual nonroot chroot calculations and negative evidence checks; no LLM calls."""
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
import unittest

from evaluation_queue import W, digest_tree
from review_tools import ReviewTools, validate_evidence, replay_for_finalization, submission_tool
from role_exec import role_processes

ROOT = W / '.state/science-review-tools/root'
SNAPSHOT = W / '.state/science-evaluation-queue/registered/calibration-v1/robust-sensor-calibration'


def call(identifier, command):
    return {'id': identifier, 'type': 'function', 'function': {'name': 'review_shell', 'arguments': json.dumps({'command': command})}}


class EvidenceTests(unittest.TestCase):
    def test_submission_schema_keeps_dimensions_separate(self):
        parameters = submission_tool(['confirmed_blocker'])['function']['parameters']
        self.assertEqual(set(parameters['properties']['dimensions']['properties']), {'science', 'contract', 'verifier', 'integrity', 'research_work', 'feasibility'})
        self.assertIn('gate', parameters['required'])
        self.assertIn('tool_evidence', parameters['required'])
        self.assertNotIn('gate', parameters['properties']['dimensions']['properties'])

    def test_resume_preserves_actual_evidence_and_usage(self):
        calls = [{'tool_call_id': str(i), 'command': 'printf evidence', 'returncode': 0, 'cleanup_confirmed': True, 'termination': None, 'stdout': 'evidence', 'stderr': ''} for i in range(10)]
        requested = [call(str(i), 'printf evidence') for i in range(11)]
        responses = [{'usage': {'prompt_tokens': 10, 'completion_tokens': 2}, 'choices': [{'finish_reason':'tool_calls', 'message': {'content':None, 'tool_calls': requested}}]}]
        messages, usage = replay_for_finalization(responses, calls)
        self.assertEqual(usage, {'prompt_tokens': 10, 'completion_tokens': 2})
        self.assertTrue(json.loads(messages[-1]['content'])['not_executed'])
        self.assertEqual(len(messages), 12)
        with self.assertRaises(ValueError):
            replay_for_finalization(responses, calls[:9])
        broken = json.loads(json.dumps(calls))
        broken[0]['command'] = 'different command'
        with self.assertRaises(ValueError):
            replay_for_finalization(responses, broken)

    def test_fabricated_quotes_refused(self):
        calls = [{'tool_call_id': 'one', 'returncode': 0, 'cleanup_confirmed': True, 'stdout': 'slope=2.000000', 'stderr': ''}]
        review = {'issues': [{'id': 'I1'}], 'tool_evidence': [{'issue_id': 'I1', 'tool_call_id': 'one', 'quote': 'slope=2.000000'}]}
        validate_evidence(review, calls)
        for field, value in [('quote', 'slope=9.000000'), ('tool_call_id', 'fabricated'), ('issue_id', 'unknown')]:
            broken = json.loads(json.dumps(review))
            broken['tool_evidence'][0][field] = value
            with self.assertRaises(ValueError):
                validate_evidence(broken, calls)
        with self.assertRaises(ValueError):
            validate_evidence({'issues': [{'id': 'I2'}], 'tool_evidence': review['tool_evidence']}, calls)


@unittest.skipUnless(os.geteuid() == 0 and ROOT.exists(), 'requires prepared private tool root')
class LiveChrootTests(unittest.TestCase):
    def test_calculation_isolation_and_cleanup(self):
        os.environ['REVIEW_HOST_SECRET_SENTINEL'] = 'must-not-reach-tools'
        tools = ReviewTools(ROOT, digest_tree(SNAPSHOT))
        try:
            code = "import os,json,csv,statistics; from pathlib import Path; rows=list(csv.DictReader(open('/task/data/calibration.csv'))); print(json.dumps({'uid':os.getuid(),'gid':os.getgid(),'groups':os.getgroups(),'rows':len(rows),'host_secret_present': 'REVIEW_HOST_SECRET_SENTINEL' in os.environ,'key_present':'OPENAI_API_KEY' in os.environ,'host_path_visible':Path('/mnt/data/zhanglinfeng/workspace/.config/llm/dawnfm.env').exists(),'proc_visible':Path('/proc/1').exists()}))"
            result = tools.call(call('calc1', 'python3 -c ' + shlex.quote(code)))
            self.assertEqual(result['returncode'], 0, result)
            evidence = json.loads(result['stdout'])
            self.assertEqual(evidence, {'uid': 21012, 'gid': 21012, 'groups': [21012], 'rows': 25, 'host_secret_present': False, 'key_present': False, 'host_path_visible': False, 'proc_visible': False})
            result = tools.call(call('readonly', "python3 -c \"open('/task/instruction.md','w').write('changed')\""))
            self.assertNotEqual(result['returncode'], 0)
            result = tools.call(call('detach', 'setsid sleep 60 >/tmp/detach.out 2>&1 & echo detached'))
            self.assertTrue(result['cleanup_confirmed'])
            self.assertFalse(role_processes(21012))
            with self.assertRaises(ValueError):
                ReviewTools(ROOT, digest_tree(SNAPSHOT))
        finally:
            tools.close()
            del os.environ['REVIEW_HOST_SECRET_SENTINEL']
        self.assertEqual(digest_tree(ROOT / 'task'), digest_tree(SNAPSHOT))

    def test_controller_death_cleans_tools(self):
        self._controller_cleanup(False)

    def test_process_group_termination_cleans_tools(self):
        self._controller_cleanup(True)

    def _controller_cleanup(self, group):
        child_code = "from review_tools import ReviewTools; from evaluation_queue import digest_tree; import json; t=ReviewTools(" + repr(str(ROOT)) + ", digest_tree(" + repr(str(SNAPSHOT)) + ")); t.call({'id':'death','type':'function','function':{'name':'review_shell','arguments':json.dumps({'command':'sleep 60'})}})"
        env = {'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(Path(__file__).parent)}
        child = subprocess.Popen([sys.executable, '-c', child_code], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=group)
        try:
            deadline = time.monotonic() + 20
            while not role_processes(21012) and time.monotonic() < deadline:
                if child.poll() is not None:
                    self.fail('Controller exited before real command started')
                time.sleep(0.1)
            self.assertTrue(role_processes(21012))
            if group:
                os.killpg(child.pid, signal.SIGTERM)
            else:
                child.kill()
            child.wait(timeout=5)
            deadline = time.monotonic() + 10
            while role_processes(21012) and time.monotonic() < deadline:
                time.sleep(0.1)
            self.assertFalse(role_processes(21012))
        finally:
            if child.poll() is None:
                child.kill()
                child.wait()


if __name__ == '__main__':
    unittest.main()
