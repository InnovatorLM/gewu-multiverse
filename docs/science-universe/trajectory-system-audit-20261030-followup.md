# Universe trajectory system audit — 2026-10-30 follow-up

Scope: latest archived sessions for author-01..04, evaluator-01..02 and curator. Read event counts, terminal records, long command results, final handoffs, and selected failing tool calls. This is a targeted audit, not a review of every message or task correctness. No new model trials were launched.

## Evidence

| Role | Run | Model replies | Terminal outcome |
|---|---|---:|---|
| author-01 | run-1793356113987-0021 | 251 | refused, exit 0; abandoned prototypes with measurements |
| author-02 | run-1793353638143-0003 | 495 | timed_out after four-hour session; incomplete eclipse prototype |
| author-03 | run-1793353638876-0004 | 293 | refused, exit 0; honest incomplete handoff |
| author-04 | run-1793353639636-0005 | 257 | refused, exit 0; PR 33 submitted with explicit container gap |
| evaluator-01 | run-1793351384914-0034 | 1 | failed: max_turns=1 |
| evaluator-02 | run-1793351384921-0035 | 1 | failed: max_turns=1 |
| curator | run-1793356808589-0028 | 9 | succeeded; no new event |

Primary evidence: universes/my-terminal-bench-science/.state/gewu-multiverse/<role>/<run>/transcript.jsonl, relative to workspace root. These archives are private; do not copy raw model request bodies or credentials into public reports.

## P0: actual capabilities and durable execution

1. All seven sampled runs logged skills_discovered with an empty skills list. Authors 01, 03 and 04 explicitly reported missing container tooling. Author-04 never called role-acs-selftest in this sampled session. Later installation may exist, but these sessions do not prove it was loaded. Require startup capability receipts: discovered skill versions, reachable selftest API, executable dependency probes, and instruction digest. Route container execution through the operator service; isolated authors do not need host Docker privileges.
2. The latest evaluator sessions are old one-turn failures, not successful reviews under current settings. Verify a fresh session and effective limits before considering the evaluator fixed. Four authors and both evaluators were waiting at the preceding live status check. Audit dispatch transitions and wakeup reasons. Do not infer the scheduler root cause from transcript outcomes alone.
3. author_selftest_worker.py returns when either result or work directory exists; this can strand interrupted jobs. It also rewrites non-scratch FROM references to one base image. Add durable per-stage state, leases, idempotent resume, preserved source/archive hashes, author-visible sanitized logs and terminal result receipts. Preserve Dockerfile semantics; resolve original bases to digests instead of changing them silently.

## P1: time accounting and feedback

4. author-02 tool turns 142 and 287 took 5,787,488 ms and 3,622,195 ms respectively, despite the model system prompt claiming a 120-second shell limit and background cleanup. Author-04 turn 21 spent 1,794,260 ms installing SciPy; turn 20 spent 443,206 ms on NumPy with about two seconds user CPU reported. These are observations, not proof of a storage bottleneck. Publish real effective command policy; use resumable jobs, progress checkpoints and targeted stalled-job intervention. Distinguish healthy long computation from no-progress hangs.
5. Author-02 hit the four-hour session limit. This differs from the user policy of five hours active iteration per idea excluding ACS wait time; both need separate clocks and explicit restart/abandon transitions. Author-04 left its idea clock active while waiting for container evidence. Automatically pause the active-iteration clock during platform waits, persist it across sessions and resume through a concrete followup.
6. Preinstalled packages were not reliably reused: author-04 created fresh virtual environments and downloaded NumPy/SciPy/pytest. Provide a verified default Python path and fast import checks, plus per-role writable package support and a local wheel cache. Avoid mutating a running role environment. preinstall_role_runtime.py currently probes click/typer/pydantic/jinja2/psutil without explicitly requesting them in PACKAGES; fix consistency before declaring the new environment verified.
7. Repeated string substitutions produced shape mismatches, syntax errors and domain errors. Author-01 tool turn 242 contained a traceback but returned exit 0. Author-02 modified geometry and tests while outputs still failed. Use fail-fast shell mode where suitable, small deterministic smoke cases, explicit data schema/invariants, and separate diagnostic logs from success receipts. Expected negative-control failures must remain distinguishable from infrastructure failures.

## P1: task validity and handoff

8. Author-04 reports simulated reference solve 27/27, and negative controls failing. This is useful preliminary evidence but not actual image build, clean container replay, or ACS model success rate. Bind formal evaluation to commit, task inventory hash and image digest; require clean oracle and empty/bad-output controls, then five independent designated-model runs. Its threshold calibration after inspecting method variants needs independent review and holdout cases; it is not evidence of cheating by itself.
9. PR 33 was open in Forgejo but absent from the existing review ledger at the previous check. Add explicit states for draft, waiting platform, selftest passed, ready review, assigned and complete. A platform build request should not be treated as a completed formal submission or trigger duplicate evaluator jobs.
10. Obsolete policy appears in artifacts: author-01 read PILOT-REVIEW-FEEDBACK with below50/ideally below30 language; authors still discuss licensing as unresolved despite current user scope excluding license gating. Keep one versioned policy source and invalidate stale feedback when superseded. Current evaluator criterion is five designated-model rollouts with pass rate <=60%, with infrastructure failures classified separately.

## P2: observability and evidence size

11. Author-04 successfully submitted a PR and ended with Session complete, yet run outcome was refused; authors 01/03 also used honest incomplete handoffs classified refused. This makes the outcome unsuitable as a business-state label. Use structured completion receipts: delivered, pivoted, waiting_platform, no_work, model_refusal, infra_failure, timeout. The classifier and scheduler linkage require code-level verification before assigning causality.
12. Latest sampled author transcripts are roughly 86–124 MB each. model_request events serialize accumulated message history, and replies also contain structured and raw bodies. Keep immutable append-only events and request metadata/hashes; store full request bodies separately under a deliberate retention policy, preserve all unique actions/results, and measure growth. This improves audit readability without discarding actual trajectories.

## Positive observations

Authors 01 and 03 abandoned scientifically weak or ambiguous directions instead of silently tightening hidden requirements. Author-04 recorded both passing reference and failing negative controls, two iteration rounds, and explicitly disclosed no real container run. Hundreds of model replies and tool calls show substantial model activity; these sessions do not support attributing the present idle state to a total DawnFM API outage.

## Recommended order and acceptance

First verify startup capabilities and repair/replay the durable author selftest queue. Then replay PR 33 at its exact commit through clean container controls and exclusive evaluation assignment. Next verify scheduler wakeup with fresh evaluator sessions, separate timing clocks and resumable command jobs. Finally improve dependency reuse, frozen task invariants, structured outcomes and incremental trajectory storage. This audit changes no running role, model, resource limit or task submission.
