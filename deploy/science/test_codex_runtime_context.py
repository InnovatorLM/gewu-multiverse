import tempfile
import unittest
from pathlib import Path
from codex_runtime_context import prepare
from evaluation_queue import W

class RuntimeContextTests(unittest.TestCase):
    def test_binds_actual_versions_and_bytes(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as d:
            root=Path(d)
            for name,text in [('codex','codex-cli 0.164.0'),('rg','ripgrep 14.1.1')]:
                path=root/name;path.write_text('#!/bin/sh\necho "'+text+'"\n');path.chmod(0o755)
            out=root/'context'
            result=prepare(out,'registry/task@sha256:'+'a'*64,root/'codex',root/'rg')
            self.assertEqual(result['runtime_tag'],'codex-0.164.0')
            self.assertEqual(result['harness_versions'],{'codex':'0.164.0','rg':'14.1.1'})
            self.assertEqual(len(result['native_binaries']['codex']['sha256']),64)
            self.assertEqual((out/'codex').read_bytes(),(root/'codex').read_bytes())
            self.assertIn('COPY codex rg',(out/'Dockerfile').read_text())
            with self.assertRaises(ValueError):prepare(out,'registry/task',root/'codex',root/'rg')
    def test_unidentifiable_binary_blocks_build(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as d:
            root=Path(d);path=root/'binary';path.write_text('#!/bin/sh\necho unknown\n');path.chmod(0o755)
            with self.assertRaises(ValueError):prepare(root/'context','registry/task',path,path)
