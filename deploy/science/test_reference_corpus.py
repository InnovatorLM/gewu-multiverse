"""Offline source-pinning checks; no benchmark/model content published."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from evaluation_queue import W
from prepare_reference_corpus import corpus


class CorpusTest(unittest.TestCase):
    def test_commit_content_ignores_dirty_checkout(self):
        with tempfile.TemporaryDirectory(dir=W / '.tmp') as directory:
            repo = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL, text=True).strip()
            git('init')
            git('config', 'user.name', 'Offline Test')
            git('config', 'user.email', 'test@example.invalid')
            path = repo / 'tasks/example/instruction.md'
            path.parent.mkdir(parents=True)
            path.write_text('fixed official content')
            git('add', '.')
            git('commit', '-m', 'fixture')
            commit = git('rev-parse', 'HEAD')
            path.write_text('dirty')
            rows = corpus(repo, commit, 'fixture')
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['instruction'], 'fixed official content')
            self.assertEqual(rows[0]['commit'], commit)
            path.unlink()
            path.symlink_to('/etc/passwd')
            git('add', '.')
            git('commit', '-m', 'invalid link')
            with self.assertRaises(ValueError):
                corpus(repo, git('rev-parse', 'HEAD'), 'fixture')


if __name__ == '__main__':
    unittest.main()
