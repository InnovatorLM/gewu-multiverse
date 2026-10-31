"""An actual stale catalog must not be replaced by inferred registry state."""
import unittest
import os
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from evaluation_queue import evaluation_catalog
from launch_evidence_audit import catalog_status, phase_requirements, role_session_budget


class CatalogAuditTests(unittest.TestCase):
    def test_historical_counts_are_observable_without_enforcing_a_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            now=datetime(2026,10,26,23,59,tzinfo=timezone.utc)
            for name,stamp in [('failed',now.timestamp()),('prepared',now.timestamp()),('future',now.timestamp()+86400),('yesterday',now.timestamp()-86400)]:
                plan=root/'evaluator'/name/'plan.json';plan.parent.mkdir(parents=True)
                plan.write_text('{}');os.utime(plan,(stamp,stamp))
            launcher='export GEWU_DAILY_ROLE_SESSIONS=3\n'
            current=role_session_budget(root,launcher,now)
            self.assertEqual(current['roles']['evaluator'],{'prepared_today':3,'remaining':None})
            self.assertIsNone(current['roles']['author']['remaining'])
            self.assertFalse(current['enforced'])
            next_day=datetime(2026,10,27,0,1,tzinfo=timezone.utc)
            self.assertEqual(role_session_budget(root,launcher,next_day)['roles']['evaluator']['prepared_today'],1)

    def test_legacy_environment_does_not_restore_removed_limit(self):
        for text in ['', 'export GEWU_DAILY_ROLE_SESSIONS=3\n']:
            report=role_session_budget(Path('/unused'),text,datetime.now(timezone.utc))
            self.assertFalse(report['enforced'])
            self.assertIsNone(report['configured_per_role'])

    def test_first_task_admission_is_not_author_startup(self):
        phases=phase_requirements()
        self.assertIs(phases['author_proposal']['qualified_first_task_required'],False)
        self.assertEqual(phases['author_proposal']['readiness'],'requires_current_preflight')
        self.assertIs(phases['first_task_admission']['qualified_first_task_required'],True)

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
