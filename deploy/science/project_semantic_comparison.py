#!/usr/bin/env python3
"""Select a source-verified benchmark subset without new model judgments."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
from evaluation_queue import W, atomic_json, root_file, validated_template
from semantic_comparison import load_corpus, validate_report


def project(report,source_records,source_manifest,target_records,target_manifest,snapshot_hash,candidate):
    validate_report(report,source_records,source_manifest,snapshot_hash,candidate)
    by_source={(row['dataset'],row['path']):row for row in report['comparisons']}
    comparisons=[]
    for index,record in enumerate(target_records):
        previous=by_source.get((record['dataset'],record['path']))
        if previous is None or any(previous[key]!=record[key] for key in ['commit','git_blob','sha256']):
            raise ValueError('Target source not exactly covered by parent report')
        comparisons.append({**previous,'source_reference_id':previous['reference_id'],'reference_id':index})
    result={**report,'corpus_sha256':target_manifest['instructions_sha256'],'corpus_selection_scope':target_manifest.get('selection_scope'),'references':len(target_records),'comparisons':comparisons,'relation_counts':dict(Counter(row['relation'] for row in comparisons)),'source_review_usage':report['usage'],'usage':{'prompt_tokens':0,'completion_tokens':0},'new_independent_review':False,'projection_only':True,'coverage':1,'model_calls_for_projection':0,'source_scope':'parent sweep also contains excluded fixtures/history; source cost cannot be allocated only to active tasks'}
    result.pop('batches',None)
    validate_report(result,target_records,target_manifest,snapshot_hash,candidate)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report',type=Path,required=True)
    parser.add_argument('--source-corpus',type=Path,required=True)
    parser.add_argument('--target-corpus',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if os.geteuid()!=0 or not args.output.resolve().is_relative_to(W) or args.output.exists():raise ValueError('Require operator and fresh workspace output')
    source=root_file(args.source_report);report=json.loads(source.read_text())
    queue=json.loads(root_file(W/'.config/science-evaluation/queue.json').read_text());entry=json.loads(root_file(queue['registry']).read_text())[report['evaluation_id']]
    validated_template(entry,{'snapshot_sha256':report['snapshot_sha256']})
    source_records,source_manifest=load_corpus(args.source_corpus);target_records,target_manifest=load_corpus(args.target_corpus)
    candidate=(Path(entry['snapshot'])/'instruction.md').read_text()
    result=project(report,source_records,source_manifest,target_records,target_manifest,entry['snapshot_sha256'],candidate)
    result['source_report_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    args.output.mkdir(mode=0o700);atomic_json(args.output/'report.json',result)
    print(json.dumps({'references':result['references'],'relation_counts':result['relation_counts'],'new_model_calls':0,'scientific_acceptance':False}))


if __name__=='__main__':main()
