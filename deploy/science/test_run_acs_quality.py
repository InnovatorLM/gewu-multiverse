"""Credential-free controller preflight refusal checks; no Kubernetes calls."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    unittest.main()
