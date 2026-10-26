"""Offline immutable snapshot/provenance boundary checks; no model calls."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from evaluation_queue import W, digest_tree
from register_evaluation import freeze


class RegistrationTest(unittest.TestCase):
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
