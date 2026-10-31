"""Give the controller a persistent controlling PTY without a tmux socket.

Terminal output is drained, not archived: credentials may appear on setup screens.
The controller's structured run logs and the monitor remain the evidence source.
"""
import argparse
import errno
import fcntl
import os
import pty
import select
import signal
import struct
import subprocess
import termios
import time


def run(command, grace=30):
    master,slave=pty.openpty()
    fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',55,240,0,0))
    def controlling_terminal():
        fcntl.ioctl(0,termios.TIOCSCTTY,0)
    child=None
    stopping=False
    deadline=None
    def stop(_signum,_frame):
        nonlocal stopping,deadline
        if not stopping:
            stopping=True;deadline=time.monotonic()+grace
            if child is not None:
                try:os.killpg(child.pid,signal.SIGTERM)
                except ProcessLookupError:pass
    previous={sig:signal.signal(sig,stop) for sig in (signal.SIGTERM,signal.SIGINT)}
    try:
        child=subprocess.Popen(command,stdin=slave,stdout=slave,stderr=slave,
            start_new_session=True,preexec_fn=controlling_terminal)
        os.close(slave);slave=None
        while child.poll() is None:
            if stopping and time.monotonic()>=deadline:
                os.killpg(child.pid,signal.SIGKILL)
            if select.select([master],[],[],.1)[0]:
                try:os.read(master,65536)
                except OSError as error:
                    if error.errno!=errno.EIO:raise
                    time.sleep(.05)
        return child.wait()
    finally:
        if child is not None:
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            if child.poll() is None:
                try:child.wait(timeout=grace)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL);child.wait()
        os.close(master)
        if slave is not None:os.close(slave)
        for sig,handler in previous.items():signal.signal(sig,handler)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    if not args.command:parser.error('a controller command is required')
    raise SystemExit(run(args.command))
