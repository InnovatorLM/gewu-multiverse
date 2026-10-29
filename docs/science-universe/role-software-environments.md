# Independent role software environments

Each role has micromamba and role-install. Run role-install python numpy scipy pip
to create/update its personal environment, or install CLI tools and compilers
from conda-forge. Prefixes /home/role/.local/env and /home/role/.local/mamba live
inside the dedicated role chroot and belong to its UID. No shared writable
package environment is used. New provisioners install the same tools when the
workspace micromamba binary is available.

Use /home/role/.local/env/bin/python explicitly when using the currently running
broker, whose environment predates the source PATH change. The production broker
is kept intact to avoid interrupting active work. Kernel modules, privileged
host services and packages unavailable from reachable sources remain unsupported.

The chroot has no host proc mount. Its self-executable compatibility dispatcher
routes micromamba package extraction back to micromamba and Codex invocations to
Codex. Required dynamic libraries are copied into the immutable runtime. The
Git credentials and existing workspaces are never replaced by this installer.
