import fcntl, os, signal, subprocess, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
import role_reset as r

class ResetTests(unittest.TestCase):
    def test_active_launcher_blocks_reset_and_restart_can_follow(self):
        with tempfile.TemporaryDirectory(dir=r.W/'.tmp') as tmp:
            directory = Path(tmp)
            with (directory / 'lifecycle.lock').open('a') as launcher:
                fcntl.flock(launcher, fcntl.LOCK_SH | fcntl.LOCK_NB)
                with self.assertRaisesRegex(RuntimeError, 'Deployment is active'):
                    with r.maintenance_lock(directory):
                        self.fail('reset entered while launcher active')
            with r.maintenance_lock(directory):
                with (directory / 'lifecycle.lock').open('a') as restart:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(restart, fcntl.LOCK_SH | fcntl.LOCK_NB)
            with (directory / 'lifecycle.lock').open('a') as restart:
                fcntl.flock(restart, fcntl.LOCK_SH | fcntl.LOCK_NB)

    def test_lifecycle_lock_refuses_symlink(self):
        with tempfile.TemporaryDirectory(dir=r.W/'.tmp') as tmp:
            directory = Path(tmp)
            (directory / 'other').touch()
            (directory / 'lifecycle.lock').symlink_to(directory / 'other')
            with self.assertRaises(OSError):
                with r.maintenance_lock(directory):
                    self.fail('symlink accepted')

    def test_directive_replaces_previous_reset_and_preserves_policy(self):
        first = r.directive('original policy', 'one', 'stalled', 'pivot')
        second = r.directive(first, 'two', 'new reason', 'new direction')
        self.assertEqual(second.count(r.BEGIN), 1)
        self.assertIn('original policy', second)
        self.assertNotIn('Operator reset: one', second)
        self.assertIn('same idea', second)

    def test_reset_updates_controller_and_chroot_without_erasing_either_policy(self):
        with tempfile.TemporaryDirectory(dir=r.W/'.tmp') as raw:
            root=Path(raw);isolated=root/'donor';isolated.mkdir()
            first=isolated/'instruction.md';first.write_text('isolated detailed rules');first.chmod(0o644)
            controller=root/'universe/.config/gewu-multiverse/agents/author-01/instruction.md';controller.parent.mkdir(parents=True);controller.write_text('controller detailed rules');controller.chmod(0o640)
            backup=root/'backup';backup.mkdir();receipt={'reset_id':'one'}
            r.update_instructions(isolated,root/'universe','author-01',backup,receipt,'stalled','preserve files and pivot')
            self.assertEqual(len(receipt['instruction_copies_updated']),2)
            for path,policy,mode in [(first,'isolated detailed rules',0o644),(controller,'controller detailed rules',0o640)]:
                self.assertIn(policy,path.read_text());self.assertIn('Operator reset: one',path.read_text())
                self.assertEqual(path.stat().st_mode&0o777,mode)
            self.assertEqual(len(list(backup.iterdir())),2)
            for path in backup.iterdir():self.assertEqual(path.stat().st_mode&0o777,0o600)
            before=first.read_bytes();controller.unlink();controller.symlink_to(first)
            with self.assertRaises(ValueError):r.update_instructions(isolated,root/'universe','author-01',backup,{'reset_id':'two'},'reason','next')
            self.assertEqual(first.read_bytes(),before)

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
