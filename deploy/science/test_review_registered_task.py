"""Offline complete-input safeguards; separate from live review evidence."""
from pathlib import Path
import tempfile
import unittest
from evaluation_queue import W
from review_registered_task import task_bundle, response_object


class BundleTests(unittest.TestCase):
    def test_response_must_finish_and_parse_directly(self):
        def response(reason, text):
            return {'choices': [{'finish_reason': reason, 'message': {'content': text}}]}
        self.assertEqual(response_object(response('stop', '{"task_id":"x"}')), {'task_id': 'x'})
        for reason, text in [('length', '{}'), ('stop', '```json\n{}\n```'), ('stop', '[]'), ('stop', '')]:
            with self.assertRaises(ValueError):
                response_object(response(reason, text))

    def test_complete_or_refused(self):
        with tempfile.TemporaryDirectory(dir=W / '.tmp') as directory:
            root = Path(directory)
            (root / 'instruction.md').write_text('task contract')
            self.assertEqual(task_bundle(root), [{'path': 'instruction.md', 'content': 'task contract'}])
            with self.assertRaises(ValueError):
                task_bundle(root, limit=1)
            (root / 'data.bin').write_bytes(b'\xff\x00')
            with self.assertRaises(ValueError):
                task_bundle(root)


if __name__ == '__main__':
    unittest.main()
