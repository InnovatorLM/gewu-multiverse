import os,signal,subprocess,sys,time,unittest
from command_watchdog import overdue,process_info,stop_command_group
class DeadlineTests(unittest.TestCase):
    def test_term_ignoring_command_is_killed_after_grace(self):
        process=subprocess.Popen([sys.executable,'-u','-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print("ready",flush=True);time.sleep(30)'],start_new_session=True,stdout=subprocess.PIPE,text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(),'ready')
            result=stop_command_group(process_info(process.pid),[],grace=.1)
            self.assertEqual(process.wait(timeout=2),-signal.SIGKILL)
            self.assertEqual(result['kill_signals'],1)
        finally:
            if process.poll() is None:process.kill();process.wait()
            process.stdout.close()

    def test_boundary_and_process_scope(self):
        info=dict(pid=12,pgid=12,state='S',comm='bash',start_ticks=10000)
        self.assertFalse(overdue(info,3699,100,3600))
        self.assertTrue(overdue(info,3700,100,3600))
        for change in [dict(state='Z'),dict(comm='python'),dict(pgid=11)]:
            self.assertFalse(overdue(dict(info,**change),4000,100,3600))
