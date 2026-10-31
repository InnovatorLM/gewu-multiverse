#!/usr/local/bin/python3
"""Author-local submission client; no cloud credentials."""
import argparse,json,uuid,tarfile,hashlib,subprocess
from pathlib import Path
p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
s=sub.add_parser('submit');s.add_argument('--task',type=Path,required=True);s.add_argument('--commit',required=True)
s.add_argument('--previous-job',help='Prior completed selftest used for result-driven iteration')
s.add_argument('--iteration-note',help='What changed in response to that execution')
s=sub.add_parser('status');s.add_argument('job_id');a=p.parse_args();base=Path('/selftest')
if a.action=='status':
 if not __import__('re').fullmatch('[a-f0-9]{32}',a.job_id):raise SystemExit('Invalid job ID')
 f=base/'results'/(a.job_id+'.json');print(f.read_text() if f.exists() else json.dumps({'status':'queued','job_id':a.job_id}))
else:
 if bool(a.previous_job)!=bool(a.iteration_note):raise SystemExit('Use --previous-job and --iteration-note together')
 if a.previous_job and (not __import__('re').fullmatch('[a-f0-9]{32}',a.previous_job) or not 20<=len(a.iteration_note.strip())<=4000):raise SystemExit('Invalid previous job or iteration note (20-4000 characters)')
 if not __import__('re').fullmatch('[a-f0-9]{40}',a.commit):raise SystemExit('Use full source commit')
 task=a.task.resolve(strict=True)
 if not task.is_relative_to(Path('/workspace')):raise SystemExit('Task must be in workspace')
 repository=Path(subprocess.check_output(['git','-C',str(task),'rev-parse','--show-toplevel'],text=True).strip()).resolve(strict=True)
 if not repository.is_relative_to(Path('/workspace')):raise SystemExit('Source repository must be in workspace')
 task_path=task.relative_to(repository).as_posix()
 if task_path=='.':raise SystemExit('Task must be a subdirectory of its source repository')
 files=list(task.rglob('*'));total=0
 for f in files:
  if f.is_symlink() or not(f.is_file() or f.is_dir()):raise SystemExit('Links and special files refused')
  if f.is_file():total+=f.stat().st_size
 if total>128*1024*1024 or len(files)>10000:raise SystemExit('Task exceeds limit')
 job=uuid.uuid4().hex;archive=base/'inbox'/(job+'.tar')
 with tarfile.open(archive,'w') as t:
  for f in files:t.add(f,arcname=f.relative_to(task),recursive=False)
 request={'job_id':job,'task_name':task.name,'source_commit':a.commit,'source_repository':repository.relative_to('/workspace').as_posix(),'source_task_path':task_path,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
 if a.previous_job:request['iteration']={'previous_job':a.previous_job,'note':a.iteration_note.strip()}
 pending=base/'inbox'/(job+'.pending');pending.write_text(json.dumps(request));pending.replace(pending.with_suffix('.json'));print(json.dumps(request))
