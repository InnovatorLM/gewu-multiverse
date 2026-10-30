"""Provision per-author request/result boundary and CLI."""
import argparse,json,os,shutil
from pathlib import Path
from evaluation_queue import W
def install(root,uid,gid):
 root=Path(root);base=root/'selftest';base.mkdir(exist_ok=True);base.chmod(0o755)
 for name in ['inbox','results']:
  d=base/name;d.mkdir(exist_ok=True);os.chown(d,uid if name=='inbox' else 0,gid);d.chmod(0o700 if name=='inbox' else 0o750)
 target=root/'usr/local/bin/role-acs-selftest';target.unlink(missing_ok=True);shutil.copyfile(Path(__file__).with_name('role_acs_selftest.py'),target);target.chmod(0o755)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=W/'.state/science-role-broker/config.json');args=p.parse_args()
 config=json.loads(args.config.read_text())
 for role,e in config['roles'].items():
  if role.startswith('author-'):install(e['root'],e['uid'],e['gid']);print(role,'selftest queue installed')
