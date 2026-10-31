"""Apply public dispatch policy; retain existing private runtime instructions as backups."""
import json,shutil
from pathlib import Path
W=Path('/mnt/data/zhanglinfeng/workspace')
def install(root,role):
    if not role.startswith('evaluator-'):return
    root=Path(root);source=Path(__file__).resolve().parents[2]
    p=root/'instruction.md';backup=root/'instruction.pre-dispatch.bak'
    if p.exists() and not backup.exists():shutil.copyfile(p,backup);backup.chmod(0o600)
    p.write_text((source/'docs/science-universe/evaluator-dispatch-policy.md').read_text())
    target=root/'usr/local/bin/role-review-status';target.unlink(missing_ok=True);shutil.copyfile(Path(__file__).with_name('role_review_status.py'),target);target.chmod(0o755)
if __name__=='__main__':
    for name,role in json.loads((W/'.state/science-role-broker/config.json').read_text())['roles'].items():install(role['root'],name)
