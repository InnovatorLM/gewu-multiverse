# Launch validation, 2026-10-26

Shanghai public ACR to Beijing ACS is working. The most recent controlled
DawnFM deepseek-v4.1-flash-1017 trial finished with reward 1, zero errors and
verified cleanup. Aggregate usage: 11,176 input tokens, 2,264 output tokens,
four native tool calls. Raw solver trajectories were not exported.

The role repository access matrix and distinct-UID file-read matrix passed.
Production per-role runtime wiring remains unfinished. Roles remain stopped.

The local evaluator could not use bubblewrap or Landlock in this environment.
A non-root chroot prototype now supports real Codex shell inspection, read-only
task files and hidden host credential paths without mounting host /proc.
Network access is permitted as requested. This prototype is not yet a complete
production role launcher. The regular-file /dev/null fallback supports non-PTY
exec only and must not be represented as a real device or process isolation.

The independent quality run inspected the task, actual grader and reference
solution. Its final answer included prose before JSON, which failed the strict
output contract. A separately labeled normalized diagnostic scored 61.25/100,
coverage 1, difficulty 2/5. It is not an acceptance. Main findings: unclear
residual-MAD convention, fixed outlier index, weak research difficulty and
contradictory historical status documents. Two successful solver samples do
not demonstrate the target pass rate below 30% (below 50% acceptable).

Evaluator regressions improved from 22 failures/15 errors to 2 failures/5 errors
in 153 tests. All remaining failures were addressed; the focused 27-test
recheck passed. Final full rerun: all 156 tests passed in 652 seconds.
Mock tests are distinct from live
DawnFM review and ACS trials.

Remaining launch work: production role runtime/credentials wiring, strict
review output, meaningful harder candidates, semantic novelty review against
fixed TB-Science and TB4 versions, enforced budgets, curator gate and final
launch/resource audit.

Prototype commands (operator/root, workspace-specific paths): run
`deploy/science/prepare_review_chroot.py`, then source the designated local
DawnFM env without tracing and run `deploy/science/run_chroot_quality.py`.
Preparation stages Python standard-library tools without site-packages.
The setup may not run concurrently with an active review using the same root.
`--normalize-existing` reformats the retained diagnostic only and records that
it is not a fresh review or acceptance. DawnFM rejects `--output-schema` with
`This text.format type is unavailable now`; that optional path was tested and
failed, without changing account/provider. Strict JSON parsing remains required.

Actual Git transport negative tests passed: author push to protected main was
rejected and evaluator push to a new branch was rejected. Task trees did not
change. Formatting-only follow-up produced strict valid JSON with the same
61.25 score, labeled as formatting rather than fresh review or acceptance.
Python stdlib and read-only/hidden-host-path checks inside chroot passed.
