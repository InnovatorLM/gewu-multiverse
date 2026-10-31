import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from evaluation_queue import W
from author_selftest_worker import build_command


class SelftestHarnessTests(unittest.TestCase):
    def test_build_uses_explicit_codex_binaries(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            directory=Path(raw)
            for name in ('codex','rg'):
                binary=directory/name;binary.write_text('test');binary.chmod(0o700)
            with patch.dict(os.environ,GEWU_CODEX_BINARY=str(directory/'codex'),GEWU_RG_BINARY=str(directory/'rg')):
                args=build_command(directory,'a'*40,'task',directory/'output')
            self.assertEqual(args[args.index('--harness')+1],'codex')
            self.assertEqual(args[args.index('--codex-binary')+1],str(directory/'codex'))
            self.assertNotIn('mini-swe-agent',args)

    def test_missing_runtime_fails_before_docker_build(self):
        with patch.dict(os.environ,GEWU_CODEX_BINARY=str(W/'.tmp/nonexistent-runtime-binary')):
            with self.assertRaises(ValueError): build_command(W,'a'*40,'task',W/'.tmp/output')


if __name__ == '__main__': unittest.main()
