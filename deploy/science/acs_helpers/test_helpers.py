"""Credential-free behavioral tests; no cluster or model requests."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import make_config
import provider_probe
import run_guard


class HelperTests(unittest.TestCase):
    def test_cluster_call_reads_lazy_response_body(self):
        class Response:
            status = 200
            data = None

            def read(self):
                self.data = b'{"items": []}'

        response = Response()
        from unittest.mock import Mock
        cluster = run_guard.Cluster.__new__(run_guard.Cluster)
        cluster.api = Mock()
        cluster.api.param_serialize.return_value = ('GET', '/mock', {}, None, [])
        cluster.api.call_api.return_value = response
        self.assertEqual(cluster.call('/mock'), {'items': []})

    def test_llm_config_binds_probe_and_preserves_secret_placeholder(self):
        with tempfile.TemporaryDirectory(dir='/mnt/data/zhanglinfeng/workspace/.tmp') as tmp:
            root = Path(tmp)
            task = root / 'a-task'
            task.mkdir()
            (task / 'task.toml').write_text('version="1.0"')
            (task / 'instruction.md').write_text('Do the task')
            kube = root / 'kubeconfig'
            kube.write_text('{}')
            probe = root / 'probe.json'
            probe.write_text(json.dumps({'live_api_test': True, 'provider': 'mock-provider',
                                        'base_url': 'https://model.invalid/v1', 'model': 'mock-model',
                                        'selected_protocol': 'chat'}))
            args = SimpleNamespace(task=str(task), kubeconfig=str(kube), image='registry.invalid/task:v1',
                                   registry=None, dind_image='docker:dind', run_id='test-run-unique', jobs_dir=str(root / 'runs'),
                                   namespace='default', pull_secret='acr-registry', mode='llm',
                                   agent='mini-swe-agent-preinstall', probe=str(probe))
            c = make_config.build(args)
            self.assertEqual(c['agents'][0]['model_name'], 'openai/mock-model')
            self.assertEqual(c['agents'][0]['env']['OPENAI_API_KEY'], '${OPENAI_API_KEY}')
            self.assertEqual(c['environment']['kwargs']['pod_overrides']['spec']['containers'][0]['image'], args.image)
            run_guard.check_config(c)
            c['environment']['kwargs']['pod_overrides']['spec']['containers'][0]['resources']['limits']['memory'] = '4Gi'
            with self.assertRaises(ValueError):
                run_guard.check_config(c)
            probe.write_text(json.dumps({'selected_protocol': None}))
            with self.assertRaises(ValueError):
                make_config.build(args)

    def test_probe_reports_status_without_leaking_raw_errors(self):
        values = {'OPENAI_API_KEY': 'mock-secret-never-log', 'OPENAI_MODEL': 'mock',
                  'OPENAI_BASE_URL': 'https://model.invalid/v1'}
        response = SimpleNamespace(ok=False, status_code=401, text='mock-secret-never-log')
        with patch.object(provider_probe.requests, 'post', return_value=response) as post:
            report = provider_probe.probe(values, 'chat')
            self.assertNotIn(values['OPENAI_API_KEY'], json.dumps(report))
            self.assertFalse(report['compatible'])
            self.assertFalse(post.call_args.kwargs['allow_redirects'])

    def test_cleanup_uses_uid_precondition_and_waits_for_two_empty_reads(self):
        calls = []

        class FakeCluster:
            snapshots = 0

            def snapshot(self, run_id):
                self.snapshots += 1
                return {k: [] for k in run_guard.KINDS}

            def call(self, path, method, body):
                calls.append((path, method, body))

            def path(self, kind):
                return '/mock/' + kind

            def deleted(self, kind, name):
                return True

        c = FakeCluster()
        with patch.object(run_guard.time, 'sleep') as sleep:
            report = run_guard.release(c, 'test-run-unique', {('pods', 'owned-pod'): 'uid-1'})
        self.assertTrue(report['confirmed'])
        self.assertEqual(calls[0][2]['preconditions'], {'uid': 'uid-1'})
        self.assertEqual(len(calls), 1)
        self.assertGreaterEqual(c.snapshots, 3)
        sleep.assert_called_once_with(3)

    def test_cleanup_does_not_treat_forbidden_as_deleted(self):
        class DeniedCluster:
            def snapshot(self, run_id):
                raise run_guard.ApiException(status=403)

        with self.assertRaises(run_guard.ApiException):
            run_guard.release(DeniedCluster(), 'test-run-unique', {})


if __name__ == '__main__':
    unittest.main()
