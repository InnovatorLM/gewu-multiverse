"""Exercise the actual launcher readiness block without services or model calls."""
import errno
from pathlib import Path
import stat
import sys
from types import SimpleNamespace
import unittest
import subprocess
import tempfile
from unittest.mock import patch


SOURCE = (Path(__file__).parent / 'start-universe').read_text().split("<<'PY_QUEUE_CHECK'\n", 1)[1].split('\nPY_QUEUE_CHECK', 1)[0]
LAUNCHER = (Path(__file__).parent / 'start-universe').read_text()


class ReadyFileTests(unittest.TestCase):
    def test_runtime_keeps_full_instruction_and_skill_manifest_for_every_role(self):
        from evaluation_queue import W
        launcher=Path(__file__).with_name('start-universe-local-runtime').read_text()
        seed=launcher.split('# Seed all configured role instructions,',1)[1].split("<<'PY'\n",1)[1].split('\nPY',1)[0]
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);runtime=root/'runtime';donor=root/'donor'
            broker=runtime/'.state/gewu-multiverse/role-broker/config.json'
            broker.parent.mkdir(parents=True)
            roles=['author-01','author-10','evaluator-03','curator']
            import json
            broker.write_text(json.dumps({'roles':dict.fromkeys(roles,{})}))
            for role in roles:
                source=donor/'.config/gewu-multiverse/agents'/role/'instruction.md'
                source.parent.mkdir(parents=True)
                source.write_text('Full rules '+role+'\n/skills/harbor-acs-evaluation/SKILL.md\n')
            subprocess.run([sys.executable,'-c',seed,str(root/'source'),str(runtime),str(donor)],check=True)
            for role in roles:
                path=Path('.config/gewu-multiverse/agents')/role/'instruction.md'
                self.assertEqual((runtime/path).read_bytes(),(donor/path).read_bytes())
        self.assertNotIn('default-instructions/',launcher)

    def test_runtime_restart_preserves_controller_role_choices(self):
        from evaluation_queue import W
        launcher=Path(__file__).with_name('start-universe-local-runtime').read_text()
        loop=launcher.split('for f in ',1)[1].split('\ndone',1)[0]
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw)
            for name in ('source','donor','runtime'):
                for directory in ('.config/gewu-multiverse','.config/science-evaluation'):
                    (root/name/directory).mkdir(parents=True)
            source=root/'source/.config/gewu-multiverse/multiverse.toml'
            target=root/'runtime/.config/gewu-multiverse/multiverse.toml'
            source.write_text('desired = "stopped"\n')
            script='set -eu\nSOURCE="$1/source"\nDONOR="$1/donor"\nRUNTIME="$1/runtime"\ncopy_control() { cp "$1" "$2"; }\nfor f in '+loop+'\ndone\n'
            subprocess.run(['bash','-c',script,'check',str(root)],check=True)
            self.assertEqual(target.read_text(),source.read_text())
            target.write_text('desired = "started"\n')
            subprocess.run(['bash','-c',script,'check',str(root)],check=True)
            self.assertEqual(target.read_text(),'desired = "started"\n')

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
