"""Preinstall verified user-space environment separately in every role root."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
W=Path('/mnt/data/zhanglinfeng/workspace')
PACKAGES=['python=3.11','pip','numpy','scipy','pandas','sympy','matplotlib-base','scikit-learn','netcdf4','astropy','h5py','pytest','requests','pyyaml','pillow','cmake','make','pkg-config','c-compiler','cxx-compiler','git','curl','coreutils','findutils','grep','sed','gawk','tar','gzip','bzip2','xz','unzip','ca-certificates']
def main():
    cfg=json.loads((W/'.state/science-role-broker/config.json').read_text())
    for name,r in cfg['roles'].items():
        root=Path(r['root']);prefix=root/'home/role/.local/env'
        if not (prefix/'gewu-preinstalled-v1.json').exists():
            # Fresh independent files; conda always rewrites the prefix on install.
            command=['chroot','--userspec='+str(r['uid'])+':'+str(r['gid']),str(root),'/usr/bin/env','-i','HOME=/home/role','TMPDIR=/tmp','PATH=/usr/local/bin:/usr/bin:/bin','MAMBA_ROOT_PREFIX=/home/role/.local/mamba','/usr/local/bin/role-install',*PACKAGES]
            log=W/'.state/universe-maintenance'/('preinstall-'+name+'.log')
            with log.open('w') as out:
                result=subprocess.run(command,stdout=out,stderr=out,timeout=7200)
            if result.returncode:raise RuntimeError(name+' preinstall failed; inspect private log')
        probe=['chroot','--userspec='+str(r['uid'])+':'+str(r['gid']),str(root),'/usr/bin/env','-i','HOME=/home/role','TMPDIR=/tmp','PATH=/home/role/.local/env/bin:/usr/local/bin:/usr/bin:/bin','/bin/bash','-o','pipefail','-c',
               'set -e; python -c "import numpy,scipy,pandas,sympy,matplotlib,sklearn,netCDF4,astropy,h5py,pytest,requests,yaml,PIL; assert numpy.arange(5).sum()==10"; command -v cmake; command -v make; command -v curl; command -v seq; command -v nohup; printf "#include <iostream>\\nint main(){std::cout << 42;}\\n" > /tmp/gewu-preinstall.cpp; compiler=$(find /home/role/.local/env/bin -maxdepth 1 -name "*-conda-linux-gnu-c++" -print -quit); test -n "$compiler"; "$compiler" /tmp/gewu-preinstall.cpp -o /tmp/gewu-preinstall; test "$(/tmp/gewu-preinstall)" = 42; rm /tmp/gewu-preinstall.cpp /tmp/gewu-preinstall']
        result=subprocess.run(probe,capture_output=True,text=True,timeout=120)
        log=W/'.state/universe-maintenance'/('verify-'+name+'.log')
        log.write_text(result.stdout+'\n'+result.stderr)
        if result.returncode:raise RuntimeError(name+' environment verification failed')
        (prefix/'gewu-preinstalled-v1.json').write_text(json.dumps({'packages':PACKAGES,'imports_and_cpp_verified':True}))
        print(name+' installed',flush=True)
if __name__=='__main__':main()
