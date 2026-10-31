"""Offline immutable snapshot/provenance boundary checks; no model calls."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import argparse
import json
import os
import hashlib
from unittest.mock import patch
import register_evaluation as registration

from evaluation_queue import W, digest_tree
from register_evaluation import freeze


class RegistrationTest(unittest.TestCase):
    def test_registration_bridges_execution_identity_without_relabeling(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);settings=root/'.config/science-evaluation';settings.mkdir(parents=True)
            state=root/'state';(state/'registered').mkdir(parents=True)
            inbox=root/'evaluation/inbox';inbox.mkdir(parents=True)
            registry=settings/'registry.json';registry.write_text('{}')
            (settings/'queue.json').write_text(json.dumps(dict(state=str(state),registry=str(registry),inbox=str(inbox),evaluator_uid=os.getgid())))
            template=root/'template.json';template.write_text('{}')
            receipt=root/'receipt.json';receipt.write_text('{"original_image_labels":true}')
            args=argparse.Namespace(evaluation_id='bridge-test',repo=str(root),commit='a'*40,task_path='tasks/proof',template=str(template),build_receipt=str(receipt),disabled=False,selftest_work=root/'selftest')
            bridge=dict(snapshot_sha256='b'*64,build_receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),execution_commit='c'*40,execution_task_path='proof',iteration_qualified=False)
            def freeze_fixture(repo,commit,task,destination):
                destination.mkdir();return 'b'*64
            with patch.dict(os.environ,GEWU_UNIVERSE_ROOT=str(root)), \
                 patch('argparse.ArgumentParser.parse_args',return_value=args), \
                 patch.object(registration,'freeze',side_effect=freeze_fixture), \
                 patch.object(registration,'inspect_task',return_value={}), \
                 patch.object(registration,'validated_template'), \
                 patch('selftest_registration.prepare',return_value=bridge) as prepare, \
                 patch('build_task_images.validate_build_receipt') as validate:
                registration.main()
                prepare.assert_called_once()
                self.assertEqual(validate.call_args.args[2:4],('c'*40,'proof'))
            entry=json.loads(registry.read_text())['bridge-test']
            self.assertEqual(entry['source_commit'],'a'*40)
            parent=state/'registered/bridge-test'
            self.assertEqual(json.loads((parent/'selftest-binding.json').read_text()),bridge)
            self.assertEqual((parent/'build-receipt.json').read_text().strip(),'{\n  "original_image_labels": true\n}')

    def test_frozen_commit_and_rejections(self):
        with tempfile.TemporaryDirectory(dir=W / '.tmp') as temporary:
            base = Path(temporary)
            repo = base / 'repo'
            repo.mkdir()
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL, text=True).strip()
            git('init')
            git('config', 'user.name', 'Offline Test')
            git('config', 'user.email', 'test@example.invalid')
            for name in ['instruction.md', 'task.toml', 'environment/Dockerfile', 'tests/test.sh', 'solution/solve.sh']:
                path = repo / 'task' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('original\n')
            git('add', '.')
            git('commit', '-m', 'fixture')
            commit = git('rev-parse', 'HEAD')
            (repo / 'task/instruction.md').write_text('uncommitted change')
            target = base / 'frozen'
            sha = freeze(repo, commit, 'task', target)
            self.assertEqual((target / 'instruction.md').read_text(), 'original\n')
            self.assertEqual(sha, digest_tree(target))
            with self.assertRaises(ValueError):
                freeze(repo, 'HEAD', 'task', base / 'mutable')
            with self.assertRaises(ValueError):
                freeze(repo, commit, '../task', base / 'traversal')
            (repo / 'task/link').symlink_to('/etc/passwd')
            git('add', '.')
            git('commit', '-m', 'link')
            with self.assertRaises(ValueError):
                freeze(repo, git('rev-parse', 'HEAD'), 'task', base / 'linked')
            self.assertFalse((base / 'linked').exists())
            with self.assertRaises(FileExistsError):
                freeze(repo, commit, 'task', target)


if __name__ == '__main__':
    unittest.main()
