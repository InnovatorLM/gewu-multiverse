import unittest
from command_watchdog import overdue
class DeadlineTests(unittest.TestCase):
    def test_boundary_and_process_scope(self):
        info=dict(pid=12,pgid=12,state='S',comm='bash',start_ticks=10000)
        self.assertFalse(overdue(info,3699,100,3600))
        self.assertTrue(overdue(info,3700,100,3600))
        for change in [dict(state='Z'),dict(comm='python'),dict(pgid=11)]:
            self.assertFalse(overdue(dict(info,**change),4000,100,3600))
