import json,tempfile,unittest
from pathlib import Path
import universe_monitor as m
class ArchiveTests(unittest.TestCase):
    def test_partial_append_and_redaction(self):
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d:
            old=m.ROOT;m.ROOT=Path(d)
            try:
                p=m.ROOT/'author-01/run-test';p.mkdir(parents=True)
                f=p/'transcript.jsonl';f.write_bytes(b'{"event":"reply","token":"secret"}\n{"event":')
                page=m.events_for('author-01','native:run-test')
                self.assertEqual(page['events'][0]['token'],'[REDACTED]')
                with f.open('ab') as out:out.write(b'"done"}\n')
                self.assertEqual(m.events_for('author-01','native:run-test',page['next_offset'])['events'][0]['event'],'done')
                with self.assertRaises(ValueError):m.events_for('author-01','native:../secret')
                self.assertTrue(any(r['id']=='native:run-test' for r in m.runs_for('author-01')))
            finally:m.ROOT=old
