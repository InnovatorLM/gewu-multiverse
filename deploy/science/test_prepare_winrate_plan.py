"""Full-package resume evidence catches binary changes that size-only checks miss."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from evaluation_queue import W,digest_tree
from prepare_winrate_plan import verify_package_inputs


class PlanInputTests(unittest.TestCase):
    def test_full_binary_hash_and_candidate_identity(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            root=Path(temporary);settings=root/'.config/science-evaluation';settings.mkdir(parents=True)
            task=root/'reference';task.mkdir();(task/'instruction.md').write_text('Reference task.');binary=task/'data.bin';binary.write_bytes(b'\x00\x01')
            import hashlib
            entry={'snapshot':str(root/'candidate'),'snapshot_sha256':'a'*64}
            (settings/'registry.json').write_text(json.dumps({'candidate-v1':entry}))
            manifest={'evaluation_id':'candidate-v1','candidate_path':entry['snapshot'],'snapshot_sha256':entry['snapshot_sha256'],'references':[{'snapshot_path':str(task),'snapshot_sha256':digest_tree(task),'instruction_sha256':hashlib.sha256((task/'instruction.md').read_bytes()).hexdigest()}]}
            with patch('prepare_winrate_plan.W',root),patch('prepare_winrate_plan.validated_template'):
                verify_package_inputs(manifest)
                binary.write_bytes(b'\x00\x02')
                with self.assertRaises(ValueError):verify_package_inputs(manifest)
                binary.write_bytes(b'\x00\x01');bad=copy.deepcopy(manifest);bad['candidate_path']=str(root/'foreign-candidate')
                with self.assertRaises(ValueError):verify_package_inputs(bad)


if __name__=='__main__':unittest.main()
