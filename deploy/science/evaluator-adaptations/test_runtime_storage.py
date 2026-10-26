import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from unified_evaluator.runtime.core import runtime_root

class RuntimeStorageTests(unittest.TestCase):
    def test_verified_fuse_opt_in_exercises_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory); target=base/'runtime'; task=base/'task'; task.mkdir()
            with patch.dict(os.environ,{'UE_VERIFIED_RUNTIME_ROOT':str(target)}), patch('unified_evaluator.runtime.core.subprocess.check_output',return_value='fuse.aliyun-alinas-efc'):
                self.assertEqual(runtime_root(target,task),target)
                self.assertEqual(list(target.iterdir()),[])
                with self.assertRaisesRegex(ValueError,'does not match'):
                    runtime_root(base/'other',task)

    def test_shared_storage_stays_rejected_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            with patch.dict(os.environ,{'UE_VERIFIED_RUNTIME_ROOT':''}), patch('unified_evaluator.runtime.core.subprocess.check_output',return_value='fuse.aliyun-alinas-efc'):
                with self.assertRaisesRegex(ValueError,'local filesystem'):
                    runtime_root(base/'runtime',base/'task')

    def test_runtime_must_not_be_inside_task(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            with self.assertRaisesRegex(ValueError,'outside task_dir'):
                runtime_root(base/'runtime',base)
