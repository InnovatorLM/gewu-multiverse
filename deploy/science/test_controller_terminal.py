import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from evaluation_queue import W
from controller_terminal import run


class ControllerTerminalTests(unittest.TestCase):
    def test_child_has_controlling_terminal_and_exit_code_is_preserved(self):
        self.assertEqual(run(['/bin/bash','-c','test -t 0 && test -t 1 && echo ready >/dev/tty || exit 99; exit 7']),7)

    def test_stop_reaches_child_and_runs_its_cleanup(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);ready=root/'ready';stopped=root/'stopped'
            script='trap \'echo clean >"$2"; exit 0\' TERM; echo ready >"$1"; while true; do sleep .1; done'
            process=subprocess.Popen([sys.executable,str(Path(__file__).with_name('controller_terminal.py')),
                '/bin/bash','-c',script,'child',str(ready),str(stopped)])
            try:
                deadline=time.monotonic()+10
                while not ready.exists() and time.monotonic()<deadline:
                    if process.poll() is not None:self.fail('terminal launcher exited early')
                    time.sleep(.05)
                self.assertTrue(ready.exists())
                process.terminate();process.wait(timeout=10)
                self.assertEqual(stopped.read_text().strip(),'clean')
                self.assertEqual(process.returncode,0)
            finally:
                if process.poll() is None:process.kill();process.wait()


if __name__=='__main__':unittest.main()
