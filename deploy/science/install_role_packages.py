import argparse,json,os,shutil,subprocess,re
from pathlib import Path
W=Path('/mnt/data/zhanglinfeng/workspace')
GUIDE='''# 独立软件环境
可以自行下载安装依赖，不要因为缺少 NumPy/SciPy 而放弃任务。
运行 role-install python numpy scipy 或 role-install cmake cxx-compiler。
环境位于 /home/role/.local/env，缓存和包独立，不影响其他角色。
PyPI 包使用 /home/role/.local/env/bin/python -m pip install PACKAGE。
需要内核模块或宿主机 root 的软件不支持；网络失败请记录真实错误。
'''
def provision(root,uid,gid,binary):
    root=Path(root)
    for dependency in re.findall(r'(/[^ ]+) \(0x', subprocess.check_output(['ldd',str(binary)],text=True)):
        source=Path(dependency); dest=root/source.relative_to('/')
        if not dest.exists():
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest);dest.chmod(0o755)
    target=root/'usr/local/bin/micromamba';target.unlink(missing_ok=True)
    shutil.copyfile(binary,target);target.chmod(0o755)
    wrapper=root/'usr/local/bin/role-install';wrapper.unlink(missing_ok=True)
    wrapper.write_text('''#!/bin/bash
set -e
unset PIP_USER PYTHONUSERBASE
export MAMBA_EXTRACT_THREADS=1
export MAMBA_ROOT_PREFIX=/home/role/.local/mamba
p=/home/role/.local/env
if [ -f "$p/conda-meta/history" ]; then action=install; else action=create; fi
exec /usr/local/bin/micromamba "$action" -y -p "$p" -c conda-forge "$@"
''');wrapper.chmod(0o755)
    dispatcher=root/'usr/local/bin/role-self-exe'
    dispatcher.write_text('#!/bin/bash'+chr(10)+'if [ "$1" = extract ] || [ "$2" = extract ] || [ "$1" = package ]; then exec /usr/local/bin/micromamba "$@"; else exec /usr/local/bin/codex "$@"; fi'+chr(10));dispatcher.chmod(0o755)
    executable=root/'proc/self/exe';executable.unlink(missing_ok=True);executable.symlink_to('/usr/local/bin/role-self-exe')
    if not (root/'bin/sh').exists(): (root/'bin/sh').symlink_to('/bin/bash')
    for name in ['.local','.local/bin','.local/mamba','.cache','.cache/pip']:
        d=root/'home/role'/name;d.mkdir(parents=True,exist_ok=True);os.chown(d,uid,gid)
    (root/'workspace/SOFTWARE-ENVIRONMENT.md').write_text(GUIDE)
    instruction=root/'instruction.md'
    if instruction.exists() and '独立软件环境' not in instruction.read_text(): instruction.write_text(instruction.read_text()+chr(10)+GUIDE)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--binary',type=Path,required=True);args=a.parse_args()
    config=json.loads((W/'.state/science-role-broker/config.json').read_text())
    for name,role in config['roles'].items():
        provision(role['root'],role['uid'],role['gid'],args.binary);print(name+' provisioned',flush=True)
