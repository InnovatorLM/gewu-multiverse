"""Exercise the actual launcher readiness block without services or model calls."""
import errno
from pathlib import Path
import stat
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SOURCE = (Path(__file__).parent / 'start-universe').read_text().split("<<'PY_QUEUE_CHECK'\n", 1)[1].split('\nPY_QUEUE_CHECK', 1)[0]
LAUNCHER = (Path(__file__).parent / 'start-universe').read_text()


class ReadyFileTests(unittest.TestCase):
    def test_watchdog_is_owned_and_stopped_with_launcher(self):
        self.assertIn('command_watchdog.py',LAUNCHER)
        self.assertIn('watchdog_pid=$!',LAUNCHER)
        self.assertIn('kill -TERM "$watchdog_pid"',LAUNCHER)
        self.assertIn('wait "$watchdog_pid"',LAUNCHER)
        self.assertLess(LAUNCHER.index('watchdog_pid=$!'),LAUNCHER.index('export USER=nobody'))

    def run_check(self, reads, times):
        with patch('pathlib.Path') as constructor, patch('os.kill'), patch('time.sleep'), patch('time.monotonic', side_effect=times), patch.object(sys, 'argv', ['check', '42', '/ready']):
            path = constructor.return_value
            path.lstat.return_value = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=0)
            path.read_text.side_effect = reads
            exec(compile(SOURCE, 'launcher-ready-check', 'exec'), {})
            return path.read_text.call_count

    def test_stale_handle_is_reopened_then_current_worker_required(self):
        self.assertEqual(self.run_check([OSError(errno.ESTALE, 'stale'), '{"pid":41}', '{"pid":42}'], [0, 1, 2]), 3)

    def test_repeated_stale_handles_still_hit_deadline(self):
        with self.assertRaisesRegex(SystemExit, 'worker failed startup'):
            self.run_check([OSError(errno.ESTALE, 'stale')], [0, 16])

    def test_permission_error_is_not_retried(self):
        with self.assertRaises(PermissionError):
            self.run_check([PermissionError(errno.EACCES, 'denied')], [0])


if __name__ == '__main__':
    unittest.main()
