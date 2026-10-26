#!/usr/bin/env python3
"""Operator queue runner: tool review, optional retained-evidence finalization.

Produces diagnostic evidence only. Does not build/run ACS or grant acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from evaluation_queue import W, atomic_json, digest_tree, root_file, validated_template
from role_exec import role_processes


def diagnostic_result(directory):
    path = Path(directory) / 'review.json'
    if not path.exists():
        return None
    data = json.loads(root_file(path).read_text())
    if data.get('scientific_acceptance') is not False or data.get('factual_acceptance') is not False:
        raise ValueError('Diagnostic runner cannot authorize acceptance')
    # The evaluator may read its diagnostic report, never controller/model
    # responses, private prompts, credentials or root filesystem paths.
    return {'review':data['review'], 'snapshot_sha256':data['snapshot_sha256'], 'method':data.get('method','retained-evidence-finalization'), 'new_independent_review':data.get('new_independent_review',True), 'tool_calls':data.get('tool_calls',data.get('source_tool_calls')), 'usage':data.get('usage'), 'usage_finalization':data.get('usage_finalization'), 'usage_source_review':data.get('usage_source_review')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-id',required=True)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--job',type=Path,required=True)
    args=parser.parse_args()
    if os.geteuid()!=0 or not args.job.resolve().is_relative_to(W) or args.job.exists():
        raise ValueError('Require operator and fresh workspace job directory')
    queue=json.loads(root_file(W/'.config/science-evaluation/queue.json').read_text())
    entry=json.loads(root_file(queue['registry']).read_text())[args.evaluation_id]
    validated_template(entry, {'snapshot_sha256':entry['snapshot_sha256']})
    if entry.get('dispatch','solver')!='quality_diagnostic' or str(args.root)!=entry.get('review_root') or digest_tree(args.root/'task')!=entry['snapshot_sha256']:
        raise ValueError('Diagnostic root/registered task mismatch')
    args.job.mkdir(mode=0o700)
    code=Path(__file__).parent
    attempts=[]
    def run(script,arguments):
        with (args.job/(script+'.log')).open('w') as log:
            result=subprocess.run([sys.executable,str(code/script),*arguments],stdout=log,stderr=log,env=os.environ.copy())
        attempts.append({'stage':script,'exit_code':result.returncode})
        atomic_json(args.job/'attempts.json',attempts)
        return result.returncode
    review_dir=args.job/'review'
    run('review_registered_task.py',['--evaluation-id',args.evaluation_id,'--tool-root',str(args.root),'--output',str(review_dir)])
    report=diagnostic_result(review_dir)
    if report is None and (review_dir/'tool-evidence.json').exists():
        finalized=args.job/'finalized'
        run('finalize_review_evidence.py',['--source',str(review_dir),'--output',str(finalized),'--json-body'])
        report=diagnostic_result(finalized)
    deadline=time.monotonic()+10
    while role_processes(21012) and time.monotonic()<deadline:
        time.sleep(.1)
    cleanup=not role_processes(21012)
    atomic_json(args.job/'summary.json',{'status':'quality_diagnostic_complete' if report is not None and cleanup else 'quality_diagnostic_failed','cleanup_confirmed':cleanup,'quality_acceptance':False,'scientific_acceptance':False,'factual_verification_required':True,'release_eligible':False,'diagnostic':report,'attempts':attempts,'acs_launched':False,'raw_trajectory_exported':False})


if __name__=='__main__':main()
