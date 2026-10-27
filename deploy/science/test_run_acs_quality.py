"""Credential-free controller preflight refusal checks; no Kubernetes calls."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('acs_controller', Path(__file__).with_name('run_acs_quality.py'))
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


class ControllerPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=controller.W / '.tmp')
        self.path = Path(self.temp.name) / 'settings.json'
        self.settings = {'task': str(controller.W / 'public-fixture'), 'task_sha256': 'task-hash',
                         'runtime_image': 'invalid-image', 'codex_binary': 'unused',
                         'codex_sha256': 'unused', 'bundled_bwrap': 'unused',
                         'bwrap_sha256': 'unused', 'boundary_receipt': 'unused',
                         'worker_sha256': 'unused', 'pipeline_sha256': 'pipeline-hash'}
        self.digest = patch.object(controller, 'pipeline_digest', return_value='pipeline-hash')
        self.digest.start()

    def tearDown(self):
        self.digest.stop()
        self.temp.cleanup()

    def save(self):
        self.path.write_text(json.dumps(self.settings))
        self.path.chmod(0o600)

    def test_arbitrary_extra_command_field_refused(self):
        self.settings['command'] = 'never execute caller commands'; self.save()
        with self.assertRaisesRegex(ValueError, 'exact operator'):
            controller.load_settings(self.path)

    def test_pipeline_changes_refused(self):
        self.settings['pipeline_sha256'] = 'old'; self.save()
        with self.assertRaisesRegex(ValueError, 'pipeline changed'):
            controller.load_settings(self.path)

    def test_task_changes_refused(self):
        self.save()
        with patch('evaluation_queue.digest_tree', return_value='changed'):
            with self.assertRaisesRegex(ValueError, 'Task source changed'):
                controller.load_settings(self.path)

    def test_unpinned_image_refused(self):
        self.save()
        with patch('evaluation_queue.digest_tree', return_value='task-hash'):
            with self.assertRaisesRegex(ValueError, 'digest-pinned'):
                controller.load_settings(self.path)


class ControllerCleanupTests(unittest.TestCase):
    def setUp(self):
        self.api = Mock()
        self.custom = Mock()
        self.api.list_namespaced_pod.return_value = SimpleNamespace(items=[])
        self.custom.list_namespaced_custom_object.return_value = {'items': []}
        self.pod = SimpleNamespace(metadata=SimpleNamespace(labels={'evaluation-run': 'qa-test'}, uid='owned'))
        self.sleep = patch.object(controller.time, 'sleep')
        self.sleep.start()

    def tearDown(self):
        self.sleep.stop()

    def test_owned_pod_deleted_and_absence_confirmed(self):
        self.api.read_namespaced_pod.side_effect = [self.pod, controller.ApiException(status=404)]
        result = controller.cleanup_owned(self.api, self.custom, 'qa-test', 'owned')
        self.assertTrue(result['confirmed'])
        self.api.delete_namespaced_pod.assert_called_once()
        self.assertEqual(len(result['two_snapshots']), 2)

    def test_already_absent(self):
        self.api.read_namespaced_pod.side_effect = controller.ApiException(status=404)
        self.assertTrue(controller.cleanup_owned(self.api, self.custom, 'qa-test')['confirmed'])
        self.api.delete_namespaced_pod.assert_not_called()

    def test_uid_mismatch_never_deleted(self):
        self.api.read_namespaced_pod.return_value = self.pod
        result = controller.cleanup_owned(self.api, self.custom, 'qa-test', 'different')
        self.assertFalse(result['confirmed'])
        self.api.delete_namespaced_pod.assert_not_called()

    def test_snapshot_unknown_is_not_clean(self):
        for error in [controller.ApiException(status=403), TimeoutError()]:
            with self.subTest(error=type(error).__name__):
                self.api.read_namespaced_pod.side_effect = controller.ApiException(status=404)
                self.custom.list_namespaced_custom_object.side_effect = error
                result = controller.cleanup_owned(self.api, self.custom, 'qa-test')
                self.assertFalse(result['confirmed'])
                self.assertTrue(result['errors'])

    def test_delete_forbidden_is_not_clean(self):
        self.api.read_namespaced_pod.return_value = self.pod
        self.api.delete_namespaced_pod.side_effect = controller.ApiException(status=403)
        result = controller.cleanup_owned(self.api, self.custom, 'qa-test', 'owned')
        self.assertFalse(result['confirmed'])
        self.assertEqual(result['errors'][0]['status'], 403)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    unittest.main()
