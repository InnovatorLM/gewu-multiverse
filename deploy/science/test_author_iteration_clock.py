import unittest
from author_iteration_clock import transition

class ClockTests(unittest.TestCase):
    def test_active_across_sessions_and_acs_excluded(self):
        s={};transition(s,'start','idea-a',100)
        transition(s,'status','idea-a',200)
        transition(s,'acs-wait','idea-a',250,run_id='acs-job-1')
        transition(s,'status','idea-a',10000)
        transition(s,'resume','idea-a',20000)
        r=transition(s,'status','idea-a',20100)
        self.assertEqual(r['active_seconds'],250)
    def test_over_budget_closes_and_cannot_reset(self):
        s={};transition(s,'start','idea-a',0)
        r=transition(s,'status','idea-a',18001)
        self.assertEqual(r['status'],'abandoned')
        with self.assertRaises(ValueError):transition(s,'start','idea-a',18002)
        transition(s,'start','idea-b',18003)
    def test_parallel_ideas_disallowed(self):
        s={};transition(s,'start','idea-a',0)
        with self.assertRaises(ValueError):transition(s,'start','idea-b',1)
    def test_wait_requires_run_id(self):
        s={};transition(s,'start','idea-a',0)
        with self.assertRaises(ValueError):transition(s,'acs-wait','idea-a',1)
    def test_clock_cannot_go_back(self):
        s={};transition(s,'start','idea-a',100)
        with self.assertRaises(ValueError):transition(s,'status','idea-a',99)
    def test_difficulty_abandonment_is_final(self):
        s={};transition(s,'start','idea-a',0)
        transition(s,'abandon','idea-a',1,reason='difficulty not viable; notes.md')
        with self.assertRaises(ValueError):transition(s,'resume','idea-a',2)
