import unittest
from author_iteration_clock import transition

class ClockTests(unittest.TestCase):
    def test_platform_and_stopped_session_do_not_spend_active_budget(self):
        s={};transition(s,'start','idea-a',0)
        transition(s,'platform-wait','idea-a',100,reason='selftest request job-123')
        with self.assertRaises(ValueError):transition(s,'start','idea-b',101)
        transition(s,'resume','idea-a',40000)
        transition(s,'session-pause','idea-a',40100,reason='operator shutdown')
        transition(s,'resume','idea-a',80000)
        self.assertEqual(transition(s,'status','idea-a',80100)['active_seconds'],300)

    def test_pause_cannot_erase_time_already_spent(self):
        s={};transition(s,'start','idea-a',0)
        with self.assertRaises(ValueError):transition(s,'session-pause','idea-a',18001,reason='too late')
        self.assertEqual(s['ideas']['idea-a']['status'],'abandoned')
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
