"""Run actual author selftest worker on an isolated existing benchmark upload.

No production role is scheduled. The real build/publish and ACS controls run;
this does not attest an author's self-solving or scientific task acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import uuid
import author_selftest_worker as worker
from evaluation_queue import W


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-repo',type=Path,required=True)
    parser.add_argument('--commit',required=True)
    parser.add_argument('--task',required=True)
    args=parser.parse_args()
    output=args.output.resolve()
    if not output.is_relative_to(W) or output.exists():
        raise ValueError('A fresh workspace-local evidence directory is required')
    output.mkdir(mode=0o700,parents=True)
    role=output/'role';workspace=role/'workspace';repo=workspace/'benchmark'
    repo.mkdir(parents=True)
    for command in [ ['init','-q'], ['config','user.email','operator@localhost'], ['config','user.name','operator'] ]:
        subprocess.run(['git','-C',str(repo),*command],check=True)
    data=subprocess.check_output(['git','-C',str(args.source_repo),'archive',args.commit,args.task])
    archive=output/'committed-source.tar';archive.write_bytes(data);archive.chmod(0o600)
    worker.unpack(archive,output/'export')
    shutil.copytree(output/'export'/args.task,repo/args.task)
    subprocess.run(['git','-C',str(repo),'add','.'],check=True)
    subprocess.run(['git','-C',str(repo),'commit','-qm','Frozen existing benchmark selftest fixture'],check=True)
    commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    inbox=role/'selftest/inbox';inbox.mkdir(parents=True)
    (role/'selftest/results').mkdir()
    job=uuid.uuid4().hex;upload=inbox/(job+'.tar')
    with tarfile.open(upload,'w') as stream:
        for path in sorted((repo/args.task).rglob('*')):
            stream.add(path,arcname=path.relative_to(repo/args.task),recursive=False)
    request=inbox/(job+'.json')
    payload=dict(job_id=job,task_name=args.task,source_commit=commit,source_repository='benchmark',source_task_path=args.task,archive_sha256=hashlib.sha256(upload.read_bytes()).hexdigest())
    request.write_text(json.dumps(payload));request.chmod(0o600)
    (output/'identity.json').write_text(json.dumps(dict(job_id=job,original_source_commit=args.commit,fixture_commit=commit,scope='real worker infrastructure acceptance; no author quality attestation'),indent=2))
    worker.STATE=output/'worker';worker.STATE.mkdir(mode=0o700)
    os.environ.setdefault('GEWU_DOCKER_LIBRARY_MIRROR','public.ecr.aws/docker/library')
    worker.process('operator-acceptance',dict(root=str(role),uid=os.getuid(),gid=os.getgid()),request)
    result=json.loads((role/'selftest/results'/(job+'.json')).read_text())
    (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(dict(job_id=job,status=result['status'],evidence=str(output)),ensure_ascii=False))
    if result['status']!='selftest_passed':raise SystemExit(1)


if __name__=='__main__':main()
