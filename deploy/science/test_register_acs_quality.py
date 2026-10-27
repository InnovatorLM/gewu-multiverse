"""Source/provenance binding checks; no model or cloud resources."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from evaluation_queue import W, digest_tree
from register_acs_quality import task_inventory, validate_registration


class RegistrationTests(unittest.TestCase):
    def test_provenance_tamper_and_source_drift_refused(self):
        with tempfile.TemporaryDirectory(dir=W / '.tmp') as temp:
            base = Path(temp)
            task = base / 'task'
            task.mkdir()
            (task / 'instruction.md').write_text('public fixture')
            settings_path = base / 'settings.json'
            settings_path.write_text('{}')
            provenance = base / 'provenance.json'
            sha = digest_tree(task)
            original = {'source_commit': 'a' * 40, 'source_task_path': 'tasks/fixture',
                        'snapshot_sha256': sha, 'scientific_acceptance': False,
                        'source_files': task_inventory(task)}
            provenance.write_text(json.dumps(original))
            entry = {'registration_kind': 'source_bound_quality_v1', 'dispatch': 'quality_diagnostic',
                     'quality_backend': 'acs', 'snapshot': str(task), 'snapshot_sha256': sha,
                     'runtime_image': 'pinned-image', 'source_commit': 'a' * 40,
                     'source_task_path': 'tasks/fixture', 'acs_quality_settings': str(settings_path),
                     'acs_quality_settings_sha256': hashlib.sha256(settings_path.read_bytes()).hexdigest(),
                     'quality_provenance': str(provenance),
                     'quality_provenance_sha256': hashlib.sha256(provenance.read_bytes()).hexdigest()}
            settings = {'task_sha256': sha, 'runtime_image': 'pinned-image'}
            with patch('register_acs_quality.load_settings', return_value=(settings, task)):
                validate_registration(entry, {'snapshot_sha256': sha})
                with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                    validate_registration(entry, {'snapshot_sha256': 'stale'})
                (task / 'instruction.md').write_text('changed')
                with self.assertRaisesRegex(ValueError, 'task bytes'):
                    validate_registration(entry, {'snapshot_sha256': sha})
                provenance.write_text('{}')
                with self.assertRaisesRegex(ValueError, 'provenance changed'):
                    validate_registration(entry, {'snapshot_sha256': sha})


if __name__ == '__main__':
    unittest.main()
