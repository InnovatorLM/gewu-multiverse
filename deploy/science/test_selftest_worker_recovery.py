"""Exercise recovery through the worker and its real role-visible receipt."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation_queue import W
import author_selftest_worker as worker


class WorkerRecoveryTests(unittest.TestCase):
    def test_interrupted_upload_publishes_once_without_restarting_cloud_work(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);state=root/'state';role=root/'role'
            job='a'*32;work=state/job;work.mkdir(parents=True)
            (role/'selftest/results').mkdir(parents=True)
            (work/'upload.tar').write_bytes(b'preserved evidence')
            request=role/'selftest/inbox'/(job+'.json')
            receipt=role/'selftest/results'/(job+'.json')
            entry={'root':str(role),'uid':os.getuid(),'gid':os.getgid()}
            with patch.object(worker,'STATE',state),patch.object(worker,'owned_run') as run:
                worker.process('author-01',entry,request)
                first=receipt.read_bytes()
                worker.process('author-01',entry,request)
                run.assert_not_called()
            status=json.loads(first)
            self.assertEqual(status['status'],'interrupted')
            self.assertIs(status['quality_acceptance'],False)
            self.assertEqual(receipt.read_bytes(),first)
            self.assertEqual(receipt.stat().st_mode & 0o777,0o640)
            self.assertEqual((work/'upload.tar').read_bytes(),b'preserved evidence')


if __name__=='__main__':unittest.main()
