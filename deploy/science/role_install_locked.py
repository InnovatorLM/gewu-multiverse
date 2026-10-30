"""Keep a per-role installation lock for the complete micromamba lifetime."""
import fcntl
import os
from pathlib import Path
import sys

def main():
    path=Path('/home/role/.local/package-install.lock')
    fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise SystemExit('Another installation is active in this role; wait for its result.')
    os.set_inheritable(fd,True)
    os.execv('/usr/local/bin/micromamba',['micromamba',*sys.argv[1:]])

if __name__=='__main__':main()
