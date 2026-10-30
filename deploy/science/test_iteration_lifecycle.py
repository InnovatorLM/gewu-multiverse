import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from evaluation_queue import W
from author_iteration_clock import transition
import iteration_lifecycle as lifecycle


class LifecycleTests(unittest.TestCase):
    def test_one_bad_ledger_does_not_disable_other_roles(self):
        config=dict(controller_uid=1,roles={'author-01':{},'author-02':{}})
        with patch.object(lifecycle,'_scan_clocks',side_effect=[ValueError('private role content'),None]) as scan,patch('builtins.print') as output:
            errors=lifecycle.scan_clocks(config)
        self.assertEqual(scan.call_count,2)
        self.assertEqual(errors,[dict(role='author-01',error_type='ValueError')])
        self.assertNotIn('private role content',str(output.call_args))

    def test_ledger_pause_resume_persists_and_keeps_permissions(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            universe=Path(raw);root=universe/'.config/gewu-multiverse/agents/author-01'
            directory=root/'home/role/.state/author-iteration';directory.mkdir(parents=True)
            run=universe/'.state/gewu-multiverse/author-01/run-test';run.mkdir(parents=True)
            path=directory/'ledger.json';state={};transition(state,'start','idea-a',10)
            path.write_text(json.dumps(state))
            config=dict(controller_uid=os.getuid(),roles={'author-01':dict(root=str(root),uid=os.getuid(),gid=os.getgid())})
            with patch.object(lifecycle,'runner_state',return_value=False),patch.object(lifecycle,'terminal_time',return_value=100),patch.object(lifecycle.time,'time',return_value=120):
                lifecycle.scan_clocks(config)
            paused=json.loads(path.read_text())['ideas']['idea-a']
            self.assertEqual(paused['active_seconds'],90)
            self.assertEqual(paused['status'],'session_paused')
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            with patch.object(lifecycle,'runner_state',return_value=True),patch.object(lifecycle.time,'time',return_value=10000):
                lifecycle.scan_clocks(config)
            resumed=json.loads(path.read_text())['ideas']['idea-a']
            self.assertEqual(resumed['active_seconds'],90)
            self.assertEqual(resumed['status'],'active')
            self.assertEqual(resumed['last_at'],10000)

    def test_runner_identity_requires_exact_run_and_uid(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            run=Path(raw);(run/'session.pid').write_text(str(os.getpid()))
            self.assertFalse(lifecycle.runner_state(run,os.getuid()))

    def test_terminal_record_can_be_read_after_large_history(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            run=Path(raw)
            (run/'transcript.jsonl').write_text('x'*20000+'\n'+json.dumps(dict(event='run_finished',ts='2026-10-31T00:00:00Z'))+'\n')
            self.assertEqual(lifecycle.terminal_time(run),1793404800)
