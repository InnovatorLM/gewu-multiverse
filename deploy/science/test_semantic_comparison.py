"""Offline semantic-comparison coverage and source-citation validation."""
import json
import unittest
from semantic_comparison import batches, evidence_options, resolve_comparisons, validate_comparisons


class ComparisonTests(unittest.TestCase):
    def test_batches_cover_every_reference_without_truncation(self):
        records=[{'instruction':'reference '+str(i)+' '+('x'*i)} for i in range(51)]
        groups=batches(records,max_characters=200,max_records=7)
        flattened=[row for group in groups for row in group]
        self.assertEqual([r['reference_id'] for r in flattened],list(range(51)))
        self.assertEqual([r['instruction'] for r in flattened],[r['instruction'] for r in records])
        self.assertTrue(all(len(group)<=7 and sum(len(r['instruction']) for r in group)<=200 for group in groups))
        with self.assertRaises(ValueError):batches([{'instruction':'x'*201}],max_characters=200)

    def test_indexed_excerpts_preserve_markdown_and_reject_invalid_ids(self):
        candidate='Write `/app/result.json` with `slope` and `residual_scale`.'
        batch=[{'reference_id':0,'instruction':'Fit `parameters` from observations.'}]
        value={'comparisons':[{'reference_id':0,'relation':'shared_method','difficulty_comparison':'unknown','reason':'Mock comparison','reference_quote_index':0,'candidate_quote_index':0}]}
        result=resolve_comparisons(value,batch,candidate)
        self.assertEqual(result['comparisons'][0]['candidate_quote'],candidate)
        self.assertEqual(result['comparisons'][0]['reference_quote'],batch[0]['instruction'])
        for index in [-1,True,100,'0']:
            broken=json.loads(json.dumps(value));broken['comparisons'][0]['candidate_quote_index']=index
            with self.assertRaises(ValueError):resolve_comparisons(broken,batch,candidate)
        self.assertTrue(all(option in candidate for option in evidence_options(candidate)))

    def test_missing_duplicate_fabricated_and_boolean_ids_refused(self):
        candidate='Fit a robust laboratory sensor calibration.'
        batch=[{'reference_id':0,'instruction':'Estimate parameters of a nonlinear physical model.'},{'reference_id':1,'instruction':'Repair a network protocol implementation.'}]
        comparisons=[{'reference_id':row['reference_id'],'relation':'shared_method','difficulty_comparison':'unknown','reason':'Mock fixture, not a model judgment','reference_quote':row['instruction'],'candidate_quote':candidate} for row in batch]
        value={'comparisons':comparisons}
        self.assertEqual(validate_comparisons(value,batch,candidate),comparisons)
        for mutation in ['missing','duplicate','quote','bool','unknown']:
            broken=json.loads(json.dumps(value))
            if mutation=='missing':broken['comparisons'].pop()
            if mutation=='duplicate':broken['comparisons'][1]['reference_id']=0
            if mutation=='quote':broken['comparisons'][0]['reference_quote']='invented reference claim'
            if mutation=='bool':broken['comparisons'][0]['reference_id']=False
            if mutation=='unknown':broken['comparisons'][0]['relation']='accepted'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):validate_comparisons(broken,batch,candidate)


if __name__=='__main__':unittest.main()
