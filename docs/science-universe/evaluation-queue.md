# Registered solver evaluation queue

The isolated evaluator can submit a solver trial without obtaining host model,
ACR or ACS credentials. The root operator worker accepts IDs and snapshot hashes,
not shell commands, model names or configuration paths. It runs only a frozen
operator-registered snapshot and a hash-bound trusted configuration.

Inside the evaluator chroot:

- `/evaluation/catalog.json`: evaluation IDs and snapshot hashes.
- `/evaluation/inbox/<job_id>.json`: evaluator-owned request, submitted atomically.
- `/evaluation/results/<job_id>.json`: root-owned aggregate result, readable by evaluator.

A job ID is32lowercase hex characters. The JSON must have exactly these keys:

```json
{"job_id":"<32 hex>","evaluation_id":"calibration-v1","snapshot_sha256":"<catalog hash>"}
```

Author and curator chroots do not contain this queue. Requests with foreign UID,
extra command/model fields, wrong hashes, changed templates or symlinks are
refused. The snapshot cannot contain links or special files. Registered images
must use digest-pinned Shanghai ACR project images; execution uses direct ACS
Pods, one attempt/concurrency1/retries0, the designated DawnFM model and the
aggregate-only harness. API keys remain placeholders in the registered template.

Every admitted job consumes a durable UTC-day dispatch allowance, including
failures and cancellations. The installed operator configuration allows3jobs/day.
Unconfirmed cleanup in a previous job blocks further dispatch. There is one
worker lock. Results never assert scientific acceptance: `solver_complete`,
`mock_complete` and `cancelled` are different statuses, all with
`quality_acceptance=false`. Raw solver trajectories are not exported.

`prepare_evaluation_queue.py` bootstraps the frozen calibration infrastructure
pilot once and refuses to overwrite an existing configuration. Private configs
and job state live under workspace `.config/science-evaluation` and
`.state/science-evaluation-queue`; they are not committed. The installed start
script starts the worker as root, checks its private readiness PID, runs the UI
as nobody, and terminates/waits for the worker before stopping the command broker.
An active guard receives SIGTERM and performs its resource cleanup before exit.

Operator checks (controller/broker stopped, workspace Python3.12):

```bash
PYTHONDONTWRITEBYTECODE=1 acs-harbor-test/.venv/bin/python \
  gewu-multiverse/deploy/science/test_evaluation_queue.py
```

This uses mock execution only; no LLM or ACS launch. It still exercises actual
role chroot submission and result reading. The worker supports explicit `--mock`
for offline checks; such results cannot be reported as live evidence.

A real evaluator-submitted trial completed with DawnFM
`deepseek-v4.1-flash-1017`, reward1/errors0,9288input/2104output tokens and4native
tool calls; cleanup was confirmed and the evaluator read the aggregate result.
A separate test terminated the worker after a real Pod appeared: cancelled,
reward unknown, cleanup confirmed, known Pod404. It is not a difficulty sample.
Installed UI start/stop with the worker also passed without enabling roles.

The queue dispatches registered solver trials and the quality diagnostic route
described below. It does not build new candidate images, automatically register
author commits, adjudicate factual correctness, run semantic novelty reviews,
produce acceptance receipts or merge tasks. Those
workflow stages still require implementation/validation before unattended
scientific production can be declared ready. The calibration task remains an
infrastructure pilot, not an accepted scientific task.


## Register another immutable task (operator)

`register_evaluation.py` accepts `--evaluation-id`, `--repo`, `--commit`
(full 40-character commit), `--task-path` (relative directory), and `--template`
(root-owned trusted solver configuration). Run with the controller stopped.
The tool reads Git objects rather than the mutable checkout, rejects links and
special files, requires standard Harbor files, and preserves source commit/path
in private provenance. It freezes the snapshot, rewrites the dataset selection,
validates the existing designated-provider/image rules, and publishes only the
ID/hash in the evaluator catalog. Existing IDs cannot be overwritten.

This is operator registration, not automatic author registration or a build
service. The operator must first verify that the trusted template's digest-pinned
images match the task environment. No image/task correspondence or scientific
acceptance is inferred by this command. If publication of the catalog fails after
registry persistence, repair the catalog from the registry; do not reuse the ID.
Offline boundary checks: `deploy/science/test_register_evaluation.py`.


## Independent static quality review (operator)

`review_registered_task.py --evaluation-id <id> --output <fresh-private-dir>`
loads the registered immutable task and the private evaluator rubric. Explicitly
source the workspace DawnFM environment before invoking it. The provider key
stays in the controller process; no role shell or task code runs. All UTF-8 task
files are supplied as untrusted data. Oversize or binary inputs are refused,
not silently omitted. A response must finish normally and parse directly as
valid rubric JSON; no prose stripping or formatting-repair acceptance occurs.
The snapshot hash is rechecked after review. Response and review files remain
private, mode0600, below a mode0700 output directory.

This is independent complete-static-input quality evidence only. It does not
prove runtime correctness, benchmark novelty, empirical difficulty or release
acceptance, and it is not yet dispatched by the role queue. Offline input-limit
checks live in `test_review_registered_task.py`; live evidence is separate.


## Fixed benchmark comparison corpus

`prepare_reference_corpus.py --tb4-commit <full-hash> --science-commit
<full-hash> --output <fresh-private-dir>` extracts every tracked
`*/instruction.md` directly from the two local benchmark Git commits. It records
each source path, commit, Git blob and SHA256; dirty checkout files are ignored.
Links are refused. Corpus text and manifest stay in private workspace storage,
not in this repository. Source-pinning checks: `test_reference_corpus.py`.

The initial corpus contains223TB4 and158TBScience instructions. This prepares
comparison input; it does not perform a semantic review or assert novelty.


DawnFM compatibility note: for this static Chat review the request explicitly
uses `thinking: {"type":"disabled"}` and JSON-object response format. A small
live probe verified normal JSON output with no reasoning content. Earlier
reasoning-enabled reviews exhausted10000/24000tokens without an answer, and a
separate normal-stop response contained invalid JSON; all were refused. The
thinking-disabled review is a distinct method and must be reported as such,
not as equivalent to a reasoning-enabled or tool-capable review.

A fresh complete static review subsequently passed direct JSON and rubric
validation (thinking disabled):47.5/100, confirmed_blocker,12929input/2399output
tokens. A preceding valid-JSON response omitted the mandatory limitations field
and was rejected. The successful review is still model-produced evidence:
its factual claims need checking, and it does not establish dynamic correctness,
novelty, difficulty or acceptance.

A factual audit of that report found incorrect numerical claims and unsupported
scientific inferences. Therefore the47.5score and blocker verdict remain
untrusted diagnostic output, not an approved quality decision. Schema-valid
output alone does not qualify this reviewer for unattended production.
Credential-free isolated calculation tools and evidence verification are still
required; this static entry point does not complete the production review gate.

## Credential-free calculation tools (operator)

Prepare a fresh task-matched tool root with `prepare_review_chroot.py
--tools-only --uid 21012 --root <private-review-state>/root --task <snapshot>`.
The reserved private state directory is workspace `.state/science-review-tools`.
Tools-only preparation copies no Codex provider configuration or credentials.
The root contains standard shell/Python utilities, read-only task files, and
writable scratch. It does not mount host proc. Network remains permitted.

`review_registered_task.py --tool-root <prepared-root>` enables `review_shell`.
The controller alone calls DawnFM. Each command runs as UID/GID21012 with a clean
environment through the existing nonroot chroot executor. This UID is distinct
from all role UIDs. A global session lock prevents concurrent reviewers sharing
that UID, the staged task hash must match the registered snapshot, and scratch
is reset at session entry. The executor watches a controller connection in a
separate helper; EOF cleans commands even if the controller is killed. Detached
children are cleaned by dedicated-UID process handles.

The review is limited to10shell calls and12model turns. Every issue must cite a
successful actual tool-call ID and an exact output substring. Missing/fabricated
references are rejected. Full commands/results and model responses stay private;
provider keys never enter tool environments. Aggregate provider token usage and
tool-call count are recorded separately from solver difficulty metrics.

`test_review_tools.py` checks actual credential-free chroot calculations,
read-only task access, process cleanup after detachment and controller SIGKILL,
concurrent-session rejection and fabricated evidence rejection. It makes no LLM
or ACS calls. Evidence-reference validation proves a quotation exists, not that
the command or scientific inference is correct. Factual audit, dynamic task
execution, semantic comparison and final acceptance are separate gates. This
operator entry point is now available through the diagnostic queue route below;
that route does not grant acceptance.

Tool-backed final reports use the schema-bearing `submit_review` function.
After10shell calls the controller removes the shell tool and forces submission.
An invalid citation may be resubmitted once against the unchanged actual output;
both rejected and resubmitted model responses are retained. This is continuation
of the same review, not a new independent sample. Quotation checks still do not
prove scientific correctness. Mock driver integration explicitly tests accepted
submission, token aggregation and persistent fabricated-evidence refusal.

Live tool review status: three attempts executed real isolated calculations but
none produced an accepted final report (call-budget/final JSON structure,
fabricated call IDs, then malformed function arguments). These are failed
review attempts, not qualified reviewer evidence. Offline six-tool-boundary
tests and mock driver integration pass; live reviewer readiness is still open.

## Continue an interrupted review from retained evidence

`finalize_review_evidence.py --source <private-review-dir> --output
<fresh-private-dir> --json-body` executes no tools. It loads root-owned retained
metadata/output, revalidates the registered task identity, and supplies the
complete task, original actual outputs and explicit report schema to DawnFM.
It permits one correction against the same evidence and retains every response.
No result is counted as a new independent review, and acceptance flags remain
false. The function-argument mode is also available; a live attempt in that mode
exhausted its output limit and was rejected. JSON-body finalization of the same
retained v3 evidence subsequently passed schema and exact citation validation.
Mock integration tests cover both modes and persistent provenance.

The resulting56.25score/no_blocker_found verdict still did not qualify the
reviewer: factual audit showed a deliberate +0.001 scale perturbation was
misrepresented as a legitimate alternative MAD convention. The quote was real,
but its interpretation was unsupported. This is recorded as diagnostic evidence,
not an accepted scientific judgment. `review_diagnostic_status.py` creates a
hash-bound nonacceptance summary for a report and its factual audit; even a score
of100and no_blocker_found cannot make its release_eligible flag true. This
summary is not a release receipt, signature, quality gate or role-queue result.

## Quality diagnostic queue dispatch

The worker also supports operator-registered `quality_diagnostic` entries.
`register_quality_diagnostic.py --source-evaluation-id <solver-id>
--evaluation-id <new-id> --review-root <prepared-root>` reuses an existing frozen
solver snapshot/configuration and requires a hash-matching root-owned tool root
under private review state. Registration cannot overwrite an ID. Only the ID,
hash and diagnostic purpose enter the evaluator catalog; requests retain exactly
the original three-field schema. No caller may choose commands/provider/root.

The fixed `run-quality-diagnostic` wrapper sources the designated workspace LLM
account controller-side. It runs a new isolated tool review and, only if that
fails with retained evidence, one JSON-body finalization of the same review.
Failures remain in private attempts/logs. The evaluator result includes the
model's diagnostic review and usage, never raw tool logs, controller paths,
prompts or provider credentials. No ACS resources are created by this route.
Results are `quality_diagnostic_complete` or `quality_diagnostic_failed`, with
`quality_acceptance=false`, `scientific_acceptance=false`,
`release_eligible=false` and `factual_verification_required=true`.

Quality diagnostics share the durable daily dispatch allowance and previous-job
cleanup gate with solver trials. Cancellation waits for dedicated reviewer UID
cleanup; unconfirmed cleanup blocks subsequent jobs. Offline mocked quality
queue tests cover route selection, a missing report and unknown dispatch refusal.
Mock orchestration tests cover failed initial review, same-evidence finalization,
and nonacceptance. These are separate from live queue evidence. This diagnostic
route does not complete semantic comparison, factual adjudication, fresh task
builds, dynamic verification or scientific acceptance.

Live diagnostic dispatch passed: evaluator submitted and read back job
`0bc28e9253f04957a6dc453edd0495a3` without a provider key. It made9shell calls;
the first review failed final validation and same-evidence JSON finalization
succeeded. Cleanup confirmed; no ACS resources launched. Private retained
provider responses account for156902input/17691output tokens in the initial
review (8requests), plus19978input/1678output in finalization (1request).
These are reviewer costs, not solver difficulty metrics. The live role summary
omitted source-review usage; it is preserved in separate private evidence and
the forwarding correction is covered by runner tests. Diagnostic score56.25
and no_blocker_found remain model claims requiring factual verification.
