from pathlib import Path
import tempfile
import unittest
from evaluation_queue import W
from task_quality_policy import install, BEGIN


class PolicyTests(unittest.TestCase):
    def test_all_author_reviewer_views_updated_idempotently(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);roles={}
            for role in ['author-01','evaluator-01']:
                isolated=root/role;isolated.mkdir();(isolated/'instruction.md').write_text('existing detailed rules')
                controller=root/'.config/gewu-multiverse/agents'/role/'instruction.md'
                controller.parent.mkdir(parents=True);controller.write_text('existing detailed rules')
                roles[role]={'root':str(isolated)}
            cfg={'roles':roles}
            install(cfg,root);install(cfg,root)
            for path in root.rglob('instruction.md'):
                text=path.read_text();self.assertEqual(text.count(BEGIN),1)
                for rule in ['80%','至少四次','真实论文','完全虚构','特别突出','existing detailed rules']:
                    self.assertIn(rule,text)


if __name__=='__main__':unittest.main()
