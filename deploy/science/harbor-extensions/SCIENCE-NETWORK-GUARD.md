# Experimental Science verifier process guard

`science_guarded_ack.ScienceGuardedACK` is opt-in and is not installed in the production launcher. It wraps every verifier `exec` entry point with `no_network_exec.py` when the task requests `no-network`. Runtime public networking remains unchanged. No upstream task or verifier is edited.

The launcher validates the Linux x86_64 audit architecture, rejects x32, closes non-standard inherited descriptors, refuses socket-backed standard descriptors, enables no_new_privs, and installs an inherited seccomp filter. Socket/socketpair, io_uring and cross-process descriptor/memory acquisition are refused. Local host tests exercise child exec and normal file I/O; an ACS probe exercised socket families, io_uring and child inheritance.

This enforces process-tree socket creation restrictions, not Pod-wide networking. It requires a fresh dedicated verifier with no untrusted background services or sidecars. Reused pools and unsupported architectures are refused. Shell startup before the trusted wrapper, artifact destinations, inherited process state, full result collection and original task numerical behavior still require integration review. The original ACK adapter remains unchanged. Do not claim complete no-network task validation from the capability probe alone.

Current evidence lives privately under `.state/harbor-eval/`: `netns-probe-4043d7a8.json`, `seccomp-local-validation.json`, and `guarded-ack-local-check.json`.

The experimental adapter now restricts verifier upload destinations to `/workspace/stacking_submission`, matching only the selected frozen stacking task. Absolute normalized paths are required; symlinks and special files in host upload trees are refused. Local checks cover valid artifacts, root-home overwrite, traversal, relative paths, and symlink rejection. Other Science tasks need their own reviewed artifact roots before this adapter can be reused.

Hardening now requires non-privileged execution, no privilege escalation, all capabilities dropped, and a read-only root filesystem. Only /tmp, /logs, and /workspace get fresh writable emptyDir mounts. Tests must be baked into the verifier image (tests_materialization=baked); live uploads to /tests are refused. ACS hardened adapter revalidation passed in guarded-ack-9f43aa47: normal command, socket denial, upload/download roundtrip, and cleanup. A direct root-write negative check passed in guarded-ack-8b1eda90, together with socket denial, normal exec, upload/download and cleanup. Full Science task validation remains pending.
