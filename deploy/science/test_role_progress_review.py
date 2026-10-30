import json
import unittest
from role_progress_review import assess
class ProgressTests(unittest.TestCase):
    def test_delta_measures_reconstructed_context_not_small_record(self):
        first=dict(model='test',messages=[dict(role='system',content='policy'),dict(role='user',content='x'*500000)])
        delta=dict(format='gewu.request-delta.v1',base='previous_model_request',base_message_count=2,
            system=first['messages'][0],append=[dict(role='assistant',content='next')],options=dict(model='test'))
        events=[dict(event='model_request',body=json.dumps(record)) for record in (first,delta)]
        result=assess(events)
        self.assertGreater(result['last_request_chars'],500000)
        self.assertEqual(result['request_replay_errors'],0)
        self.assertEqual(result['recommendation'],'manual_review')

    def test_missing_checkpoint_is_unknown_not_healthy_small_context(self):
        delta=dict(format='gewu.request-delta.v1',base='previous_model_request',base_message_count=2,system={},append=[],options={})
        result=assess([dict(event='model_request',body=json.dumps(delta))])
        self.assertIsNone(result['last_request_chars'])
        self.assertEqual(result['request_replay_errors'],1)
        self.assertEqual(result['recommendation'],'manual_review')

    def test_full_checkpoint_recovers_after_broken_delta(self):
        result=assess([dict(event='model_request',body=json.dumps(dict(format='gewu.request-delta.v1'))),
            dict(event='model_request',body=json.dumps(dict(model='test',messages=[{},{}])))])
        self.assertGreater(result['last_request_chars'],0)
        self.assertEqual(result['request_replay_errors'],1)

    def test_hints_never_claim_dead_end(self):
        events=[dict(event='tool_result',exit_code=1,output='expected negative control') for _ in range(10)]
        result=assess(events)
        self.assertEqual(result['recommendation'],'manual_review')
        self.assertIn('Expected failed controls', result['caution'])
    def test_silent_command_is_not_automatically_a_dead_end(self):
        self.assertEqual(assess([dict(event='tool_call',command='compute')])['recommendation'],'no_hint')
    def test_masked_exception_and_context_growth(self):
        result=assess([dict(event='tool_result',exit_code=0,output='Traceback (most recent call last)'),dict(event='model_request',body='x'*500001)])
        self.assertEqual(len(result['reasons']),2)
    def test_missing_skills_and_turn_limit_are_platform_hints(self):
        result=assess([dict(event='skills_discovered',skills=[]),dict(event='run_finished',outcome='failed',reason='bound: max_turns')])
        self.assertEqual(result['recommendation'],'manual_review')
        self.assertEqual(len(result['reasons']),2)
    def test_timeout_requires_time_accounting_review(self):
        result=assess([dict(event='run_finished',outcome='timed_out',reason='time limit')])
        self.assertIn('platform waits',result['reasons'][0])
if __name__=='__main__':unittest.main()
