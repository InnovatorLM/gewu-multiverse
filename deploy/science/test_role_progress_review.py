import unittest
from role_progress_review import assess
class ProgressTests(unittest.TestCase):
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
if __name__=='__main__':unittest.main()
