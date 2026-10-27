import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('receipt', Path(__file__).with_name('read_unified_quality_receipt.py'))
receipt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receipt)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=receipt.W / '.tmp')
        self.root = Path(self.temp.name)
        self.run_id = 'qa-live-0123456789'
        self.run = self.root / self.run_id
        (self.run / 'output').mkdir(parents=True)
        self.patch = patch.object(receipt, 'STATE', self.root)
        self.patch.start()
        self.source = receipt.SOURCE / 'unified_evaluator/pipelines/quality_review/review.py'
        self.manifest = {'run_id': self.run_id, 'task': 'public-task', 'files': [
            {'path': 'source/' + p.relative_to(receipt.SOURCE).as_posix(),
             'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted((receipt.SOURCE / 'unified_evaluator').rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']}
        self.report = {'run_id': self.run_id, 'evidence_dir': str(self.run),
                       'controller_exit_code': 0,
                       'result': {'exit_code': 0, 'valid_review_exists': True,
                                  'task_unchanged': True, 'provider': 'dawnfm',
                                  'endpoint': 'https://dawnfm.gravarc.cn/v1',
                                  'model': 'deepseek-v4.1-flash-1017',
                                  'secret_findings_before_redaction': []},
                       'cleanup': {'confirmed': True, 'known_pod_404': True,
                                   'two_snapshots': [dict.fromkeys(['pods', 'sandboxsets', 'sandboxclaims', 'sandboxes'], []) for _ in range(2)]}}
        self.review = {'task_id': 'public-task', 'summary': 'Static fixture; not a live review.',
                       'dimensions': {k: {'score': 2, 'reason': 'Fixture evidence.'} for k in ['science', 'contract', 'verifier', 'integrity', 'research_work', 'feasibility']},
                       'gate': {'status': 'no_blocker_found', 'reason': 'Fixture only.'},
                       'difficulty': {'level': 2, 'confounded': True, 'reason': 'Fixture only.'},
                       'issues': [], 'suggestions': [], 'limitations': ['Fixture only.'],
                       'quality_score': 50, 'coverage': 1, 'score_range': [50, 50],
                       'review_metadata': {'model': 'deepseek-v4.1-flash-1017', 'successful_shell_commands': 2,
                                           'workspace': str(receipt.W / '.state/private/task'),
                                           'usage': {'input_tokens': 1}}}
        self.review_path = self.run / 'output/review.json'
        self.write(self.review_path, self.review)
        self.audit = {'run_id': self.run_id, 'findings': [], 'secret_encodings_checked': 10,
                      'review_sha256': hashlib.sha256(self.review_path.read_bytes()).hexdigest()}
        self.save()

    def write(self, path, value):
        path.write_text(json.dumps(value)); path.chmod(0o600)

    def save(self):
        self.write(self.root / ('acs-quality-live-' + self.run_id + '.json'), self.report)
        self.write(self.root / ('quality-live-input-manifest-' + self.run_id + '.json'), self.manifest)
        report_path = self.root / ('acs-quality-live-' + self.run_id + '.json')
        self.audit['guard_report_sha256'] = hashlib.sha256(report_path.read_bytes()).hexdigest()
        self.write(self.run / 'exact-secret-audit.json', self.audit)

    def tearDown(self):
        self.patch.stop(); self.temp.cleanup()

    def test_valid_diagnostic_cannot_grant_acceptance_or_export_metadata(self):
        self.review['summary'] = self.review['review_metadata']['workspace'] + '/instruction.md'
        self.write(self.review_path, self.review)
        self.audit['review_sha256'] = hashlib.sha256(self.review_path.read_bytes()).hexdigest()
        self.save()
        result = receipt.validate(self.run_id)
        self.assertEqual(result['review']['summary'], '/task/instruction.md')
        self.assertFalse(result['scientific_acceptance'])
        self.assertFalse(result['quality_acceptance'])
        self.assertFalse(result['release_eligible'])
        self.assertFalse(result['raw_trajectory_exported'])
        self.assertNotIn('review_metadata', result['review'])

    def test_timeout_is_not_a_review_even_with_saved_json(self):
        self.report['result']['exit_code'] = 1; self.save()
        with self.assertRaisesRegex(ValueError, 'did not complete'):
            receipt.validate(self.run_id)

    def test_cleanup_claim_needs_actual_empty_snapshots(self):
        self.report['cleanup']['two_snapshots'][1]['pods'] = ['still-running']; self.save()
        with self.assertRaisesRegex(ValueError, 'cleanup'):
            receipt.validate(self.run_id)

    def test_stale_secret_audit_rejected(self):
        self.review['summary'] = 'Changed after scanning.'; self.write(self.review_path, self.review)
        with self.assertRaisesRegex(ValueError, 'stale'):
            receipt.validate(self.run_id)

    def test_modified_run_report_requires_new_scan(self):
        path = self.root / ('acs-quality-live-' + self.run_id + '.json')
        self.report['result']['elapsed_seconds'] = 123
        self.write(path, self.report)
        with self.assertRaisesRegex(ValueError, 'stale for the run report'):
            receipt.validate(self.run_id)

    def test_audit_from_another_run_rejected(self):
        self.audit['run_id'] = 'qa-live-fffffffffe'
        self.save()
        with self.assertRaisesRegex(ValueError, 'failed exact-secret audit'):
            receipt.validate(self.run_id)

    def test_partial_source_inventory_rejected(self):
        self.manifest['files'].pop(); self.save()
        with self.assertRaisesRegex(ValueError, 'full evaluator'):
            receipt.validate(self.run_id)

    def test_source_change_rejected_before_import(self):
        self.manifest['files'][0]['sha256'] = '0' * 64; self.save()
        with self.assertRaisesRegex(ValueError, 'differs'):
            receipt.validate(self.run_id)

    def test_inconsistent_gate_rejected_by_original_validator(self):
        self.review['gate']['status'] = 'confirmed_blocker'
        self.write(self.review_path, self.review)
        self.audit['review_sha256'] = hashlib.sha256(self.review_path.read_bytes()).hexdigest(); self.save()
        with self.assertRaisesRegex(ValueError, 'gate/blocker'):
            receipt.validate(self.run_id)


if __name__ == '__main__':
    unittest.main()
