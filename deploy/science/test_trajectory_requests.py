import json
import unittest
from trajectory_requests import replay, requests


class RequestReplayTests(unittest.TestCase):
    def test_history_tools_system_changes_and_summary_checkpoint(self):
        first = dict(model='test', messages=[dict(role='system', content='policy'), dict(role='user', content='task')])
        delta = dict(format='gewu.request-delta.v1', base='previous_model_request', base_message_count=2,
                     system=dict(role='system', content='updated policy'),
                     append=[dict(role='assistant', tool_calls=[dict(id='call1')]), dict(role='tool', tool_call_id='call1', content='计算结果')],
                     options=dict(model='test'))
        summary = dict(model='test', messages=[dict(role='system', content='policy'), dict(role='user', content='summary')])
        events = [dict(event='model_request', turn=i, body=json.dumps(x)) for i,x in enumerate([first,delta,summary])]
        rows = list(requests(events))
        self.assertEqual(rows[0]['request'], first)
        self.assertEqual(rows[1]['request']['messages'], [delta['system'], first['messages'][1], *delta['append']])
        self.assertEqual(rows[2]['request'], summary)
        self.assertEqual(first['messages'][0]['content'], 'policy')

    def test_missing_base_or_options_change_is_rejected(self):
        delta = dict(format='gewu.request-delta.v1',base='previous_model_request',base_message_count=2,
                     system={},append=[],options=dict(model='different'))
        with self.assertRaises(ValueError): replay(None,delta)
        with self.assertRaises(ValueError): replay(dict(model='test',messages=[{},{}]),delta)
        delta['options'] = dict(model='test');delta['base_message_count'] = 3
        with self.assertRaises(ValueError): replay(dict(model='test',messages=[{},{}]),delta)

    def test_non_request_events_do_not_change_base(self):
        first = dict(model='test',messages=[{},{}])
        self.assertEqual(list(requests([dict(event='tool_result'),dict(event='model_request',turn=1,body=json.dumps(first))]))[0]['request'],first)


if __name__ == '__main__': unittest.main()
