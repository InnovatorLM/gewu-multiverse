import os,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import bootstrap_role_environments as m
import preinstall_role_runtime as preinstall

class BootstrapTests(unittest.TestCase):
    def test_role_verification_tmp_is_private_and_workspace_local(self):
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as raw:
            root=Path(raw)/'role-root';env=root/'home/role/.local/env';env.mkdir(parents=True)
            (env/(preinstall.PREINSTALL_VERSION+'.json')).write_text('{}')
            role={'root':str(root),'uid':os.getuid(),'gid':os.getgid()}
            def fake_run(command,**kwargs):
                if command[0]=='chroot':
                    self.assertIn('TMPDIR=/home/role/.cache/gewu-preinstall-tmp',command)
                    self.assertIn('"$TMPDIR/gewu-preinstall.cpp"',command[-1])
                    self.assertNotIn('/tmp/gewu-preinstall',command[-1])
                    return subprocess.CompletedProcess(command,0,'ok','')
            with patch.object(preinstall,'run_owned',side_effect=fake_run):
                preinstall.install_role('fixture',role,install=False)
            tmp=root/'home/role/.cache/gewu-preinstall-tmp'
            self.assertEqual(tmp.stat().st_uid,os.getuid())
            self.assertEqual(tmp.stat().st_mode & 0o777,0o700)

    def test_marker_uses_current_version(self):
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as raw:
            env=Path(raw);(env/'gewu-preinstalled-v1.json').write_text('{}')
            self.assertFalse(m.existing_verified(env))
            (env/(m.PREINSTALL_VERSION+'.json')).write_text('{}')
            self.assertTrue(m.existing_verified(env))

    def test_active_role_cannot_be_replaced(self):
        with patch.object(m,'role_processes',return_value=[123]):
            with self.assertRaises(ValueError):m.require_stopped({'uid':21002})
        with patch.object(m,'role_processes',return_value=[]):m.require_stopped({'uid':21002})

if __name__=='__main__':unittest.main()
