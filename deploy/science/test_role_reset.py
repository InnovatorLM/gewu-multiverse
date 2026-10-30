import os, signal, subprocess, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
import role_reset as r

class ResetTests(unittest.TestCase):
    def test_directive_replaces_previous_reset_and_preserves_policy(self):
        first = r.directive('original policy', 'one', 'stalled', 'pivot')
        second = r.directive(first, 'two', 'new reason', 'new direction')
        self.assertEqual(second.count(r.BEGIN), 1)
        self.assertIn('original policy', second)
        self.assertNotIn('Operator reset: one', second)
        self.assertIn('same idea', second)

    def test_invalid_block_refused(self):
        with self.assertRaises(ValueError):
            r.directive('policy ' + r.BEGIN, 'one', 'reason', 'action')

    def test_runner_requires_uid_run_and_flag(self):
        run = Path('/workspace/state/author-02/run-123')
        info = dict(uid=65534,state='S',argv=[b'binary',b'--run-agent',str(run).encode()])
        self.assertTrue(r.runner_matches(info, run, 65534))
        for change in [dict(uid=0),dict(state='Z'),dict(argv=[b'binary',b'--run-agent',b'/another/run'])]:
            self.assertFalse(r.runner_matches(dict(info, **change), run, 65534))

    def test_pid_reuse_refuses_signal(self):
        with patch.object(r.os, 'pidfd_open', return_value=99), patch.object(r.os, 'close'), patch.object(r, 'process_info', return_value=dict(uid=1,start_ticks=20)), patch.object(r.signal, 'pidfd_send_signal') as send:
            with self.assertRaises(RuntimeError):
                r.signal_identity(dict(pid=123,uid=1,start_ticks=19), signal.SIGTERM)
            send.assert_not_called()

    def test_actual_throwaway_process_termination(self):
        process = subprocess.Popen(['sleep','30'])
        try:
            info = r.process_info(process.pid)
            r.signal_identity(info, signal.SIGTERM)
            process.wait(timeout=3)
            self.assertFalse(r.alive(info))
        finally:
            if process.poll() is None:process.kill();process.wait()

if __name__ == '__main__':unittest.main()
