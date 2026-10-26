"""Exercise the generated Harbor package without a model, Docker or ACS."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from package_draft import package, WORKSPACE


class PackageTests(unittest.TestCase):
    def test_standalone_reference_grading_and_authoritative_data(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/'.tmp',prefix='eis-package-') as temporary:
            root=Path(temporary);task=package(root/'task');report=root/'report.json'
            env={'PATH':'/usr/bin:/bin','HOME':str(WORKSPACE/'.state/harbor-home'),
                 'TMPDIR':str(WORKSPACE/'.tmp'),'PYTHONDONTWRITEBYTECODE':'1'}
            solved=subprocess.run([sys.executable,str(task/'solution/solve.py'),str(task/'environment/data/cases.json'),str(report)],cwd=root,env=env,capture_output=True,text=True,timeout=20)
            self.assertEqual(solved.returncode,0,solved.stderr)
            def grade():
                return subprocess.run([sys.executable,str(task/'tests/grade.py'),'--report',str(report)],cwd=root,env=env,capture_output=True,text=True,timeout=20)
            self.assertEqual(grade().returncode,0)
            original=json.loads(report.read_text())
            case_ids=list(original)
            # Solver-editable data are deliberately corrupted. Authoritative
            # tests must still grade the original case data and reject a bad fit.
            (task/'environment/data/cases.json').write_text('{}')
            self.assertEqual(grade().returncode,0)
            mutations=[]
            bad=json.loads(json.dumps(original));del bad[case_ids[0]];mutations.append(bad)
            bad=json.loads(json.dumps(original));bad[case_ids[0]]['two_branch']['rs']='999';mutations.append(bad)
            bad=json.loads(json.dumps(original));bad[case_ids[0]]['d_vector'][0]='999';mutations.append(bad)
            bad=json.loads(json.dumps(original));bad[case_ids[0]]['next_measurement']=1.0;mutations.append(bad)
            bad=json.loads(json.dumps(original));bad[case_ids[1]]['certificate']=[0,0,0];mutations.append(bad)
            for bad in mutations:
                report.write_text(json.dumps(bad));self.assertNotEqual(grade().returncode,0)
            report.write_text('{"x":1,"x":2}');self.assertNotEqual(grade().returncode,0)

    def test_build_context_and_source_hashes(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/'.tmp',prefix='eis-package-') as temporary:
            task=package(Path(temporary)/'task')
            environment=task/'environment'
            self.assertEqual({str(p.relative_to(environment)) for p in environment.rglob('*') if p.is_file()}, {'Dockerfile','data/cases.json'})
            public=json.loads((environment/'data/cases.json').read_text())
            self.assertEqual(set(public),{'spectrum-1','spectrum-2'})
            for case in public.values():
                self.assertNotIn('branches',case);self.assertNotIn('known_witness_reports',case)
            self.assertIn('COPY data/ /app/data/',(environment/'Dockerfile').read_text())
            self.assertEqual((environment/'data/cases.json').read_bytes(),(task/'tests/public-cases.json').read_bytes())
            with self.assertRaises(ValueError):package(task)
            provenance=json.loads((task/'authoring/provenance.json').read_text())
            self.assertFalse(provenance['registration_enabled'])
            self.assertFalse(provenance['scientific_acceptance'])
            self.assertFalse(provenance['runtime_verified'])


if __name__=='__main__':unittest.main()
