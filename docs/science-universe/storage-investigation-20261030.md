# Universe role storage investigation and repair

## Plan

1. Identify the workspace filesystem and check active writers before modifying role environments.
2. Measure bounded create/read/rename and sequential write/fsync/read behavior, including inside a real role chroot.
3. Repair interrupted package installations without concurrent writes to the same prefix.
4. Make each role's workspace, cache, runs, temporary directory and HOME independently writable and persistent; verify isolation as the configured UIDs.
5. Give every role a complete independent software environment, validated by imports, command availability and C++ compile/run.
6. Exercise real session preparation, repository reuse and Git fetch for every role, then inspect the final automated verification state. Keep production scheduling off until this passes.

## Findings

The workspace is on the Shanghai CPFS FUSE mount `fuse.aliyun-alinas-efc`.
Bounded probes completed successfully, but CPFS metadata operations are much
slower than local NVMe: creating/reading/renaming 100 x 4 KiB files took 7.56 s
on CPFS and 0.0025 s on the comparison filesystem. A 16 MiB write, fsync and
read/hash took 0.586 s and 0.061 s respectively. Repeating inside author-02's
actual chroot took 7.72 s and 0.315 s. These results demonstrate high metadata
latency, not a corrupt or unavailable filesystem. The volume showed over 100
TiB available during repair, and writes/fsync/readback succeeded.

The long environment unpack is storage-bound rather than CPU-bound. A live
`tar` extraction spent multiple minutes in uninterruptible I/O wait while its
accumulated CPU time was only about 0.27 seconds; its read/write counters grew
as it progressed. Both archive and destination live on CPFS, where each file
creation and metadata update incurs the slow path. More CPU cores are therefore
unlikely to materially reduce the observed time. An overlay/reflink shortcut
was tested: CPFS reflink returns `Operation not supported`, and overlay mounts
are denied in the current runtime. Avoid changing CPU sizing as a response to
this measured bottleneck.

An interrupted micromamba transaction was resumed under its original role UID
and prefix. A role-local install lock and global recovery lock prevent
overlapping package writers. Timeout handling now kills child processes, and a
role-owned success marker is written atomically only after package imports,
basic tools and a C++ compile/run succeed. A second installer was refused
while the lock was held. author-01..03 passed the full environment probe.

An expanded storage audit uncovered incorrect `/cache` and `/runs` ownership
on some old role roots and missing directories on others. The directories
were repaired from the broker's UID/GID configuration without deleting
contents. `/cache` is role-owned mode 0700; `/runs` is controller-owned and
role-group writable mode 2770. Provisioning code now creates these paths for
future roles. The isolation test now uses `bash -e -o pipefail`, so early
permission failures cannot be hidden by later successful commands.

## Live validation

The actual-UID persistence verifier passed all 14 roles. In each role's
`/workspace`, `/cache`, `/runs`, `/tmp` and `/home/role`, it performed a write,
fsync, rename and fresh-process readback. It also checked distinct private
directories and denied a peer role's read. Evidence:
`.state/storage-investigation/universe-persistence.json`.

Actual no-model `RealSpawner::prepare` checks passed for all 14 roles:
two preparations, private repository reuse and a subsequent Git fetch. author-04
was tested after its environment finished extracting. Logs:
`.state/storage-investigation/*session-prepare.log`.

author-02's validated environment was archived once (2.61 GB; archive SHA-256
`b25797ba2a814e4fbd8a2e11a380852aa068bfdcd4d3ef043e6f842146f3c573`) and is
being extracted into independent role-owned prefixes. CPFS does not support
reflink cloning, so role environments are copied serially rather than sharing
mutable files. The bootstrap process verifies each copy before publishing its
marker and preserves/restores the old environment on failure. Current progress
is authoritative in `.state/storage-investigation/bootstrap-status.json`;
`bootstrap.log` records completed roles. Do not infer completion from a live
process or a partial staging directory.

At the latest checkpoint, author-01..07 had verified environments and author-08
was extracting. author-07's tar extraction completed after approximately 39
minutes; its environment import/tool/C++ probe and subsequent real session
prepare/fetch both passed. The final verifier waits for the bootstrap process, then checks
all 14 role markers, reruns storage persistence, and prepares every actual
session. Its state is `.state/storage-investigation/recovery-verification.json`.
No scheduler or model calls are part of these checks. Production scheduling
remains stopped until the final verifier reports `passed: true`.

## Code and remaining gate

The repair code and test updates are pushed to the backup branch
`terminal-bench-science-backup-20261029T015224Z`, including commits `4e830b5`,
`eef5285` and `e265e99`. The preinstall, recovery-verifier and storage-probe
regression suite passed five tests; recovery-verifier unit tests are mocked and
are not a substitute for its pending live run.

Remaining: finish independent environment copies for author-05..10,
evaluator-01..03 and curator; require each full per-role probe; run the final
14-role live session and persistence verifier; check all reports and process
exit states. Keep the Universe scheduler stopped until these checks pass.
