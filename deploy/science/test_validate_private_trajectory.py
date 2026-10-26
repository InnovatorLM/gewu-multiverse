"""Reject copied/stale/cancelled private trajectory evidence before judge access."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from evaluation_queue import W
import validate_private_trajectory as validator


@unittest.skipUnless(os.geteuid()==0,'operator evidence fixture')
class BindingTests(unittest.TestCase):
    def test_full_binding_and_changed_inputs(self):
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            root=Path(temporary);directory=root/'job';directory.mkdir(mode=0o700)
            entry={'snapshot':str(root/'task'),'snapshot_sha256':'a'*64}
            images={'runtime_image':'registry/runtime@sha256:'+'b'*64,'verifier_image':'registry/verifier@sha256:'+'c'*64}
            identity={**entry,'snapshot_path':entry['snapshot'],'provider':'dawnfm','model':'deepseek-v4.1-flash-1017',**images}
            atif={'schema_version':'ATIF-v1.7','steps':[{'step_id':1,'source':'agent'}]}
            binding={'snapshot_sha256':'a'*64,'snapshot_unchanged_after_run':True,'cleanup_confirmed':True,'trajectory_retained':True,'review_input_eligible':True,'solver_status':'solver_complete','scientific_acceptance':False}
            def save(name,value):
                p=directory/name;p.write_text(json.dumps(value));p.chmod(0o600)
            def setup():
                save('identity.json',identity);save('mini-swe-agent.trajectory.json',{'messages':[]});save('trajectory.json',atif);save('execution-binding.json',binding)
                retention={'snapshot_sha256':'a'*64,'review_ready':True,'schema_version':'ATIF-v1.7','scientific_acceptance':False}
                for name,key in [('identity.json','identity_sha256'),('mini-swe-agent.trajectory.json','raw_sha256'),('trajectory.json','atif_sha256')]:retention[key]=hashlib.sha256((directory/name).read_bytes()).hexdigest()
                save('retention.json',retention)
            setup()
            with patch.object(validator,'ROOT',root),patch.object(validator,'validated_template',return_value={'environment':{'kwargs':images}}):
                result=validator.validate(directory,entry);self.assertTrue(result['review_input_eligible']);self.assertFalse(result['release_eligible'])
                for field in ['snapshot_unchanged_after_run','cleanup_confirmed','trajectory_retained','review_input_eligible','solver_status']:
                    setup();bad=copy.deepcopy(binding);bad[field]='cancelled' if field=='solver_status' else False;save('execution-binding.json',bad)
                    with self.subTest(field=field),self.assertRaises(ValueError):validator.validate(directory,entry)
                for name in ['identity.json','mini-swe-agent.trajectory.json','trajectory.json']:
                    setup();(directory/name).write_text('{}')
                    with self.subTest(file=name),self.assertRaises((ValueError,KeyError)):validator.validate(directory,entry)
                setup();(directory/'trajectory.json').chmod(0o644)
                with self.assertRaises(ValueError):validator.validate(directory,entry)
                setup();bad=copy.deepcopy(identity);bad['runtime_image']='foreign';save('identity.json',bad)
                with self.assertRaises(ValueError):validator.validate(directory,entry)


if __name__=='__main__':unittest.main()
