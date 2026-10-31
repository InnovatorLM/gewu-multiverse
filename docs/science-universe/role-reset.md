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

Current validation: eight reset tests pass, including real disposable-process termination, lifecycle lock contention and updates to both the isolated role instruction and the controller copy. Each copy keeps its own detailed policy, ownership and mode; private backups preserve both originals. Symlink/malformed copies are refused before instruction writes.

The default maintenance reset requires the launcher and its supervisor to be stopped: the launcher holds a shared lifetime lock and reset requires exclusive access. This prevents concurrent controller starts during maintenance, but is not a hot, per-role controller transaction. A successful reset receipt still does not prove that the next real model session was scheduled or read the directive; verify that separately before claiming full behavioral acceptance.

Real maintenance recovery validation (2026-10-31): a private upstream-fixture PR passed the actual author gate and immutable registration, received one exclusive assignment, and the controller cloned its new repository and started evaluator-02 after reset. Seven designated DeepSeek requests were retained; the initial request contained the exact reset ID, and the model wrote the expected nonce plus assignment identity and exited 0. Evidence is private under workspace `.state/universe-repair-20261031/reset-controller-v1/verified-evidence.json`. This verifies controller-managed recovery after maintenance, not hot per-role reset or scientific acceptance. The fixture PR/issue were closed and the test deployment stopped afterward.

Controller hold groundwork (not yet an online reset CLI): the scheduler recognizes
`<state-root>/operator-role-holds/<role>` as a fail-closed pause. The marker is
operator-managed and contains no executable instructions. It leaves the saved
started/stopped choice intact, stops a current local session through the existing
session settlement path, and prevents a replacement while present. In-flight
preparation and spawn handoff also check the hold. Removing it lets the normal
scheduler resume. Other roles and operator-owned cloud jobs are unaffected by
this gate. Do not use file presence or disappearance as proof that cleanup has
finished: an acknowledged transaction and CLI integration are still required
before claiming online reset support. This source change is not deployed by
editing the file; the installed binary must be rebuilt and validated separately.


Online protocol implementation (not yet deployed or live-validated):

```sh
GEWU_UNIVERSE_ROOT=/absolute/workspace/runtime \
python3 deploy/science/role_reset.py author-02 --online --apply \
  --reason 'operator reviewed stalled exploration' \
  --next-action 'preserve artifacts and pivot to the documented alternative'
```

`--online` takes a shared deployment lifecycle lock and an exclusive role lock,
creates a unique operator hold, and waits for a matching controller acknowledgement.
The controller acknowledges only after no active runner, preparation/spawn or
unsettled child remains. The acknowledgement binds the role, nonce and live
controller PID; the CLI also verifies controller UID, command and process identity.
Only then does it update both instruction copies and clean dedicated-role
processes. It releases the hold after successful cleanup and identity recheck.
No cloud worker is signalled. Desired Start/Stop choices and histories are preserved.

On timeout or failure the hold intentionally remains, and retries refuse to
replace it. Inspect the acknowledgement, retained instruction backups and current
processes before manual recovery; never remove an unexplained hold merely to
make the dashboard active. An old installed controller does not acknowledge this
protocol, so the CLI fails closed rather than attempting an uncoordinated reset.
A successful receipt means the hold was released, not that the next model session
has been observed; that requires a separate new-run/directive check.

Real online lifecycle validation (2026-10-31): installed binary `92f6b1f`
kept the same actual controller PID while evaluator-02 was executing a model-issued
300-second local command. `--online` received the exact quiescent acknowledgement,
updated both instruction copies, and released the role. The old runner/command
were gone; an automatically scheduled new designated DeepSeek session contained
the exact reset ID in its initial request, wrote the AFTER marker, and exited 0.
Saved desired settings were unchanged and prior trajectories remained readable.
Only evaluator-02 was enabled in this isolated test: concurrent active-role
noninterference is not established by this evidence. No cloud jobs were submitted.
One additional harmless AFTER session started before the fixture wake was marked
completed; both histories are retained. The isolated deployment was then stopped,
original instructions/settings/wakes restored, and loopback ports verified closed.
Private evidence: `.state/universe-repair-20261031/online-reset-v1/verified-evidence.json`.
