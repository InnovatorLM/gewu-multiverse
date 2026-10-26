"""A green-looking model report cannot become scientific acceptance."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from evaluation_queue import W
from review_diagnostic_status import diagnostic_status


@unittest.skipUnless(os.geteuid()==0,'operator-owned evidence required')
class DiagnosticTests(unittest.TestCase):
    def test_high_score_and_no_blocker_remain_nonacceptance(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            root=Path(temporary)
            report={'scientific_acceptance':False,'factual_acceptance':False,'snapshot_sha256':'a'*64,'review':{'quality_score':100,'gate':{'status':'no_blocker_found'}}}
            (root/'review.json').write_text(json.dumps(report))
            status=diagnostic_status(root)
            self.assertEqual(status['state'],'diagnostic_unverified')
            for flag in ['scientific_acceptance','quality_acceptance','release_eligible','role_queue_dispatch_verified']:self.assertFalse(status[flag])
            (root/'factual-audit.json').write_text(json.dumps({'factual_acceptance':False,'scientific_acceptance':False}))
            status=diagnostic_status(root)
            self.assertEqual(status['state'],'diagnostic_audited')
            self.assertFalse(status['release_eligible'])
            report['scientific_acceptance']=True
            (root/'review.json').write_text(json.dumps(report))
            with self.assertRaises(ValueError):diagnostic_status(root)


if __name__=='__main__':unittest.main()
