"""Validate operator attestation before allocating evaluator work."""
import json,re,math
from pathlib import Path
W=Path('/mnt/data/zhanglinfeng/workspace')
CHECKS=('schema','container_build','container_start','author_solve','verifier_positive','verifier_negative','post_iteration_rerun')
def validate_receipt(receipt,commit,task):
    if receipt.get('commit')!=commit or receipt.get('task')!=task:raise ValueError('Stale author preflight identity')
    if not re.fullmatch(r'[a-f0-9]{64}',receipt.get('snapshot_sha256','')):raise ValueError('Missing frozen execution identity')
    if not re.fullmatch(r'.+@sha256:[a-f0-9]{64}',receipt.get('runtime_image','')):raise ValueError('Missing image digest')
    if any(receipt.get('checks',{}).get(k) is not True for k in CHECKS):raise ValueError('Author container preflight incomplete')
    if receipt.get('iteration_applied') is not True:raise ValueError('No result-driven iteration')
    active=receipt.get('active_iteration_seconds')
    if isinstance(active,bool) or not isinstance(active,(int,float)) or not math.isfinite(active) or not 0<=active<=18000:raise ValueError('Author iteration exceeds five hours')
    if receipt.get('difficulty_viable') is not True:raise ValueError('Direction abandoned: difficulty not viable')
    if not receipt.get('evidence_files'):raise ValueError('Missing actual execution evidence')
    import hashlib
    for entry in receipt['evidence_files']:
        p=Path(entry['path']);info=p.lstat()
        if p.is_symlink() or not p.resolve().is_relative_to(W) or info.st_uid!=0 or info.st_mode & 0o022 or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Invalid operator evidence')
    return receipt

def approved(commit,task):
    key=commit+'-'+__import__('hashlib').sha256(task.encode()).hexdigest()[:16]
    p=W/'.state/science-author-preflight'/ (key+'.json')
    if not p.exists():return False
    info=p.lstat()
    if p.is_symlink() or info.st_uid!=0 or info.st_mode & 0o022:raise ValueError('Untrusted preflight receipt')
    validate_receipt(json.loads(p.read_text()),commit,task)
    return True
