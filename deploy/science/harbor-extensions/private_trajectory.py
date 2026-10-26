"""Controller-private, opt-in trajectory retention; never a role export."""
import hashlib
import json
from pathlib import Path
import re
import stat
from harbor.agents.installed.mini_swe_agent import convert_mini_swe_agent_to_atif

W = Path('/mnt/data/zhanglinfeng/workspace')
ROOT = W / '.state/science-private-trajectories'


def private_directory(directory):
    path = Path(directory)
    if ROOT.is_symlink() or path.is_symlink() or path.parent.resolve() != ROOT.resolve() or path.resolve() == ROOT.resolve():
        raise ValueError('Private trajectory destination refused')
    for item in [ROOT, path]:
        info = item.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError('Private trajectory directory ownership/mode refused')
    return path


def save_json(path, value):
    with path.open('x') as stream:
        path.chmod(0o600)
        json.dump(value, stream, indent=2)
        stream.write('\n')


async def retain(environment, directory, secrets=()):
    path = private_directory(directory)
    identity_path = path/'identity.json'
    if identity_path.is_symlink() or identity_path.stat().st_uid != 0 or stat.S_IMODE(identity_path.stat().st_mode) != 0o600:
        raise ValueError('Private trajectory identity ownership/mode refused')
    identity = json.loads(identity_path.read_text())
    if not re.fullmatch('[a-f0-9]{64}', identity.get('snapshot_sha256','')) or identity.get('provider') != 'dawnfm' or identity.get('model') != 'deepseek-v4.1-flash-1017':
        raise ValueError('Private trajectory identity refused')
    raw_path = path/'mini-swe-agent.trajectory.json'
    if raw_path.exists() or raw_path.is_symlink():
        raise ValueError('Private trajectory destination must be fresh')
    raw_path.touch(mode=0o600)
    await environment.download_file('/logs/agent/mini-swe-agent.trajectory.json', raw_path)
    info = raw_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_size > 20*1024*1024:
        raise ValueError('Private trajectory file type/size refused')
    raw_path.chmod(0o600)
    raw = raw_path.read_bytes()
    if any(value and str(value).encode() in raw for value in secrets) or b'-----BEGIN PRIVATE KEY-----' in raw or b'-----BEGIN OPENSSH PRIVATE KEY-----' in raw:
        save_json(path/'retention.json', {'review_ready':False,'known_credential_detected':True,'scientific_acceptance':False})
        raise ValueError('Private trajectory contains known credential material; private quarantine only')
    data = json.loads(raw)
    if (data.get('info',{}).get('config',{}).get('model',{}).get('model_name')) != 'openai/'+identity['model']:
        raise ValueError('Retained trajectory model differs from registered provider/model')
    atif = convert_mini_swe_agent_to_atif(data, path.name).to_json_dict()
    if not atif.get('steps'):
        raise ValueError('Retained trajectory has no ATIF steps')
    save_json(path/'trajectory.json', atif)
    manifest = {'snapshot_sha256':identity['snapshot_sha256'],'identity_sha256':hashlib.sha256(identity_path.read_bytes()).hexdigest(),'raw_sha256':hashlib.sha256(raw).hexdigest(),'atif_sha256':hashlib.sha256((path/'trajectory.json').read_bytes()).hexdigest(),'schema_version':atif['schema_version'],'model':identity['model'],'review_ready':True,'credential_scan':'known runtime credential values and private-key markers only; not an exhaustive secret audit','raw_trajectory_exported_to_roles':False,'scientific_acceptance':False}
    save_json(path/'retention.json', manifest)
    return manifest
