import subprocess
import tempfile
import unittest
from pathlib import Path
from evaluation_queue import W
from selftest_lifecycle import recover_interrupted, owned_run

class RecoveryTests(unittest.TestCase):
    def test_interrupted_job_keeps_source(self):
        with tempfile.TemporaryDirectory(dir=W / '.tmp') as raw:
            root = Path(raw)
            work = root / 'job'
            work.mkdir()
            source = work / 'upload.tar'
            source.write_bytes(b'preserved')
            result = root / 'result.json'
            result.write_text('{"status":"building"}')
            published = []
            self.assertTrue(recover_interrupted(work, result, published.append))
            self.assertEqual(published[0]['status'], 'interrupted')
            self.assertEqual(source.read_bytes(), b'preserved')

    def test_finished_jobs_are_not_repeated(self):
        with tempfile.TemporaryDirectory(dir=W / '.tmp') as raw:
            root = Path(raw)
            result = root / 'r'
            result.write_text('{"status":"selftest_passed"}')
            self.assertTrue(recover_interrupted(root / 'job', result, lambda _: self.fail('republished')))

    def test_new_job_is_eligible(self):
        with tempfile.TemporaryDirectory(dir=W / '.tmp') as raw:
            self.assertFalse(recover_interrupted(Path(raw) / 'job', Path(raw) / 'r', lambda _: None))

    def test_timeout_is_not_swallowed(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            owned_run(['sleep', '20'], timeout=0.05)

if __name__ == '__main__':
    unittest.main()
