"""Validate operator attestation before allocating evaluator work."""
import json,re,math,os,stat,hashlib
from pathlib import Path
W=Path('/mnt/data/zhanglinfeng/workspace')
CHECKS=('schema','container_build','container_start','author_solve','verifier_positive','verifier_negative','post_iteration_rerun')
REQUIRED_ORDER=('schema','container_build','container_start','author_solve','verifier_positive','verifier_negative','post_iteration_rerun')
def read_operator_file(path,limit=16*1024*1024):
    path=Path(path)
    if not path.is_absolute() or not path.resolve().is_relative_to(W.resolve()):raise ValueError('Operator evidence outside workspace')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_mode & 0o022 or info.st_size>limit:
            raise ValueError('Invalid operator evidence type, ownership or size')
        data=stream.read(limit+1)
        after=os.fstat(stream.fileno())
        if len(data)>limit or len(data)!=info.st_size or (info.st_mtime_ns,info.st_ctime_ns)!=(after.st_mtime_ns,after.st_ctime_ns):
            raise ValueError('Operator evidence changed during read')
        return data
def validate_receipt(receipt,commit,task):
    if receipt.get('commit')!=commit or receipt.get('task')!=task:raise ValueError('Stale author preflight identity')
    if not re.fullmatch(r'[a-f0-9]{64}',receipt.get('snapshot_sha256','')):raise ValueError('Missing frozen execution identity')
    if not re.fullmatch(r'.+@sha256:[a-f0-9]{64}',receipt.get('runtime_image','')):raise ValueError('Missing image digest')
    if any(receipt.get('checks',{}).get(k) is not True for k in CHECKS):raise ValueError('Author container preflight incomplete')
    order=receipt.get('pre_submission_order')
    if order != list(REQUIRED_ORDER):raise ValueError('Pre-submission checks must be recorded in order')
    if receipt.get('iteration_applied') is not True:raise ValueError('No result-driven iteration')
    active=receipt.get('active_iteration_seconds')
    if isinstance(active,bool) or not isinstance(active,(int,float)) or not math.isfinite(active) or not 0<=active<=18000:raise ValueError('Author iteration exceeds five hours')
    if receipt.get('difficulty_viable') is not True:raise ValueError('Direction abandoned: difficulty not viable')
    if not receipt.get('evidence_files'):raise ValueError('Missing actual execution evidence')
    for entry in receipt['evidence_files']:
        if hashlib.sha256(read_operator_file(entry['path'])).hexdigest()!=entry['sha256']:raise ValueError('Invalid operator evidence digest')
    return receipt

def approved(commit,task):
    key=commit+'-'+__import__('hashlib').sha256(task.encode()).hexdigest()[:16]
    p=W/'.state/science-author-preflight'/ (key+'.json')
    if not p.exists():return False
    validate_receipt(json.loads(read_operator_file(p,1024*1024)),commit,task)
    return True
