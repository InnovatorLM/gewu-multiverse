import json,os,subprocess,tempfile,unittest
from pathlib import Path
from role_capabilities import W,inspect,MODULES,TOOLS
from install_role_skills import selected

class CapabilityTests(unittest.TestCase):
    def fixture(self,root):
        for name in selected('author-01'):
            path=root/'skills'/name/'SKILL.md';path.parent.mkdir(parents=True);path.write_text('skill')
        (root/'instruction.md').write_text('policy')
        for name in ['home/role/.local/env/bin/python','usr/local/bin/role-acs-selftest']:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.touch()
        return dict(root=str(root),uid=21001,gid=21001)

    def test_checks_identity_and_reports_missing_dependencies(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            entry=self.fixture(Path(raw))
            payload=dict(uid=21001,modules={k:{'ok':True} for k in MODULES},tools={k:'/usr/bin/'+k for k in TOOLS})
            def run(args,**kwargs):
                self.assertIn('--userspec=21001:21001',args)
                return subprocess.CompletedProcess(args,0,json.dumps(payload),'')
            receipt=inspect('author-01',entry,run);self.assertTrue(receipt['ready'])
            payload['modules']['numpy']['ok']=False
            self.assertFalse(inspect('author-01',entry,run)['ready'])
            payload['modules'].pop('numpy')
            with self.assertRaisesRegex(ValueError,'Incomplete'):inspect('author-01',entry,run)
            payload['uid']=0
            with self.assertRaises(ValueError):inspect('author-01',entry,run)

    def test_no_raw_probe_error_is_exposed(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            entry=self.fixture(Path(raw))
            with self.assertRaisesRegex(ValueError,'no raw output'):
                inspect('author-01',entry,lambda *a,**k:subprocess.CompletedProcess([],1,'secret','secret'))

if __name__=='__main__':unittest.main()
