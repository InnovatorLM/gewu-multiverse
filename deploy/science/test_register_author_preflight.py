import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import author_submission_gate as gate
import register_author_preflight as m


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=gate.W / '.tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.override = patch.object(gate, 'W', self.root)
        self.override.start(); self.addCleanup(self.override.stop)
        self.universe_override=patch.object(gate,'universe_root',return_value=self.root)
        self.universe_override.start();self.addCleanup(self.universe_override.stop)
        self.evidence = self.root / 'evidence.json'
        self.evidence.write_text('{"fixture":true}')
        self.evidence.chmod(0o600)
        self.commit = 'a' * 40; self.task = 'tasks/example'
        self.receipt = dict(commit=self.commit, task=self.task,
            snapshot_sha256='b' * 64, runtime_image='registry/ns/task@sha256:' + 'c' * 64,
            checks={name: True for name in gate.CHECKS}, pre_submission_order=list(gate.REQUIRED_ORDER),
            iteration_applied=True, active_iteration_seconds=12, difficulty_viable=True,
            evidence_files=[dict(path=str(self.evidence), sha256=hashlib.sha256(self.evidence.read_bytes()).hexdigest())])
        self.source = self.root / 'receipt.json'
        self.save()

    def save(self):
        self.source.write_text(json.dumps(self.receipt)); self.source.chmod(0o600)

    def test_preview_does_not_grant_eligibility(self):
        result = m.register(self.source, self.commit, self.task)
        self.assertFalse(result['applied'])
        self.assertFalse(gate.approved(self.commit, self.task))
        self.assertFalse((self.root / '.state').exists())

    def test_published_receipt_is_consumed_by_gate_and_cannot_be_overwritten(self):
        before = self.source.read_bytes()
        result = m.register(self.source, self.commit, self.task, apply=True)
        path = Path(result['destination'])
        self.assertTrue(gate.approved(self.commit, self.task))
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.source.read_bytes(), before)
        registered = path.read_bytes()
        with self.assertRaises(FileExistsError): m.register(self.source, self.commit, self.task, apply=True)
        self.assertEqual(path.read_bytes(), registered)
        self.assertFalse(list(path.parent.glob('.register-*')))
        self.evidence.write_text('changed')
        with self.assertRaises(ValueError): gate.approved(self.commit, self.task)

    def test_missing_selfsolve_is_never_inferred_from_other_checks(self):
        self.receipt['checks']['author_solve'] = False; self.save()
        with self.assertRaises(ValueError): m.register(self.source, self.commit, self.task, apply=True)
        self.assertFalse(gate.approved(self.commit, self.task))

    def test_role_identity_cannot_register(self):
        with patch.object(m.os, 'geteuid', return_value=21002):
            with self.assertRaises(PermissionError): m.register(self.source, self.commit, self.task, apply=True)

    def test_registry_symlink_is_rejected(self):
        state=self.root/'.state'; state.mkdir()
        other=self.root/'other'; other.mkdir(mode=0o700)
        (state/'science-author-preflight').symlink_to(other,target_is_directory=True)
        with self.assertRaises(ValueError):m.register(self.source,self.commit,self.task,apply=True)
        self.assertEqual(list(other.iterdir()),[])


if __name__ == '__main__': unittest.main()
