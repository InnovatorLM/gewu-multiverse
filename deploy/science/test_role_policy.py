from pathlib import Path
import tempfile
import unittest
from evaluation_queue import W
from role_policy import retire_pilot_feedback


class PolicyTests(unittest.TestCase):
    def test_preserves_history_but_removes_active_feedback(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);(root/'workspace').mkdir()
            source=root/'workspace/PILOT-REVIEW-FEEDBACK.md';source.write_text('old guidance')
            self.assertTrue(retire_pilot_feedback(root))
            self.assertFalse(source.exists())
            self.assertEqual((root/'workspace/.historical-feedback/PILOT-REVIEW-FEEDBACK.md').read_text(),'old guidance')
            self.assertIn('Superseded',(root/'workspace/.historical-feedback/README.md').read_text())
            self.assertFalse(retire_pilot_feedback(root))

    def test_does_not_follow_role_feedback_link(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);(root/'workspace').mkdir();target=root/'other';target.write_text('keep')
            (root/'workspace/PILOT-REVIEW-FEEDBACK.md').symlink_to(target)
            with self.assertRaises(ValueError):retire_pilot_feedback(root)
            self.assertEqual(target.read_text(),'keep')
