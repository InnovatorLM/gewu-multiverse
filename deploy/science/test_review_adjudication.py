"""Reject transferred audits and unverifiable evidence; never authorize release."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from evaluation_queue import W
from review_adjudication import claim_ids, validate_adjudication


class AdjudicationTests(unittest.TestCase):
    def test_binding_coverage_evidence_and_nonacceptance(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            root=Path(temporary);report=root/'review.json';evidence=root/'calculation.txt'
            data={'snapshot_sha256':'a'*64,'review':{'issues':[{'id':'I1'}],'dimensions':{'science':{}},'suggestions':[{}],'limitations':['not measured']}}
            report.write_text(json.dumps(data));evidence.write_text('deliberate_shift=0.001\n')
            ref={'path':str(evidence.relative_to(W)),'sha256':hashlib.sha256(evidence.read_bytes()).hexdigest(),'quote':'deliberate_shift=0.001'}
            audit={'schema_version':1,'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'snapshot_sha256':'a'*64,'scientific_acceptance':False,'factual_acceptance':False,'operator':'test-operator','decisions':[{'claim_id':key,'verdict':'unresolved','rationale':'Not adjudicated','evidence':[]} for key in sorted(claim_ids(data))]}
            issue=next(x for x in audit['decisions'] if x['claim_id']=='issue:I1');issue.update(verdict='refuted',rationale='The quoted calculation deliberately shifts the expected output.',evidence=[ref])
            result=validate_adjudication(report,audit)
            self.assertEqual(result['claim_counts']['refuted'],1)
            self.assertFalse(result['all_claims_adjudicated'])
            for key in ['scientific_acceptance','factual_acceptance','release_eligible','machine_factual_verification']:self.assertFalse(result[key])
            favorable=copy.deepcopy(audit)
            for item in favorable['decisions']:
                item.update(verdict='supported',rationale='Test operator attestation only',evidence=[ref])
            favorable_result=validate_adjudication(report,favorable)
            self.assertTrue(favorable_result['all_claims_supported'])
            self.assertFalse(favorable_result['release_eligible'])
            self.assertFalse(favorable_result['machine_factual_verification'])
            for kind in ['report','snapshot','missing','duplicate','quote','evidence_hash','acceptance']:
                bad=copy.deepcopy(audit)
                if kind=='report':bad['report_sha256']='0'*64
                elif kind=='snapshot':bad['snapshot_sha256']='0'*64
                elif kind=='missing':bad['decisions'].pop()
                elif kind=='duplicate':bad['decisions'].append(bad['decisions'][0])
                elif kind=='acceptance':bad['scientific_acceptance']=True
                else:
                    item=next(x for x in bad['decisions'] if x['claim_id']=='issue:I1')
                    item['evidence'][0]['quote' if kind=='quote' else 'sha256']='fabricated'
                with self.subTest(kind=kind),self.assertRaises(ValueError):validate_adjudication(report,bad)
            evidence.write_text('replaced calculation\n')
            with self.assertRaises(ValueError):validate_adjudication(report,audit)


if __name__=='__main__':unittest.main()
