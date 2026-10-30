import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import bootstrap_role_environments as m

class BootstrapTests(unittest.TestCase):
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
