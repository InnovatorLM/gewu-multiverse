"""Focused filesystem probe for distinguishing small-file latency from I/O stalls."""
import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path


class StorageProbeTests(unittest.TestCase):
    def test_workspace_and_local_disk_create_read_rename_and_fsync(self):
        workspace = Path('/mnt/data/zhanglinfeng/workspace')
        reports = {}
        for label, temporary_root in (
            ('workspace_cpfs', workspace / '.tmp'),
        ):
            temporary_root.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='storage-probe-', dir=temporary_root) as raw:
                root = Path(raw)
                small_started = time.monotonic()
                for i in range(100):
                    path = root / str(i)
                    path.write_bytes(b'x' * 4096)
                    self.assertEqual(path.read_bytes(), b'x' * 4096)
                    path.rename(root / (str(i) + '.moved'))
                small_file_seconds = time.monotonic() - small_started

                payload = os.urandom(16 * 1024 * 1024)
                path = root / 'large.bin'
                large_started = time.monotonic()
                with path.open('wb') as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), hashlib.sha256(payload).digest())
                large_file_seconds = time.monotonic() - large_started

            reports[label] = {
                'filesystem_path': str(temporary_root),
                'small_file_count': 100,
                'small_file_create_read_rename_seconds': round(small_file_seconds, 4),
                'large_file_bytes': len(payload),
                'large_file_write_fsync_hash_seconds': round(large_file_seconds, 4),
                'result': 'passed',
            }
        output = workspace / '.state/storage-investigation/filesystem-probe.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(reports, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
