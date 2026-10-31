"""Offline final-verifier gates; subprocesses are mocked, no Universe restart."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import verify_storage_recovery as verifier

class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=verifier.W/'.tmp')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'.state/science-role-broker').mkdir(parents=True)
        (self.root/'.state/universe-maintenance').mkdir()
        role=self.root/'role'
        self.marker=role/'home/role/.local/env/gewu-preinstalled-v1.json'
        self.marker.parent.mkdir(parents=True)
        cfg={'roles':{'author-01':{'root':str(role),'uid':os.getuid()}}}
        (self.root/'.state/science-role-broker/config.json').write_text(json.dumps(cfg))

    def run_verifier(self):
        with patch.object(verifier,'W',self.root),patch.object(verifier,'process_identity',side_effect=['start',None]),patch('sys.argv',['verify','--recovery-pid','123']),patch.object(verifier.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run:
            try:verifier.main()
            except SystemExit:pass
        report=json.loads((self.root/'.state/storage-investigation/recovery-verification.json').read_text())
        return report,run.call_count

    def test_missing_marker_blocks_all_final_checks(self):
        report,calls=self.run_verifier()
        self.assertFalse(report['passed'])
        self.assertEqual(report['state'],'failed')
        self.assertEqual(calls,0)

    def test_valid_marker_still_requires_both_final_checks(self):
        self.marker.write_text('{"imports_and_cpp_verified":true}')
        self.marker.chmod(0o600)
        report,calls=self.run_verifier()
        self.assertTrue(report['passed'])
        self.assertEqual(calls,2)

if __name__=='__main__':unittest.main()
