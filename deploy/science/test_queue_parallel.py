import os
import json
import subprocess
from unittest.mock import patch
from pathlib import Path
import sys
import tempfile
import time
import unittest
from evaluation_queue import W, active_queue_worker, process
from queue_parallel import ActiveJobs


class ParallelTests(unittest.TestCase):
    def test_five_real_processes_overlap_and_duplicates_do_not_start(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);pool=ActiveJobs(5)
            script='''import pathlib,sys,time
root=pathlib.Path(sys.argv[1]);key=sys.argv[2]
(root/(key+'.ready')).touch()
while not (root/'release').exists():time.sleep(.02)
(root/(key+'.done')).touch()
'''
            try:
                for i in range(5):
                    self.assertTrue(pool.start(str(i),[sys.executable,'-c',script,str(root),str(i)]))
                self.assertFalse(pool.start('0',[sys.executable,'-c','raise Exception()']))
                self.assertFalse(pool.start('6',[sys.executable,'-c','raise Exception()']))
                deadline=time.monotonic()+15
                while len(list(root.glob('*.ready')))<5 and time.monotonic()<deadline:time.sleep(.05)
                self.assertEqual(len(list(root.glob('*.ready'))),5)
                self.assertTrue(all(child.poll() is None for child in pool.children.values()))
                (root/'release').touch()
                while pool.children and time.monotonic()<deadline:pool.reap();time.sleep(.05)
                self.assertEqual(len(list(root.glob('*.done'))),5)
                self.assertFalse(pool.children)
            finally:pool.stop()

    def test_active_sibling_allowed_but_unclean_or_dead_sibling_blocks(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw)
            for name in ['state','results','inbox']:(root/name).mkdir()
            prior='a'*32;job=root/'state'/prior;job.mkdir()
            worker=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)',
                str(Path(__file__).with_name('evaluation_queue.py').resolve()),
                '--single-request',str(root/'inbox'/(prior+'.json')),'--queue-index','0'])
            try:
                claim={'queue_worker_pid':worker.pid,'day':'2026-10-31'}
                (job/'claim.json').write_text(json.dumps(claim));(job/'claim.json').chmod(0o600)
                registry=root/'registry.json';registry.write_text(json.dumps({'candidate':{'dispatch':'solver'}}));registry.chmod(0o600)
                cfg=dict(state=str(root/'state'),results=str(root/'results'),registry=str(registry),evaluator_uid=21002,max_jobs_per_day=0)
                def request(key):
                    path=root/'inbox'/(key*32+'.json')
                    path.write_text(json.dumps(dict(job_id=key*32,evaluation_id='candidate',snapshot_sha256='b'*64)))
                    os.chown(path,21002,21002)
                    return path
                with patch('evaluation_queue.validated_template',return_value={}):
                    self.assertEqual(process(cfg,request('b'),mock=True)['status'],'mock_complete')
                    (job/'result.json').write_text('{"cleanup_confirmed":false}')
                    with self.assertRaisesRegex(ValueError,'cleanup is not confirmed'):process(cfg,request('c'),mock=True)
                    (job/'result.json').unlink();worker.terminate();worker.wait()
                    with self.assertRaisesRegex(ValueError,'cleanup is not confirmed'):process(cfg,request('d'),mock=True)
            finally:
                if worker.poll() is None:worker.terminate()
                worker.wait()

    def test_arbitrary_live_pid_is_not_a_queue_worker(self):
        self.assertFalse(active_queue_worker({'queue_worker_pid':os.getpid()},'a'*32))
        self.assertFalse(active_queue_worker({'queue_worker_pid':999999999},'a'*32))


if __name__=='__main__':unittest.main()
