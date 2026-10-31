import asyncio
import base64
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
from evaluation_queue import W
from universe_ack import UniverseACK


class EvidenceTests(unittest.TestCase):
    def test_full_verifier_output_and_reward_collected(self):
        data={k:base64.b64encode(v).decode() for k,v in {'reward.txt':b'1\n','test-stdout.txt':b'All tests passed\n','ctrf.json':b'{"passed":true}'}.items()}
        obj=object.__new__(UniverseACK)
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
            with patch.object(UniverseACK,'exec',AsyncMock(return_value=SimpleNamespace(return_code=0,stdout=json.dumps(data)))):
                asyncio.run(obj.download_dir('/logs/verifier',raw))
            self.assertEqual((Path(raw)/'test-stdout.txt').read_text(),'All tests passed\n')
            self.assertEqual((Path(raw)/'reward.txt').read_text(),'1\n')
            self.assertEqual((Path(raw)/'ctrf.json').stat().st_mode&0o777,0o600)

    def test_unsafe_verifier_path_and_missing_reward_refused(self):
        obj=object.__new__(UniverseACK)
        for data in [{'test-stdout.txt':base64.b64encode(b'pass').decode()},
                     {'reward.txt':base64.b64encode(b'1').decode(),'../escape':base64.b64encode(b'bad').decode()}]:
            with tempfile.TemporaryDirectory(dir=W/'.tmp') as raw:
                with patch.object(UniverseACK,'exec',AsyncMock(return_value=SimpleNamespace(return_code=0,stdout=json.dumps(data)))):
                    with self.assertRaises(ValueError):asyncio.run(obj.download_dir('/logs/verifier',raw))

    def test_source_adapters_identical_and_wrapper_prefers_source(self):
        directory=Path(__file__).parent
        self.assertEqual((directory/'universe_ack.py').read_bytes(),(directory/'harbor-extensions/universe_ack.py').read_bytes())
        wrapper=(directory/'run-acs-evaluation').read_text()
        self.assertIn('PYTHONPATH="$W/gewu-multiverse/deploy/science/harbor-extensions:',wrapper)


if __name__=='__main__':unittest.main()
