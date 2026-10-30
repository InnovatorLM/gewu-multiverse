"""Register an operator-reviewed preflight receipt; never infer author work.

This is the publication step after evidence review, not an automatic scientific
approval. Dry run is the default. Original execution evidence stays unchanged.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import time
import author_submission_gate as gate


def register(receipt_path, commit, task, apply=False):
    if os.geteuid() != 0:
        raise PermissionError('Operator required')
    gate.validate_identity(commit, task)
    raw = gate.read_operator_file(receipt_path, 1024 * 1024)
    receipt = gate.validate_receipt(json.loads(raw), commit, task)
    key = commit + '-' + hashlib.sha256(task.encode()).hexdigest()[:16]
    directory = gate.universe_root(gate.W) / '.state/science-author-preflight'
    destination = directory / (key + '.json')
    result = dict(commit=commit, task=task, destination=str(destination),
                  applied=False, source_sha256=hashlib.sha256(raw).hexdigest(),
                  scope='author preflight only; independent evaluation still required')
    if not apply:
        return result
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o077:
        raise ValueError('Preflight registry must be an operator-private directory')
    published = dict(receipt, registration=dict(at=time.time(), operator_uid=0,
                     source_sha256=result['source_sha256'], scope=result['scope']))
    fd, temporary = tempfile.mkstemp(prefix='.register-', dir=directory)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(published, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        # Revalidate immediately before publication; do not replace prior evidence.
        gate.validate_receipt(published, commit, task)
        os.link(temporary, destination, follow_symlinks=False)
        directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        Path(temporary).unlink(missing_ok=True)
    result['applied'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(register(args.receipt, args.commit, args.task, args.apply), ensure_ascii=False))


if __name__ == '__main__':
    main()
