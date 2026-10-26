"""Installed schema and shell parsing without executing candidate code."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from evaluation_queue import W, digest_tree
from check_harbor_task import inspect_task, validate_mechanical_check


class MechanicalTests(unittest.TestCase):
    def test_mechanical_receipt_cannot_be_reused_or_changed(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            root=Path(temporary);task=root/'task';task.mkdir();(task/'input').write_text('original')
            report={'snapshot_sha256':digest_tree(task),'schema_parsed':True,'required_files_nonempty':True,'shell_syntax_valid':True,'task_code_executed':False,'scientific_acceptance':False}
            path=root/'mechanical-check.json';path.write_text(json.dumps(report));sha=hashlib.sha256(path.read_bytes()).hexdigest()
            validate_mechanical_check(path,task,sha)
            (task/'input').write_text('changed')
            with self.assertRaises(ValueError):validate_mechanical_check(path,task,sha)
            (task/'input').write_text('original');path.write_text(json.dumps({**report,'scientific_acceptance':True}))
            with self.assertRaises(ValueError):validate_mechanical_check(path,task,sha)

    def test_real_schema_and_nonexecution(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            task=Path(temporary);sentinel=task/'must-not-exist'
            contents={'instruction.md':'Write a result.','task.toml':'schema_version="1.0"\n[environment]\ncpus=2\nmemory_mb=4096\n','environment/Dockerfile':'FROM scratch\n','tests/test.sh':'#!/bin/bash\ntouch '+str(sentinel)+'\n','solution/solve.sh':'#!/bin/sh\nexit 0\n'}
            for name,text in contents.items():
                path=task/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
            report=inspect_task(task)
            self.assertTrue(report['schema_parsed']);self.assertTrue(report['shell_syntax_valid']);self.assertFalse(report['scientific_acceptance']);self.assertFalse(sentinel.exists())
            self.assertEqual(report['schema_resolved_resources']['memory_mb'],4096)
            for text in ['[agent]\ntimeout_sec="not-a-number"\n','[verifier]\ntimeout_sec=-1\n','[environment]\ncpus=-2\n']:
                (task/'task.toml').write_text(text)
                with self.subTest(config=text),self.assertRaises(ValueError):inspect_task(task)
            (task/'task.toml').write_text(contents['task.toml']);(task/'tests/test.sh').write_text('if then\n')
            with self.assertRaises(ValueError):inspect_task(task)
            (task/'tests/test.sh').write_text(contents['tests/test.sh']);(task/'instruction.md').write_text('')
            with self.assertRaises(ValueError):inspect_task(task)
            self.assertFalse(sentinel.exists())


if __name__=='__main__':unittest.main()
