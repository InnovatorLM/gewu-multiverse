"""Mock semantic route with complete source-bound reports, no live API/ACS."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest.mock import patch
from evaluation_queue import W, evaluation_catalog, process
from semantic_comparison import evidence_options, load_corpus, validate_report


class CatalogTests(unittest.TestCase):
    def test_all_dispatch_types_keep_distinct_purposes(self):
        registry={kind:{'dispatch':kind,'snapshot_sha256':'a'*64} for kind in ['solver','quality_diagnostic','semantic_diagnostic']}
        rows=evaluation_catalog(registry)['evaluations']
        self.assertEqual(len({row['purpose'] for row in rows}),3)
        self.assertTrue(all('not acceptance' in row['purpose'] for row in rows))
        self.assertTrue(all(set(row)=={'evaluation_id','snapshot_sha256','purpose'} for row in rows))
        registry['semantic_diagnostic']['enabled']=False
        self.assertEqual(len(evaluation_catalog(registry)['evaluations']),2)


@unittest.skipUnless(os.geteuid()==0 and (W/'.config/science-evaluation/registry.json').exists(),'operator corpus fixture required')
class SemanticQueueTests(unittest.TestCase):
    def test_retired_request_refused_before_claim(self):
        entry=json.loads((W/'.config/science-evaluation/registry.json').read_text())['calibration-v1']
        entry['enabled']=False
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            base=Path(temporary);(base/'state').mkdir()
            registry=base/'registry.json';registry.write_text(json.dumps({'retired':entry}))
            identifier=uuid.uuid4().hex;request=base/f'{identifier}.json';request.write_text(json.dumps({'job_id':identifier,'evaluation_id':'retired','snapshot_sha256':entry['snapshot_sha256']}));os.chown(request,21002,21002)
            with self.assertRaisesRegex(ValueError,'retired'):
                process({'registry':str(registry),'state':str(base/'state'),'results':str(base),'evaluator_uid':21002},request)
            self.assertFalse((base/'state'/identifier).exists())

    def test_complete_report_and_mutated_source_refusal(self):
        entry=json.loads((W/'.config/science-evaluation/registry.json').read_text())['calibration-semantic-active-v1']
        records,manifest=load_corpus(entry['reference_corpus'])
        candidate=(Path(entry['snapshot'])/'instruction.md').read_text()
        comparisons=[{'reference_id':i,'relation':'unrelated','difficulty_comparison':'unknown','reason':'Mock fixture, not real semantic judgment','reference_quote':evidence_options(row['instruction'])[0],'candidate_quote':evidence_options(candidate)[0],**{key:row[key] for key in ['dataset','commit','path','git_blob','sha256']}} for i,row in enumerate(records)]
        report={'corpus_selection_scope':manifest.get('selection_scope','all'),'snapshot_sha256':entry['snapshot_sha256'],'corpus_sha256':manifest['instructions_sha256'],'coverage':1,'references':len(records),'comparisons':comparisons,'relation_counts':{'unrelated':len(records)},'scientific_acceptance':False,'quality_acceptance':False,'release_eligible':False,'factual_verification_required':True}
        validate_report(report,records,manifest,entry['snapshot_sha256'],candidate)
        for mutation in ['missing','source','quote','acceptance']:
            changed=copy.deepcopy(report)
            if mutation=='missing':changed['comparisons'].pop()
            if mutation=='source':changed['comparisons'][0]['commit']='0'*40
            if mutation=='quote':changed['comparisons'][0]['candidate_quote']='invented candidate source'
            if mutation=='acceptance':changed['scientific_acceptance']=True
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):validate_report(changed,records,manifest,entry['snapshot_sha256'],candidate)
        with tempfile.TemporaryDirectory(dir=W/'.tmp') as temporary:
            base=Path(temporary)
            for name in ['state','results']: (base/name).mkdir()
            registry=base/'registry.json';registry.write_text(json.dumps({'semantic-test':entry}))
            identifier=uuid.uuid4().hex;request=base/f'{identifier}.json';request.write_text(json.dumps({'job_id':identifier,'evaluation_id':'semantic-test','snapshot_sha256':entry['snapshot_sha256']}));os.chown(request,21002,21002)
            class FakeChild:
                pid=99999999
                def __init__(self,command,**kwargs):
                    assert command[0].endswith('/run-semantic-diagnostic')
                    output=Path(command[command.index('--output')+1]);output.mkdir();(output/'report.json').write_text(json.dumps(report))
                def wait(self,timeout=None):return 0
                def poll(self):return 0
            config={'registry':str(registry),'state':str(base/'state'),'results':str(base/'results'),'evaluator_uid':21002,'max_jobs_per_day':3}
            with patch('evaluation_queue.subprocess.Popen',FakeChild):result=process(config,request)
            self.assertEqual(result['status'],'semantic_diagnostic_complete')
            self.assertFalse(result['quality_acceptance'])
            self.assertFalse(result['acs_launched'])
            self.assertTrue(result['factual_verification_required'])
            self.assertTrue(result['cleanup_confirmed'])
            self.assertEqual(result['comparison']['references'],138)


if __name__=='__main__':unittest.main()
