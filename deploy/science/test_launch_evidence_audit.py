"""An actual stale catalog must not be replaced by inferred registry state."""
import unittest
from evaluation_queue import evaluation_catalog
from launch_evidence_audit import catalog_status


class CatalogAuditTests(unittest.TestCase):
    def test_stale_disabled_entry_is_reported_as_visible(self):
        registry={'candidate':{'enabled':False,'snapshot_sha256':'a'*64}}
        self.assertTrue(catalog_status(registry,evaluation_catalog(registry))['published_matches_current_registry'])
        stale=evaluation_catalog({'candidate':{'enabled':True,'snapshot_sha256':'a'*64}})
        status=catalog_status(registry,stale)
        self.assertFalse(status['published_matches_current_registry'])
        self.assertIn('candidate',status['visible_evaluation_ids'])

    def test_changed_hash_and_duplicate_are_not_valid(self):
        registry={'candidate':{'enabled':True,'snapshot_sha256':'a'*64}}
        stale=evaluation_catalog(registry);stale['evaluations'][0]['snapshot_sha256']='b'*64
        self.assertFalse(catalog_status(registry,stale)['published_matches_current_registry'])
        stale['evaluations']*=2
        with self.assertRaises(ValueError):catalog_status(registry,stale)


if __name__=='__main__':unittest.main()
