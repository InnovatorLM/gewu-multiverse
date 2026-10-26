"""Subset projection preserves actual judgments and cannot invent source tasks."""
import copy
import unittest
from project_semantic_comparison import project


class ProjectionTests(unittest.TestCase):
    def test_projection_preserves_source_and_adds_no_model_calls(self):
        records=[{'dataset':'fixture','commit':'a'*40,'path':f'{prefix}/mock/instruction.md','git_blob':str(i)*40,'sha256':str(i)*64,'instruction':f'Instruction source number {i}.'} for i,prefix in enumerate(['scripts','tasks'])]
        candidate='Robust sensor calibration task.'
        rows=[{**{key:record[key] for key in ['dataset','commit','path','git_blob','sha256']},'reference_id':i,'relation':'unrelated','difficulty_comparison':'unknown','reason':'Mock evidence','reference_quote':record['instruction'],'candidate_quote':candidate} for i,record in enumerate(records)]
        source_manifest={'instructions_sha256':'a'*64};target_manifest={'instructions_sha256':'b'*64,'selection_scope':'active'}
        report={'snapshot_sha256':'c'*64,'corpus_sha256':'a'*64,'references':2,'coverage':1,'comparisons':rows,'relation_counts':{'unrelated':2},'scientific_acceptance':False,'quality_acceptance':False,'release_eligible':False,'factual_verification_required':True,'usage':{'prompt_tokens':100,'completion_tokens':10}}
        result=project(report,records,source_manifest,records[1:],target_manifest,'c'*64,candidate)
        self.assertEqual(result['references'],1)
        self.assertEqual(result['comparisons'][0]['source_reference_id'],1)
        self.assertEqual(result['comparisons'][0]['reference_id'],0)
        self.assertEqual(result['comparisons'][0]['reason'],rows[1]['reason'])
        self.assertEqual(result['model_calls_for_projection'],0)
        self.assertFalse(result['new_independent_review'])
        self.assertEqual(result['usage'],{'prompt_tokens':0,'completion_tokens':0})
        self.assertEqual(result['source_review_usage'],report['usage'])
        changed=copy.deepcopy(records[1:]);changed[0]['sha256']='f'*64
        with self.assertRaises(ValueError):project(report,records,source_manifest,changed,target_manifest,'c'*64,candidate)


if __name__=='__main__':unittest.main()
