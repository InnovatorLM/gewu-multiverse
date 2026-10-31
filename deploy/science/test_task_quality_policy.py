from pathlib import Path
import tempfile
import unittest
from evaluation_queue import W
from task_quality_policy import install, update, BEGIN


class PolicyTests(unittest.TestCase):
    def test_superseded_body_requirements_are_removed_not_only_overridden(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            p=Path(raw)/'instruction.md'
            p.write_text('A. 来源与许可、与现有任务区别、风险。\nB. 提案通过后实现 Harbor 题目。\n理想目标是正确率低于 30%；这是困难目标而不是硬性淘汰线，整体正确率低于 50% 可以接受。\n真实容器自测和完整性检查。')
            update(p);first=p.read_text();update(p)
            self.assertEqual(first,p.read_text())
            for old in ['来源与许可','与现有任务区别','提案通过后','低于 50%','低于 30%']:
                self.assertNotIn(old,first)
            self.assertIn('无需等待人工提案批准',first)
            self.assertIn('真实容器自测和完整性检查',first)
            self.assertIn('大于等于80%严格拒绝',first)

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
