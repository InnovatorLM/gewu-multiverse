import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from deployment_paths import universe_root,WORKSPACE

class DeploymentTests(unittest.TestCase):
    def test_launcher_rejects_invalid_root_before_starting_services(self):
        env=dict(os.environ,GEWU_UNIVERSE_ROOT='/root/disallowed-universe')
        result=subprocess.run(['bash',str(Path(__file__).with_name('start-universe'))],env=env,capture_output=True,text=True,timeout=10)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Universe root must be an absolute directory below workspace',result.stderr)

    def test_default_and_explicit_replacement_are_distinct(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/'.tmp') as raw:
            root=Path(raw)
            with patch.dict(os.environ,{},clear=True):
                self.assertEqual(universe_root(root),root/'universes/my-terminal-bench-science')
            with patch.dict(os.environ,GEWU_UNIVERSE_ROOT=str(root/'universes/replacement')):
                self.assertEqual(universe_root(root),root/'universes/replacement')

    def test_outside_relative_and_workspace_itself_are_refused(self):
        for value in ('relative','/root/new-universe',str(WORKSPACE)):
            with self.subTest(value=value),patch.dict(os.environ,GEWU_UNIVERSE_ROOT=value),self.assertRaises(ValueError):
                universe_root()
