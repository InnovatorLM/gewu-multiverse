"""Snapshot untrusted role uploads without following links or blocking on FIFOs."""
import os
from pathlib import Path
import stat


def snapshot_upload(source, uid, limit, destination=None):
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_uid != uid or before.st_size > limit:
            raise ValueError('Invalid upload type, owner or size')
        chunks = []
        total = 0
        out = None
        try:
            if destination is not None:
                out_fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                out = os.fdopen(out_fd, 'wb')
            while True:
                block = os.read(fd, min(1024 * 1024, limit - total + 1))
                if not block:
                    break
                total += len(block)
                if total > limit:
                    raise ValueError('Upload grew beyond size limit')
                if out is not None:
                    out.write(block)
                else:
                    chunks.append(block)
            after = os.fstat(fd)
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns) or total != before.st_size:
                raise ValueError('Upload changed during snapshot')
        except BaseException:
            if out is not None:
                out.close()
                Path(destination).unlink(missing_ok=True)
            raise
        finally:
            if out is not None and not out.closed:
                out.close()
        return b''.join(chunks) if destination is None else total
    finally:
        os.close(fd)
