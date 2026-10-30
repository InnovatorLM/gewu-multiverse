"""Version changes and caller-authored green gates must not become approvals."""
import copy
import unittest
from unittest.mock import patch
from prepare_review_packet import validate,GATES


class PacketTests(unittest.TestCase):
    def test_removed_user_requirements_cannot_reappear_as_admission_gates(self):
        for removed in ('source_and_license','semantic_comparison_both_benchmarks','first_pilot_user_approval'):
            self.assertNotIn(removed,GATES)
        self.assertIn('source_provenance',GATES)
        self.assertIn('independent_reference_and_negative_controls',GATES)
        self.assertIn('empirical_difficulty',GATES)

    def packet(self):
        return {'schema_version':1,'kind':'private_review_inventory','evaluation_id':'test',
          'source_commit':'a'*40,'source_task_path':'tasks/test','snapshot_sha256':'b'*64,
          'registered_template_sha256':'c'*64,'registered_enabled':False,'images':{},'evidence_inventory':{},
          'gates':{'scientific_suitability':{'status':'not_adjudicated','evidence':[]}},
          **{k:False for k in ('scientific_acceptance','release_eligible','approval_authenticated','raw_evidence_included','safe_for_publication')}}

    def test_stale_sources_images_and_evidence_refused(self):
        p=self.packet()
        with patch('prepare_review_packet.prepare',return_value=p):
            self.assertTrue(validate(p))
            for key in ('source_commit','snapshot_sha256','registered_template_sha256','registered_enabled','images','evidence_inventory'):
                bad=copy.deepcopy(p);bad[key]='changed'
                with self.subTest(key=key),self.assertRaises(ValueError):validate(bad)

    def test_inventory_cannot_greenlight_or_claim_safe_sharing(self):
        p=self.packet()
        with patch('prepare_review_packet.prepare',return_value=p):
            for key in ('scientific_acceptance','release_eligible','approval_authenticated','raw_evidence_included','safe_for_publication'):
                bad=copy.deepcopy(p);bad[key]=True
                with self.subTest(key=key),self.assertRaises(ValueError):validate(bad)
            bad=copy.deepcopy(p);bad['gates']['scientific_suitability']['status']='pass'
            with self.assertRaises(ValueError):validate(bad)


if __name__=='__main__':unittest.main()
