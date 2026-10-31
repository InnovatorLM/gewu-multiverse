import tempfile,unittest
from pathlib import Path
from install_role_skills import install,BEGIN
W=Path('/mnt/data/zhanglinfeng/workspace')
class ProvisionTests(unittest.TestCase):
    def test_roles_discovery_and_idempotence(self):
        for role,count in [('author-04',1),('evaluator-01',2),('curator',1)]:
            with tempfile.TemporaryDirectory(dir=W/'.tmp') as d:
                root=Path(d);(root/'instruction.md').write_text('Original instructions')
                names=install(root,role,owner=None);install(root,role,owner=None)
                self.assertEqual(len(names),count)
                self.assertEqual((root/'instruction.md').read_text().count(BEGIN),1)
                for n in names:self.assertTrue((root/'skills'/n/'SKILL.md').is_file())
                if role=='curator':self.assertNotIn('acs-quality-rollout-review',names)
    def test_initializer_calls_installer(self):
        self.assertIn('install_skills(root, role)',Path(__file__).with_name('prepare_role_runtime.py').read_text())
