"""Credential-free secret-scan checks; no model or Kubernetes calls."""
import base64
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from finalize_acs_quality import scan_evidence
from evaluation_queue import W


class ScanTests(unittest.TestCase):
    def test_outputs_guard_and_upload_are_all_scanned(self):
        secret = b'FAKE-CREDENTIAL-FOR-TEST'
        with tempfile.TemporaryDirectory(dir=W / '.tmp') as temp:
            root = Path(temp) / 'outputs'
            root.mkdir()
            output = root / 'trace.json'
            output.write_bytes(base64.b64encode(secret))
            output.chmod(0o600)
            archive = Path(temp) / 'input.tar.gz'
            with tarfile.open(archive, 'w:gz') as bundle:
                entry = tarfile.TarInfo('config.json')
                entry.size = len(secret)
                bundle.addfile(entry, io.BytesIO(secret))
            patterns = {'fake': secret, 'fake_base64': base64.b64encode(secret)}
            findings, records, count = scan_evidence(root, archive, secret, patterns)
            self.assertEqual({item['path'] for item in findings}, {'guard-report', 'trace.json', 'input:config.json'})
            self.assertEqual(count, 1)
            self.assertEqual(len(records), 1)
            self.assertNotIn(secret.decode(), str(findings))

    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory(dir=W / '.tmp') as temp:
            root = Path(temp)
            (root / 'link').symlink_to('/etc/passwd')
            with self.assertRaisesRegex(ValueError, 'link'):
                scan_evidence(root, root / 'unused', b'', {'fake': b'fake-secret'})


if __name__ == '__main__':
    unittest.main()
