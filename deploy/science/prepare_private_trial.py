#!/usr/bin/env python3
"""Assemble a private trajectory-review input from one verified worker run."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from evaluation_queue import W, atomic_json, root_file
from validate_private_trajectory import validate, read_private


def prepare(directory, entry, state, output):
    directory=Path(directory);state=Path(state);output=Path(output)
    if output.exists() or not output.resolve().is_relative_to(W/'.state'):
        raise ValueError('Require fresh private state output')
    validation=validate(directory,entry)
    if not state.resolve().is_relative_to(W/'.state'):
        raise ValueError('Worker state must remain private')
    job=state/directory.name
    answer=json.loads(root_file(job/'result.json').read_text())
    identity=json.loads(read_private(directory/'identity.json'))
    if answer.get('job_id')!=directory.name or answer.get('evaluation_id')!=identity.get('evaluation_id') or answer.get('snapshot_sha256')!=entry['snapshot_sha256'] or answer.get('status')!='solver_complete' or answer.get('cleanup_confirmed') is not True:
        raise ValueError('Worker result does not match eligible private trajectory')
    guard=json.loads(root_file(job/'report.json').read_text())
    if guard.get('cleanup',{}).get('confirmed') is not True or guard.get('harbor_exit_code')!=0:
        raise ValueError('Independent guard completion/cleanup is not verified')
    config=json.loads(root_file(job/'config.json').read_text());job_name=config['job_name']
    if not isinstance(job_name,str) or Path(job_name).name!=job_name:
        raise ValueError('Invalid registered run name')
    run=job/'runs'/job_name
    trials=[p.parent for p in run.glob('*/result.json')]
    if len(trials)!=1:raise ValueError('Require exactly one actual trial')
    trial=trials[0]
    original_config=json.loads(root_file(trial/'config.json').read_text())
    if Path(original_config.get('task',{}).get('path','')).resolve()!=Path(entry['snapshot']).resolve():
        raise ValueError('Trial executed a different task path')
    model=(original_config.get('agent') or {}).get('model_name')
    if model!='openai/deepseek-v4.1-flash-1017':raise ValueError('Trial model differs from designated model')
    result=json.loads(root_file(trial/'result.json').read_text())
    reward=(result.get('verifier_result') or {}).get('rewards',{}).get('reward')
    if not result.get('finished_at') or result.get('exception_info') is not None or result.get('cleanup_exception_info') is not None or type(reward) not in [int,float] or reward not in [0,1]:
        raise ValueError('Require a completed normal binary-reward trial')
    inputs={'config.json':root_file(trial/'config.json'),'result.json':root_file(trial/'result.json'),'verifier/test-stdout.txt':root_file(trial/'verifier/test-stdout.txt'),'agent/trajectory.json':root_file(directory/'trajectory.json')}
    if (trial/'verifier/reward.txt').exists():inputs['verifier/reward.txt']=root_file(trial/'verifier/reward.txt')
    hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in inputs.items()}
    # Never copy the original config env/key material. Native review needs only
    # task path, declared model and basic run settings, not provider credentials.
    sanitized_config={'task':{'path':entry['snapshot']},'agent':{'model_name':model,'name':(original_config.get('agent') or {}).get('name')}}
    sanitized_result={key:result.get(key) for key in ['task_name','started_at','finished_at']}
    sanitized_result.update(exception_info=None,verifier_result={'rewards':{'reward':reward}})
    output.mkdir(mode=0o700)
    try:
        for name,path in inputs.items():
            target=output/name;target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            if name=='config.json':atomic_json(target,sanitized_config)
            elif name=='result.json':atomic_json(target,sanitized_result)
            else:shutil.copyfile(path,target);target.chmod(0o600)
        sys.path.insert(0,str(W/'repos/unified-evaluator-pipeline'))
        from unified_evaluator.inputs.trajectory import prepare as native_prepare
        native,_,_=native_prepare(Path(entry['snapshot']),output)
        validate(directory,entry)
        if any(hashlib.sha256(path.read_bytes()).hexdigest()!=hashes[name] for name,path in inputs.items()):raise ValueError('Source trial changed during preparation')
        manifest={'snapshot_sha256':entry['snapshot_sha256'],'source_job_id':directory.name,'source_input_hashes':hashes,'prepared_input_hashes':{name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in inputs},'trajectory_validation':validation,'native_input_validation_passed':True,'warnings':native.get('warnings',[]),'config_sanitized':True,'result_sanitized':True,'artifact_collection_copied':False,'model_calls':0,'scientific_acceptance':False,'release_eligible':False}
        atomic_json(output/'preparation.json',manifest)
        return manifest
    except BaseException:
        shutil.rmtree(output)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-id',required=True)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if os.geteuid()!=0:raise ValueError('Operator required')
    queue=json.loads(root_file(W/'.config/science-evaluation/queue.json').read_text());registry=json.loads(root_file(queue['registry']).read_text())
    result=prepare(args.directory,registry[args.evaluation_id],Path(queue['state']),args.output)
    print(json.dumps({'native_input_validation_passed':result['native_input_validation_passed'],'model_calls':0,'scientific_acceptance':False}))


if __name__=='__main__':main()
