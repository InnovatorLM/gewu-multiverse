"""Verify author UID can submit frozen task and read only its published result."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from evaluation_queue import W
from selftest_source import verify_source


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--role',default='author-02')
    parser.add_argument('--fixture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cloud',action='store_true',help='Run this exact role upload through the real worker and ACS controls')
    args=parser.parse_args()
    if args.output.exists() or not args.output.resolve().is_relative_to(W):raise ValueError('Fresh workspace output required')
    config=json.loads((W/'.state/science-role-broker/config.json').read_text())
    entry=config['roles'][args.role];root=Path(entry['root'])
    from role_exec import role_processes
    if role_processes(entry['uid']):raise ValueError('Role must be stopped')
    name='selftest-client-acceptance-'+str(time.time_ns())
    target=root/'workspace'/name
    shutil.copytree(args.fixture,target)
    for path in [target,*target.rglob('*')]:
        if path.is_symlink():raise ValueError('Fixture links refused')
        os.chown(path,entry['uid'],entry['gid'])
    command=['chroot','--userspec='+str(entry['uid'])+':'+str(entry['gid']),str(root),'/usr/bin/env','-i','HOME=/home/role','PATH=/home/role/.local/env/bin:/usr/local/bin:/usr/bin:/bin','LD_LIBRARY_PATH=/home/role/.local/env/lib','PYTHONDONTWRITEBYTECODE=1']
    def run(argv):return subprocess.check_output(command+argv,text=True,timeout=60)
    commit=run(['git','-C','/workspace/'+name,'rev-parse','HEAD']).strip()
    request=json.loads(run(['/home/role/.local/env/bin/python','/usr/local/bin/role-acs-selftest','submit','--task','/workspace/'+name+'/openssl-selfsigned-cert','--commit',commit]))
    archive=root/'selftest/inbox'/(request['job_id']+'.tar')
    request_file=archive.with_suffix('.json')
    assert archive.stat().st_uid==entry['uid'] and request_file.stat().st_uid==entry['uid']
    # Client-only acceptance must never remain eligible for production workers.
    request_file.rename(request_file.with_suffix('.acceptance-completed'))
    result=root/'selftest/results'/(request['job_id']+'.json')
    if args.cloud:
        import author_selftest_worker as worker
        worker.STATE=args.output.parent/(args.output.stem+'-worker')
        worker.STATE.mkdir(mode=0o700)
        os.environ.setdefault('GEWU_DOCKER_LIBRARY_MIRROR','public.ecr.aws/docker/library')
        worker.process(args.role,entry,request_file.with_suffix('.acceptance-completed'))
    else:
        # Client-only fixtures never attest a real cloud run.
        result.write_text(json.dumps(dict(job_id=request['job_id'],status='client_acceptance_only',quality_acceptance=False)))
        os.chown(result,0,entry['gid']);result.chmod(0o640)
    verified=verify_source(root/'workspace',request['source_repository'],request['source_task_path'],commit,target/'openssl-selfsigned-cert')
    observed=json.loads(run(['/home/role/.local/env/bin/python','/usr/local/bin/role-acs-selftest','status',request['job_id']]))
    assert observed['status']==('selftest_passed' if args.cloud else 'client_acceptance_only')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(dict(role=args.role,uid=entry['uid'],job_id=request['job_id'],submit_under_role_uid=True,read_operator_result=True,source_git_tree_verified=verified['source_git_tree_verified'],cloud_run=args.cloud,observed_status=observed['status']),indent=2));args.output.chmod(0o600)
    print(args.output.read_text())


if __name__=='__main__':main()
