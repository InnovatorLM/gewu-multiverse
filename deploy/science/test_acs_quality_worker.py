import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('worker', Path(__file__).with_name('acs_quality_worker.py'))
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class WorkerContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=worker.WORKSPACE / '.tmp')
        self.w = Path(self.temp.name)
        self.root = self.w / '.state/qa-live-0123456789'
        self.task = self.root / 'tasks/public-benchmark-fixture'
        # Contract fixture only; never published or used as a benchmark problem.
        for name in ['instruction.md', 'task.toml', 'environment/Dockerfile',
                     'solution/solve.sh', 'tests/test.sh']:
            p = self.task / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('contract fixture\n')
        self.patch = patch.object(worker, 'WORKSPACE', self.w)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_inventory_binds_all_task_content(self):
        task, before = worker.contract(self.root, self.task.name)
        (task / 'instruction.md').write_text('changed')
        self.assertNotEqual(before, worker.inventory(task))

    def test_task_traversal_and_bad_run_identity_refused(self):
        for name in ['../public-benchmark-fixture', '/task', 'bad;echo']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                worker.contract(self.root, name)
        with self.assertRaises(ValueError):
            worker.contract(self.root.parent / 'arbitrary', self.task.name)

    def test_task_symlink_refused(self):
        (self.task / 'escaped').symlink_to(self.w)
        with self.assertRaisesRegex(ValueError, 'links'):
            worker.contract(self.root, self.task.name)

    def test_missing_harbor_input_refused(self):
        (self.task / 'tests/test.sh').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            worker.contract(self.root, self.task.name)

    def test_command_has_fixed_model_and_no_key_argument(self):
        cmd = worker.command(self.root, self.task)
        self.assertEqual(cmd[cmd.index('--model') + 1], 'deepseek-v4.1-flash-1017')
        self.assertEqual(cmd[cmd.index('--timeout') + 1], '1800')
        self.assertEqual(cmd[cmd.index('--output') + 1], str(self.root / 'output/review.json'))
        self.assertFalse(any('OPENAI_API_KEY' in item for item in cmd))

    def test_existing_state_refused_before_model_launch(self):
        (self.root / 'home').mkdir()
        with patch.object(worker.subprocess, 'Popen') as spawn:
            with self.assertRaisesRegex(ValueError, 'fresh'):
                worker.run(self.root, self.task.name, 'FAKE_NOT_A_REAL_KEY')
            spawn.assert_not_called()


if __name__ == '__main__':
    unittest.main()
