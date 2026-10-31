import json,tempfile,unittest
from pathlib import Path
import universe_monitor as m
class ArchiveTests(unittest.TestCase):
    def test_brief_recovers_durable_history_after_interrupted_latest_write(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d:
            root=Path(d);latest=root/'latest.json'
            latest.write_text('{partial')
            (root/'history.jsonl').write_text(json.dumps(dict(text='previous',generated_at=1))+'\n')
            with patch.object(m,'BRIEF_DIR',root),patch.object(m,'BRIEF_FILE',latest),patch.object(m,'snapshot',return_value={'roles':[]}):
                m.write_brief()
            result=json.loads(latest.read_text())
            self.assertEqual(result['periods'][0]['text'],'previous')
            self.assertEqual(len(result['periods']),2)
            self.assertFalse((root/'latest.json.pending').exists())

    def test_monitor_lifecycle_follows_exact_owner_identity(self):
        from unittest.mock import patch,Mock
        server=Mock()
        with patch.object(m,'owner_identity',side_effect=['original','replacement']),patch.object(m.time,'sleep'):
            m.watch_owner(server,123,'original')
        server.shutdown.assert_called_once()
        self.assertIsNotNone(m.owner_identity(__import__('os').getpid()))
        self.assertIsNone(m.owner_identity(999999999))

    def test_cold_start_roles_are_visible_and_stale_brief_is_refreshed(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d:
            with patch.object(m,'ROOT',Path(d)), \
                 patch.object(m,'desired_roles',return_value={'author-01':'started','evaluator-01':'stopped'}), \
                 patch.object(m,'controller_live',return_value=True), \
                 patch.object(m,'review_waits',return_value={}), \
                 patch.object(m,'read_brief',return_value={'text':'old','generated_at':0,'periods':[]}):
                state=m.snapshot()
            self.assertEqual(len(state['roles']),2)
            self.assertEqual(state['roles'][0]['status'],'等待调度')
            self.assertEqual(state['roles'][1]['status'],'已停用')
            self.assertIn('当前启用 1 个角色',state['brief']['text'])
            self.assertEqual(state['brief']['periods'],[])

    def test_actual_startup_failure_is_visible_redacted_and_not_reported_running(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d:
            root=Path(d);run=root/'author-01/run-failed';run.mkdir(parents=True)
            (run/'startup-error.txt').write_text('clone permission denied token=private-value')
            with patch.object(m,'ROOT',root), \
                 patch.object(m,'desired_roles',return_value={'author-01':'started'}), \
                 patch.object(m,'controller_live',return_value=True), \
                 patch.object(m,'review_waits',return_value={}), \
                 patch.object(m,'read_brief',return_value={}):
                row=m.snapshot()['roles'][0]
                self.assertEqual(row['status'],'启动失败')
                self.assertIn('clone permission denied',row['startup_error'])
                self.assertNotIn('private-value',json.dumps(row))
                with patch.object(m,'controller_live',return_value=False):
                    self.assertEqual(m.snapshot()['roles'][0]['status'],'控制器未运行')
                with patch.object(m,'live_run',return_value=True):
                    self.assertEqual(m.snapshot()['roles'][0]['status'],'运行中')
        self.assertIn('esc(x.startup_error)',m.HTML)

    def test_review_wait_reason_is_latest_and_redacted(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d,patch.object(m,'DISPATCH_STATE',Path(d)):
            (Path(d)/'ledger.json').write_text(json.dumps({'old':dict(role='evaluator-01',state='reviewing',updated_at=1),'new':dict(role='evaluator-01',state='waiting_author',stage='completeness',reason='missing test.sh token=private-value',updated_at=2)}))
            row=m.review_waits()['evaluator-01']
            self.assertEqual(row['key'],'new')
            self.assertEqual(row['state'],'waiting_author')
            self.assertNotIn('private-value',row['reason'])

    def test_schedule_reason_requires_matching_controller_and_redacts(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as raw:
            root=Path(raw);(root/'author-01').mkdir();(root/'controller.pid').write_text('123')
            p=root/'author-01/schedule-state.json'
            row=dict(version=1,controller_pid=123,role='author-01',state='blocked',reason='missing token=private-value',next_at=None,last_session_outcome='refused',last_business_activity='opened pull request #33')
            p.write_text(json.dumps(row))
            with patch.object(m,'ROOT',root):
                result=m.scheduling_state('author-01')
                self.assertNotIn('private-value',result['reason'])
                self.assertEqual(result['last_session_outcome'],'refused')
                self.assertEqual(result['last_business_activity'],'opened pull request #33')
                self.assertEqual(m.scheduling_status('等待调度',result),'调度受阻')
                self.assertEqual(m.scheduling_status('控制器未运行',result),'控制器未运行')
                self.assertEqual(m.scheduling_status('运行中',result),'运行中')
                row['controller_pid']=124;p.write_text(json.dumps(row))
                self.assertIsNone(m.scheduling_state('author-01'))

    def test_evaluator_assignment_gate_matches_controller_schema(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(dir=m.W/'.tmp') as d:
            root=Path(d);home=root/'.config/gewu-multiverse/agents/evaluator-01';home.mkdir(parents=True)
            with patch.object(m,'UNIVERSE',root):
                self.assertFalse(m.evaluator_assignment_ready('evaluator-01'))
                p=home/'review-dispatch.json'
                for generation in [-1,True,'1',None]:
                    p.write_text(json.dumps(dict(state='reviewing',key='30:abc',generation=generation)))
                    self.assertFalse(m.evaluator_assignment_ready('evaluator-01'))
                p.write_text(json.dumps(dict(state='reviewing',key='30:abc',generation=0)))
                self.assertTrue(m.evaluator_assignment_ready('evaluator-01'))
                p.write_text(json.dumps(dict(state='waiting_author',key='30:abc',generation=0)))
                self.assertFalse(m.evaluator_assignment_ready('evaluator-01'))

    def test_evaluator_without_assignment_waits_without_implying_a_scheduled_session(self):
        from unittest.mock import patch
        with patch.object(m,'evaluator_assignment_ready',return_value=False):
            row=dict(state='restarting')
            self.assertEqual(m.scheduling_status('等待调度',row,'evaluator-01'),'等待评测派单')
            self.assertEqual(m.scheduling_status('等待调度',row,'author-01'),'等待下次会话')
            self.assertEqual(m.scheduling_status('等待作者修复',row,'evaluator-01'),'等待作者修复')
            self.assertEqual(m.scheduling_status('运行中',row,'evaluator-01'),'运行中')
        with patch.object(m,'evaluator_assignment_ready',return_value=True):
            self.assertEqual(m.scheduling_status('等待调度',row,'evaluator-01'),'等待下次会话')

    def test_review_wait_is_distinguished_without_overriding_process_facts(self):
        for state,label in [('waiting_author','等待作者修复'),('waiting_platform','等待平台处理'),('completed','审核完成，等待新任务')]:
            self.assertEqual(m.review_role_status('等待调度',{'state':state}),label)
            for status in ['运行中','启动失败','已停用','控制器未运行']:
                self.assertEqual(m.review_role_status(status,{'state':state}),status)
        self.assertEqual(m.review_role_status('等待调度',None),'等待调度')
        self.assertEqual(m.review_role_status('等待调度',{'state':'reviewing'}),'等待调度')

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
