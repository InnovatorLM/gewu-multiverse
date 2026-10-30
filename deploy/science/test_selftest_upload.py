import os
from pathlib import Path
import tempfile
import unittest
from evaluation_queue import W
from selftest_upload import snapshot_upload


class UploadTests(unittest.TestCase):
    def test_snapshot_is_private_and_destination_never_overwritten(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);source=root/'source';source.write_bytes(b'content');target=root/'frozen'
            self.assertEqual(snapshot_upload(source,os.getuid(),7,target),7)
            self.assertEqual(target.read_bytes(),b'content')
            self.assertEqual(target.stat().st_mode & 0o777,0o600)
            with self.assertRaises(FileExistsError):snapshot_upload(source,os.getuid(),7,target)
            self.assertEqual(target.read_bytes(),b'content')

    def test_links_fifos_owner_and_size_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            root=Path(raw);source=root/'source';source.write_bytes(b'content')
            link=root/'link';link.symlink_to(source);fifo=root/'fifo';os.mkfifo(fifo)
            for path,uid,limit in [(link,os.getuid(),10),(fifo,os.getuid(),10),(source,os.getuid()+1,10),(source,os.getuid(),6)]:
                with self.subTest(path=path,uid=uid,limit=limit),self.assertRaises((ValueError,OSError)):
                    snapshot_upload(path,uid,limit)

    def test_json_bytes_are_read_from_opened_regular_file(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            source=Path(raw)/'request';source.write_bytes(b'{}')
            self.assertEqual(snapshot_upload(source,os.getuid(),16384),b'{}')
