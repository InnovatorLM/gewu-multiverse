"""Controller-owned credentials need a distinct, private-file guard."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from controller_credentials import load_controller_credentials
from evaluation_queue import W


@unittest.skipUnless(os.geteuid() == 0, 'Operator file guard')
class CredentialsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=W / '.tmp')
        self.root = Path(self.temp.name)
        self.path = self.root / 'universes/my-terminal-bench-science/.config/gewu-multiverse/credentials.toml'
        self.path.parent.mkdir(parents=True, mode=0o700)
        self.path.write_text('forgejo_admin_token = "fixture-only"\n')
        self.path.chmod(0o600)
        self.patch = patch('controller_credentials.W', self.root)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_private_controller_file_read_and_nonoperator_refusal(self):
        self.assertEqual(load_controller_credentials()['forgejo_admin_token'], 'fixture-only')
        with patch('controller_credentials.os.geteuid', return_value=21001):
            with self.assertRaises(ValueError):
                load_controller_credentials()

    def test_public_modes_and_symlink_are_refused(self):
        self.path.chmod(0o644)
        with self.assertRaises(ValueError):
            load_controller_credentials()
        self.path.chmod(0o600)
        self.path.parent.chmod(0o755)
        with self.assertRaises(ValueError):
            load_controller_credentials()
        self.path.parent.chmod(0o700)
        target = self.path.with_name('original.toml')
        self.path.rename(target)
        self.path.symlink_to(target)
        with self.assertRaises(ValueError):
            load_controller_credentials()


if __name__ == '__main__':
    unittest.main()
