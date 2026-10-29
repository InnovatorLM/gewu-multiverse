#!/usr/bin/env python3
"""Live, credential-free filesystem checks of prepared author instances."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess

W = Path('/mnt/data/zhanglinfeng/workspace')
A = W / 'universes/my-terminal-bench-science/.config/gewu-multiverse/agents'
results = []
for name, uid, other in [('author-01', 21001, 'author-02'), ('author-02', 21002, 'author-01')]:
    root = A / name
    def drop():
        os.chroot(root); os.chdir('/workspace'); os.setgroups([]); os.setgid(uid); os.setuid(uid)
    checks = {
        'own_persistent_write': 'echo '+name+' > /workspace/.storage-isolation-proof; test "$(cat /workspace/.storage-isolation-proof)" = '+name,
        'private_home_cache_tmp': ': > /home/role/.storage-proof; : > /cache/.storage-proof; : > /tmp/.storage-proof',
        'public_references_readable': 'cat /references/author-instruction.md >/dev/null',
        'public_references_not_writable': 'test ! -w /references/author-instruction.md && test ! -w /references',
        'peer_host_path_not_visible': 'test ! -e '+str(A / other / 'workspace'),
        'host_credentials_not_visible': 'test ! -e '+str(W / '.config/llm/dawnfm.env'),
    }
    for label, command in checks.items():
        p = subprocess.run(['/bin/bash', '-c', command], preexec_fn=drop, capture_output=True, timeout=15)
        results.append({'instance':name, 'check':label, 'passed':p.returncode==0})
    # Distinct Unix identities cannot read peer HOME even without the chroot view.
    def uid_only():
        os.setgroups([]);os.setgid(uid);os.setuid(uid)
    p = subprocess.run(['/bin/bash','-c','test ! -r '+str(A / other / 'home/role/.storage-proof')],preexec_fn=uid_only,capture_output=True,timeout=15)
    results.append({'instance':name,'check':'peer_home_denied_by_uid','passed':p.returncode==0})
    for relative in ['workspace/.storage-isolation-proof','home/role/.storage-proof','cache/.storage-proof','tmp/.storage-proof']:
        (root/relative).unlink(missing_ok=True)
# No mutable HOME/workspace or tool inode is shared.
for relative in ['workspace','home/role','tmp','cache','bin/bash']:
    x,y=(A/n/relative for n in ['author-01','author-02'])
    results.append({'check':'distinct_inode:'+relative,'passed':(x.stat().st_dev,x.stat().st_ino)!=(y.stat().st_dev,y.stat().st_ino)})
r={'passed':all(x['passed'] for x in results),'checks':results,'scope':'live Unix/chroot storage checks; no model, Git identity or engine startup'}
(W/'.state/harbor-eval/author-storage-isolation.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r));raise SystemExit(0 if r['passed'] else 1)
