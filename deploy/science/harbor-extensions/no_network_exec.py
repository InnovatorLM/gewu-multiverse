#!/usr/bin/env python3
"""Fail-closed Linux x86_64 process-tree network guard for trusted launchers.

Not a Pod-wide policy: every untrusted entry point must use this launcher.
Requires no pre-existing worker processes or inherited socket descriptors.
"""
import ctypes
import errno
import os
import platform
import socket
import stat
import sys

class Filter(ctypes.Structure):
    _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte),
                ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint)]

class Program(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ushort), ('filters', ctypes.POINTER(Filter))]

def install():
    if sys.platform != 'linux' or platform.machine() != 'x86_64':
        raise RuntimeError('Only reviewed Linux x86_64 syscall ABI is supported')
    for fd in (0, 1, 2):
        try:
            if stat.S_ISSOCK(os.fstat(fd).st_mode):
                raise RuntimeError('Socket-backed standard descriptor refused')
        except OSError:
            pass
    for item in os.listdir('/proc/self/fd'):
        fd = int(item)
        if fd > 2:
            try: os.close(fd)
            except OSError: pass
    deny = 0x00050000 | errno.EPERM
    # Validate audit arch; forbid x32 ABI. Deny socket creation and io_uring
    # (including inherited rings); prevent cross-process fd/memory acquisition.
    rules = [(0x20,0,0,4), (0x15,1,0,0xc000003e), (0x06,0,0,0x80000000),
             (0x20,0,0,0), (0x35,0,1,0x40000000), (0x06,0,0,deny)]
    for syscall in (41,53,425,426,427,438,101,310,311):
        rules += [(0x15,0,1,syscall),(0x06,0,0,deny)]
    rules += [(0x06,0,0,0x7fff0000)]
    filters = (Filter * len(rules))(*(Filter(*r) for r in rules))
    program = Program(len(rules), filters)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38,1,0,0,0) != 0:
        raise OSError(ctypes.get_errno(), 'no_new_privs failed')
    if libc.prctl(22,2,ctypes.byref(program),0,0) != 0:
        raise OSError(ctypes.get_errno(), 'seccomp filter failed')
    try:
        socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    except OSError as error:
        if error.errno != errno.EPERM: raise
    else:
        raise RuntimeError('Network guard self-check failed')

if __name__ == '__main__':
    if len(sys.argv) < 2: raise SystemExit('usage: no_network_exec.py command [args]')
    install()
    os.execvp(sys.argv[1],sys.argv[1:])
