# Registered solver evaluation queue

Current comparison scope: TB4 `tasks/` contains66instructions and TBScience
`tasks/` contains72at the fixed source commits. The earlier381-file corpus also
contains CI fixtures, templates and historical directories; its broad counts
must not be represented as current benchmark task counts. The old all-file
semantic dispatch ID is retired, and the active138-task corpus is separately
hash-bound. Historical evidence below is retained with this correction.

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
(root-owned trusted solver configuration), plus required `--build-receipt`
(root-owned publication receipt). Run with the controller stopped.
The tool reads Git objects rather than the mutable checkout, rejects links and
special files, requires standard Harbor files, and preserves source commit/path
in private provenance. It freezes the snapshot, rewrites the dataset selection,
validates the existing designated-provider/image rules, and publishes only the
ID/hash in the evaluator catalog. Existing IDs cannot be overwritten.

This is operator registration, not automatic author registration or a build
service. Registration checks the receipt against the frozen commit, complete snapshot,
environment/tests hashes, harness versions, provenance labels and runtime/verifier
digests, including the Pod image override. A private receipt copy is retained.
`--disabled` retains infrastructure proof without exposing it in the dispatch
catalog. These source bindings do not prove scientific correctness or absence
of hidden answers. If publication of the catalog fails after
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

## Full fixed-corpus instruction comparison (operator)

`semantic_comparison.py --evaluation-id <registered-id> --corpus
<private-fixed-corpus> --output <fresh-private-dir>` compares the registered
candidate instruction with every manifest reference. It verifies corpus and
per-instruction hashes, both benchmark source sets, unique identities, and the
registered candidate snapshot. Batches preserve full instruction text without
truncation. Every reference must receive exactly one relation, inferred workload
comparison, explanation and exact source/candidate quotation. Missing, duplicate,
unknown references or fabricated quotations fail validation.

Requests use designated DawnFM, thinking disabled, JSON-object mode. Failed
responses remain private and up to two targeted corrections are allowed per batch. `--resume`
requires the same candidate/corpus/prompt/model identity, revalidates completed
batches, and reuses retained responses rather than silently repeating calls.
The final report includes every source commit/path/blob/SHA and provider usage
including failed responses. This operator route executes no tools, solver or
ACS resources; the queue integration below has mock coverage. It is diagnostic only:
full instruction coverage does not prove semantic judgment, implementation
originality, task quality or empirical model difficulty. Acceptance remains false.


Citation transport uses zero-based numbered source excerpts. The model selects
an actual excerpt index; the controller restores its exact original text and
validates it against the full instruction. The first direct-quotation pilot
stopped after a later batch repeatedly omitted Markdown backticks. The indexed
pilot preserves those failed responses and does not weaken exact-text checks.
Out-of-range selections receive reference-specific valid-index feedback; none
are silently corrected. Excerpt choices do not truncate the supplied full task
instructions or prove that a model's semantic inference follows from its quote.

The semantic queue route is registered with `register_semantic_diagnostic.py
--source-evaluation-id <solver-id> --evaluation-id <new-id> --corpus <fixed-dir>`.
It binds the root-owned corpus manifest hash and candidate snapshot. Its fixed
wrapper uses the designated model account; no caller-supplied commands or
provider settings are accepted. The worker rechecks complete comparison coverage,
every source identity and exact citation before publishing the diagnostic report.
It never launches ACS. Registered semantic diagnostics share daily dispatch
allowance; results cannot grant quality/scientific acceptance or release.
The route has mock coverage; a live evaluator-queue comparison has not yet run.
The separate live operator sweep is recorded independently.


Source-scope correction: `prepare_reference_corpus.py` now defaults to
`--scope active`, selecting only tracked `tasks/**/instruction.md`. Explicit
`--scope all` retains the broader repository-file inventory. Current-source
metadata checks found a corresponding task.toml for all138selected instructions.
The broad sweep finished all381records; exact-source projection to the138active
records reused existing judgments without new model calls or independent-review
claims. It reports13shared_method/125unrelated and no near_duplicate. The model
infers candidate_easier for all138; that is an uncalibrated text-based diagnostic,
not measured success rate or proof of scientific originality. Corpus hash,
source commits/blobs and citations were revalidated after projection. The full
sweep consumed339467input/27205output tokens, including retained failed attempts;
that cost also covers excluded fixtures/history and cannot be allocated solely
to current tasks. The earlier direct-quote pilot's costs remain separate.

`project_semantic_comparison.py` verifies both source corpora, source report,
all target source identities and exact citations. It preserves each original
judgment/source reference ID and records zero additional model calls. Tests
reject a target whose commit/blob/content differs from the parent evidence.
`evaluation_catalog` preserves distinct dispatch purposes and excludes retired
IDs; a stale request for a retired ID is rejected before job admission.

Installed UI smoke uses the workspace-local test dependencies in
`deploy/science/test-ui-requirements.txt`. It reconstructs the terminal screen
with pyte, waits for both actual repository names, and verifies the Keys popup
and return before quitting. Stripping ANSI sequences was insufficient: real
incremental screen updates split words and produced false negatives even while
the UI displayed both repositories. Replaying the retained failed capture with
the terminal decoder confirmed this. Raw captures and screen snapshots remain
private in workspace state; the smoke never enables roles or requests a model.


## Source-bound image publication (operator)

`deploy/science/build_task_images.py` requires `--repo`, `--commit` (full Git
commit), `--task-path`, `--output` (fresh private workspace directory), and
`--python-base` (digest-pinned Python image). Add `--publish` to push to the
Shanghai public ACR `terminal-bench-universe` namespace. Docker credentials stay
in workspace private Docker configuration and never enter build contexts.

Only the frozen `environment/` is used for the official image. The runtime
adapter adds pinned mini-swe-agent/litellm/openai/mcp dependencies. A supplied
`tests/Dockerfile` builds the separate verifier; otherwise a verifier derived
from the official digest receives standard tests later through Harbor. Solution
files never form a build context. External FROM images require digests. Context
checks reject links/special files and known credential paths/private-key markers;
this is not a complete secret detector or an audit of arbitrary Dockerfile code.

Publication checks remote manifest/config-ID linkage and records source/context
hashes and image labels. It is not a hermetic build: transitive Python packages
are not fully locked. Standard tags can be updated by publication; registered
evaluations always bind digests. Source-oracle leakage review remains required.
Do not publish an unreviewed author Dockerfile with privileged build options.
The operator-side tool is not yet automatic author submission/build dispatch.

A real infrastructure-only Harbor fixture completed all three builds, Shanghai
ACR pushes and remote manifest checks. Its immutable registration passed source
receipt validation and was deliberately disabled in the evaluator catalog.
No LLM or ACS was launched for this proof; it is not a scientific candidate or
an acceptance/difficulty result. Offline tests reject mismatched commits, hashes,
publication status, image repositories, provenance labels and Pod overrides.


The operator evaluation wrapper now checks the configured Kubernetes pull
Secret before loading model credentials or launching Harbor. It requires the
Docker-config Secret type and entries for both runtime/verifier registry hosts.
This checks existence and configuration, not credential validity; only a real
image pull can establish that. A live check passed against the restored Shanghai
Secret and a nonexistent-secret negative check refused before launch. The
Secret was found missing during new-image ACS validation despite older successful
runs, so historical trial evidence must not replace a current preflight.


The new source-built runtime subsequently passed a real Beijing ACS image smoke:
2CPU/4GiB actual requests and limits, pinned package-version assertions and
mini-swe-agent import succeeded, exit0. Pod image used the published manifest
digest; the container runtime reported its configuration digest, which exactly
matched the build receipt (these are distinct OCI digest types). The unique Pod
was deleted/404 and two resource snapshots were empty. This smoke called no LLM
and is infrastructure evidence only. The restored pull Secret is persistent
configuration, not a leaked compute resource.

## Register a complete candidate handoff

`register_candidate_bundle.py` combines immutable solver registration, a fresh
credential-free reviewer root and fixed-corpus semantic registration. It accepts
`--evaluation-id`, `--repo`, `--commit`, `--task-path`, `--template`,
`--build-receipt` and `--corpus`. The receipt comes from the separate reviewed
image build/publish step; a caller cannot supply a mutable task or substitute
images. IDs are `<id>`, `<id>-quality` and `<id>-semantic`. All three bind the
same snapshot, source commit and template. The quality route binds a newly
prepared UID21012 tool root; the semantic route binds a validated corpus manifest.

The operator tool prepares and rechecks every input before one atomic registry
publication. Preparation failures remove its new snapshot/reviewer root and
publish no routes. A catalog-projection failure after registry persistence keeps
the evidence: regenerate the catalog from the registry, do not reuse the ID.
SIGKILL/host failure can leave unpublished staging directories; investigate those
exact destinations before removing them. The tool does not claim crash-atomic
filesystem rollback. Never run two operations against the same bundle ID.

`--disabled` keeps all three infrastructure-proof entries out of the catalog.
Normal registration makes diagnostic routes dispatchable; it does not execute
them, grant acceptance, bypass daily allowance or approve a merge. This remains
an operator action after reviewing the author proposal/Dockerfile and evidence.
No role receives registry write access, build-service privileges or credentials.

Real infrastructure handoff proof passed with all three routes disabled: shared
source/template hashes validated, active comparison corpus validated, a real
UID21012 reviewer command verified read-only task access, absent provider/admin
environment and absent host proc. Reviewer process cleanup was confirmed.
Duplicate IDs and a wrong source receipt were rejected with byte-identical
registry preservation; failed fresh-registration destinations were absent.
These checks made zero model calls and launched no ACS resources. They verify
handoff mechanics, not reviewer factual reliability or candidate acceptance.

## Operator factual adjudication ledger

`review_adjudication.py --report <review.json> --audit <operator-ledger.json>
--output <fresh-private-file>` validates the provenance of an explicit operator
judgment. The ledger uses `schema_version: 1`, exact `report_sha256` and
`snapshot_sha256`, an attributed `operator`, and false `scientific_acceptance`
and `factual_acceptance` flags. Its `decisions` cover every `issue:<id>`,
`dimension:<name>`, `summary`, `gate`, `difficulty`, `suggestions:<index>` and
`limitations:<index>` exactly once. Each has `claim_id`, `verdict` (`supported`,
`refuted`, `unresolved`), `rationale` and `evidence`. Supported/refuted decisions
require actual workspace-relative evidence paths, SHA256 hashes and exact text
quotes. Unresolved entries remain explicit; do not omit difficult claims.

The validator checks identity, coverage and evidence linkage. It cannot prove
that quoted evidence supports an operator inference or authenticate a human
signature. Even an all-supported ledger has machine_factual_verification=false
and release_eligible=false. Neither model output nor this ledger authorizes a
merge; independent scientific review and final approval remain separate.
Private commands, source reports and calculations stay outside source control.

`review_diagnostic_status.py` no longer treats the mere presence of an audit
file as audited evidence. Old unbound files yield `diagnostic_audit_unbound`;
fully bound version1 ledgers yield `diagnostic_adjudication_recorded`, with
supported/refuted/unresolved counts and all acceptance flags false. Changed
reports/snapshots/evidence, missing claims and fabricated quotes are rejected.

A real isolated UID21012 reproduction selected the excluded point through
exhaustive leave-one-out least-squares SSE minimization. Its independent fit and
six-decimal result passed the unchanged calibration grader; a deliberate0.001
scale shift failed. The original retained command also explicitly added0.001,
and its file hash matches finalization provenance. The false alternate-MAD
rejection claim is recorded as refuted, while17other report items remain
unresolved. This calculation used no model/ACS and is not a new review or
scientific acceptance. Tests also confirm that an all-supported operator ledger
cannot become automatic factual verification or release permission.

## Installed Harbor mechanical evidence

Both operator registration tools now call `check_harbor_task.py` on the frozen
snapshot before publication. It parses task.toml using the actually installed
Harbor TaskConfig, checks standard files are nonempty, checks schema-resolved
resource/time values are nonnegative/positive where applicable, and uses clean
environment `bash -n` on test.sh/solve.sh without executing them. Optional
unspecified values stay unspecified; defaults are not evidence of actual Pod
resources. Reports record Harbor distribution version, schema/checker source
SHA256 and the complete task hash. A native Harbor parser may tolerate unknown
fields; this is not a comprehensive upstream authoring rubric or typo detector.

Each new registration retains a private mechanical-check.json and its hash.
Dispatch rechecks the evidence hash, snapshot binding, successful checks and
nonacceptance scope. Old bootstrap registrations without this field are legacy
infrastructure evidence, not retroactively mechanically certified or releasable
scientific tasks. A real disabled infrastructure registration passed with its
mechanical receipt. Tests reject malformed schema/time/resource settings,
broken shell syntax, empty instructions, changed snapshots/receipts, and verify
a candidate shell command is never executed by checking an absent sentinel.
No model, task runtime, license audit, Oracle or ACS execution is implied.

## Full-package quality WinRate preparation

`prepare_winrate_plan.py --evaluation-id <registered-solver-id> --corpus
<active-corpus-dir> --reference-index <index> [--reference-index <index> ...]
--output <fresh-private-dir>` freezes complete reference task directories from
Git objects at the corpus commits. Selection must include both TB4 and TBScience;
duplicate indices and colliding original task directory names are refused.
Extracted instruction hashes must match the corpus. Full package hashes include
binary data, in addition to the native pipeline's metadata/source snapshots.

The tool validates the candidate registration, builds a native unified-evaluator
WinRate dry-run plan, checks every selected task appears, and rechecks full
package hashes after planning. It passes a clean workspace-local environment
without model credentials. There is no live-evaluation mode. Inspect the saved
source-manifest and plan before implementing/authorizing a live execution path;
do not bypass private-tool boundaries by removing --dry-run from an ad hoc
controller command. `verify_package_inputs` checks retained full-package content;
tests reject equal-size binary changes and candidate identity substitution.

A real plan passed with two current tasks from each benchmark at fixed commits:
embedding-drift-monitor, roy-polymorph-cn, navigation-sensor-calibration and
hbv-calibration-1. Four pairs imply eight future swapped judgments, but actual
model calls were zero. This is an explicitly chosen diagnostic subset, not a
representative quality sample, comparison result or acceptance evidence.

The trajectory-review native dry-run also accepted a historical real certificate
trial with ATIF-v1.7. The original executed task snapshot hash was not retained,
so current-tree identity cannot be proven. This is input-adapter evidence only,
not a science-pilot trajectory review. Current aggregate-only science trials
cannot retroactively supply missing ATIF. Science trajectory review/WinRate
still require a separately validated private retention and exact-version binding
path; no raw trajectory was exported to roles or source control by these checks.

## Explicit private trajectory retention

Trusted operator templates may set agent kwargs `retain_private_trajectory: true`.
It defaults to false. Requests still accept only ID/hash; callers cannot choose a
path. The worker assigns a fresh root-owned0700 directory under workspace
`.state/science-private-trajectories/<job_id>` and writes a0600identity binding
with candidate snapshot, designated provider/model and both image digests.
The agent downloads the real Mini-SWE log there, checks the recorded model,
converts it using Harbor's installed ATIF converter, and records raw/ATIF hashes.
Nothing is fabricated when an aggregate-only trial has no retained trajectory.

Known runtime API credential values and private-key markers cause private
quarantine and failure, with no review-ready ATIF. This is not an exhaustive
secret detector; private traces must never be copied to roles, public logs or
source control. A separate boundary review is required before supplying these
files to any future trajectory judge. All files are0600; default metadata mode
still downloads no trajectory and publishes aggregate-only results.

After guard exit the worker records a private execution-binding.json. Eligibility
requires unchanged task content, a real retained trace, normal solver completion
and confirmed cleanup. Missing/failed retention cannot be upgraded because a
solver succeeded. The role-readable result contains neither private paths nor
raw trace contents. Aggregate exports remain false: private control-plane
retention is distinct from a role/public export.

Offline tests use real Harbor ATIF conversion with mock transfer, no LLM/ACS:
normal conversion/hash/modes, known credential refusal, wrong model, symlink/mode
refusal, default-off transfer and metadata, worker-assigned paths, caller-path
rejection, absent-path public result and missing-retention ineligibility. Quality
and semantic queue regressions also pass. The private mode is not yet validated
by a live science solver run; existing templates remain aggregate-only. Do not
claim trajectory review/WinRate completion from this implementation.

`validate_private_trajectory.py --evaluation-id <id> --directory <private-job>`
is the controller-side read gate for retained evidence. It revalidates the
current registered snapshot/template, exact runtime/verifier images, provider,
model, private0700/0600ownership/modes, identity/raw/ATIF hashes and all post-run
eligibility flags. Cancelled/incomplete runs and changed/copied evidence are
refused. The queue now records cancellation before evaluating private eligibility,
so a late stop cannot leave a cancelled trace marked reviewable.

This remains operator provenance rather than a cryptographic proof of solver
honesty: a solver can influence logs inside its container. Future judgments must
consider verifier/terminal evidence and cannot treat an internally recorded
trajectory as tamper-proof. The read gate does not grant file access to roles,
call a model, or claim semantic validity of trace contents. Tests cover changed
identity/raw/ATIF, image substitution, public permissions, cancelled state,
unconfirmed cleanup, missing retention and changed-snapshot flags.

## Prepare a native private trajectory-review trial

`prepare_private_trial.py --evaluation-id <id> --directory <private-job>
--output <fresh-private-state-dir>` revalidates retention, current registration,
worker job/result identity, guard success/cleanup and exactly one normal Harbor
trial at the registered task path with the designated model. It assembles ATIF,
verifier stdout and minimal configuration/result data, preserving source and
prepared-file hashes. Both config.json and result.json use explicit allowlists:
Harbor result.json embeds a complete config, so copying it wholesale would
reintroduce provider environment values. Native trajectory input validation
runs before a preparation manifest is written. Changed inputs or validation
failures remove this tool's incomplete output.

This makes no model calls, does not copy artifact collections, and explicitly
retains native warnings about missing artifacts. It is not a full trial export,
scientific review or proof of complete evidence. Trace/verifier text remains
private untrusted content; secret/content review is still required before any
judge call. Tests use a synthetic normal trial and native input validator, with
mocked upstream retention validation. They verify no secret sentinel from either
embedded config appears in prepared metadata, reject foreign worker jobs and
wrong executed task paths. This is not live science retention evidence.

Repeated job IDs are idempotent only for the exact original three-field request.
Before returning any retained result, the worker now compares both its durable
claim and result with job_id/evaluation_id/snapshot_sha256. Reusing an ID with a
foreign candidate or changed snapshot, or a mismatched retained result, is
refused before overwriting the public aggregate. An interrupted matching claim
without a result remains interrupted with cleanup unconfirmed. Offline tests
cover valid replay, cross-candidate/hash replay, changed result identity and the
interrupted state. This prevents evidence misattribution; it does not rerun or
upgrade previous work.
