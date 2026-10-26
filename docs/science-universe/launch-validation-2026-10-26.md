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
recheck passed. A full rerun is in progress. Mock tests are distinct from live
DawnFM review and ACS trials.

Remaining launch work: production role runtime/credentials wiring, strict
review output, meaningful harder candidates, semantic novelty review against
fixed TB-Science and TB4 versions, protected Git push denial test, enforced
budgets, curator gate and final full regression/resource audit.
