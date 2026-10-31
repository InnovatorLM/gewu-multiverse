import json,tempfile,unittest
from pathlib import Path
import universe_monitor as m
class ArchiveTests(unittest.TestCase):
    def test_review_wait_reason_is_latest_and_redacted(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d,patch.object(m,'DISPATCH_STATE',Path(d)):
            (Path(d)/'ledger.json').write_text(json.dumps({'old':dict(role='evaluator-01',state='reviewing',updated_at=1),'new':dict(role='evaluator-01',state='waiting_author',stage='completeness',reason='missing test.sh token=private-value',updated_at=2)}))
            row=m.review_waits()['evaluator-01']
            self.assertEqual(row['key'],'new')
            self.assertEqual(row['state'],'waiting_author')
            self.assertNotIn('private-value',row['reason'])

    def test_stopped_controller_is_not_presented_as_scheduling_wait(self):
        self.assertEqual(m.role_status('started',False,False),'控制器未运行')
        self.assertEqual(m.role_status('started',False,True),'等待调度')
        self.assertEqual(m.role_status('stopped',True,False),'运行中')
        self.assertEqual(m.role_status('stopped',False,False),'已停用')
    def test_snapshot_tail_is_bounded_and_drops_partial_first_line(self):
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d:
            path=Path(d)/'large'
            path.write_bytes(b'x'*1000000+bytes([10])+b'last'+bytes([10]))
            tail=m.tail_text(path,100)
            self.assertLessEqual(len(tail),100)
            self.assertEqual(tail.strip(),'last')

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

    def test_live_status_does_not_trust_a_stale_pid(self):
        import os
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d:
            run=Path(d)
            (run/'session.pid').write_text(str(os.getpid()))
            self.assertFalse(m.live_run(run))
            (run/'session.pid').write_text('999999999')
            self.assertFalse(m.live_run(run))

    def test_controller_status_uses_owned_pid_marker(self):
        import subprocess
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d:
            old=m.ROOT;m.ROOT=Path(d)/'.state/gewu-multiverse';m.ROOT.mkdir(parents=True)
            child=subprocess.Popen(['/bin/bash','-c','exec -a gewu-multiverse sleep 10'])
            try:
                (m.ROOT/'controller.pid').write_text(str(child.pid))
                self.assertTrue(m.controller_live())
                (m.ROOT/'controller.pid').write_text('999999999')
                self.assertFalse(m.controller_live())
            finally:
                child.terminate();child.wait(timeout=5);m.ROOT=old

    def test_selection_is_read_from_agent_settings(self):
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d:
            old=m.SETTINGS;m.SETTINGS=Path(d)/'settings.toml'
            try:
                m.SETTINGS.write_text('[[agents]]\nname = "author-01"\ndesired = "started"\n[[agents]]\nname = "author-05"\ndesired = "stopped"\n')
                self.assertEqual(m.desired_roles(),{'author-01':'started','author-05':'stopped'})
            finally:m.SETTINGS=old
