# Manual role reset

Run from the gewu-multiverse repository as the host operator. This is a CLI feature, not a website button or automatic intervention service.

```bash
python3 deploy/science/role_progress_review.py author-02
python3 deploy/science/role_reset.py author-02 \
  --reason 'Repeated tuning has not resolved the geometry invariant' \
  --next-action 'Keep the old prototype as evidence. Abandon this direction and start a new candidate.'
# Inspect the dry-run receipt, then repeat with --apply to execute.
```

The review command emits advisory hints and never signals processes. A high failure count may be intentional negative-control testing. A long job may be making useful progress. Human review decides whether to reset.

Reset preserves workspace files, branches, idea time ledgers and archived transcripts. It backs up the previous instruction under workspace .state/science-role-reset with mode 0600, then replaces a bounded operator directive in instruction.md. It signals verified model runners identified by controller UID, run path and --run-agent, plus processes owned by the role's dedicated non-root UID. SIGTERM is followed by SIGKILL only for the same captured process identities that survive the grace period. PID reuse is checked using start ticks and pidfds.

Role reset terminates local role work; an installation or local write in progress may be interrupted. It does not delete workspaces, reset Git, erase prior evidence, replenish an idea budget, or terminate operator-owned ACS evaluations. Evaluate those cloud jobs separately.

Fresh model context is supplied by the controller's next native session. The CLI does not launch an unmanaged second runner or change the desired started/stopped state. reset_ready means targeted cleanup completed and the next-session instruction was written, not that restart succeeded. Verify a new run directory and the instruction digest before claiming reset complete. If the controller is blocked, diagnose that separately.

Current validation: five unit/process tests, including real disposable-process termination, plus three advisory tests passed. author-02 dry run found no live process. No production role was killed during feature validation. Concurrent controller session launches are not atomically paused by this CLI; inspect the newly started run if reset coincides with a launch. A future engine-level reset command should coordinate this transition in one controller transaction.
