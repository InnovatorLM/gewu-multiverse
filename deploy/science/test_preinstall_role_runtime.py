import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import subprocess
import preinstall_role_runtime as runtime

class PreinstallTests(unittest.TestCase):
    def test_marker_requires_success_and_is_private(self):
        with tempfile.TemporaryDirectory(dir=runtime.W / ".tmp") as raw:
            root=Path(raw); (root / ".state/universe-maintenance").mkdir(parents=True)
            prefix=root / "home/role/.local/env"; prefix.mkdir(parents=True)
            role=dict(root=str(root),uid=os.getuid(),gid=os.getgid())
            marker=prefix / "gewu-preinstalled-v1.json"
            with patch.object(runtime, "W", root), patch.object(runtime, "run_owned", return_value=subprocess.CompletedProcess([],1,"","failed")):
                with self.assertRaises(RuntimeError): runtime.install_role("author-test",role,install=False)
            self.assertFalse(marker.exists())
            with patch.object(runtime, "W", root), patch.object(runtime, "run_owned", return_value=subprocess.CompletedProcess([],0,"passed","")):
                runtime.install_role("author-test",role,install=False)
            self.assertTrue(json.loads(marker.read_text())["imports_and_cpp_verified"])
            self.assertEqual(marker.stat().st_mode & 0o777,0o600)
            self.assertEqual(marker.stat().st_uid,role["uid"])

if __name__ == "__main__": unittest.main()
