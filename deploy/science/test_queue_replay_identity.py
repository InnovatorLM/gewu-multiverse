"""A repeated job ID must not relabel evidence to another candidate/hash."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from evaluation_queue import W,process


@unittest.skipUnless(os.geteuid()==0,'role-owned request fixture required')
class ReplayTests(unittest.TestCase):
    def test_replay_requires_original_claim_and_result_identity(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            root=Path(temporary)
            for name in ['state','results','inbox']:(root/name).mkdir()
            jobid='a'*32;request={'job_id':jobid,'evaluation_id':'candidate-v1','snapshot_sha256':'b'*64}
            job=root/'state'/jobid;job.mkdir()
            claim=job/'claim.json';claim.write_text(json.dumps({**request,'mock':False}));claim.chmod(0o600)
            answer={**request,'status':'solver_complete','cleanup_confirmed':True,'quality_acceptance':False}
            result=job/'result.json';result.write_text(json.dumps(answer))
            path=root/'inbox'/(jobid+'.json');path.write_text(json.dumps(request));os.chown(path,21002,21002)
            cfg={'state':str(root/'state'),'results':str(root/'results'),'evaluator_uid':21002}
            self.assertEqual(process(cfg,path),answer)
            public=root/'results'/(jobid+'.json');original=public.read_bytes()
            for field,value in [('evaluation_id','foreign-candidate'),('snapshot_sha256','c'*64)]:
                path.write_text(json.dumps({**request,field:value}))
                with self.subTest(field=field),self.assertRaises(ValueError):process(cfg,path)
                self.assertEqual(public.read_bytes(),original)
            path.write_text(json.dumps(request));result.write_text(json.dumps({**answer,'snapshot_sha256':'d'*64}))
            with self.assertRaises(ValueError):process(cfg,path)
            self.assertEqual(public.read_bytes(),original)
            result.unlink();interrupted=process(cfg,path)
            self.assertEqual(interrupted['status'],'interrupted');self.assertFalse(interrupted['cleanup_confirmed'])


if __name__=='__main__':unittest.main()
