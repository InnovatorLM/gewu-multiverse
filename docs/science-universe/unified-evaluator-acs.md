# Unified evaluator and ACS integration

The source is the existing private checkout `repos/unified-evaluator-pipeline`,
commit `8650fd5821da347e64716ee96e799ba34b8b3951`, with local runtime/test
adaptations. Record the actual source inventory rather than identifying a
modified checkout solely by its commit. Do not publish its private source,
review prompts, trajectories or credentials to this repository.

## Verified execution boundary

On 2026-10-27, a temporary Beijing ACS Pod used the already published Shanghai
ACR runtime image for the public `stacking-disorder-diffraction` task. It ran
Codex 0.164.0 as UID 21012 with a read-only task and a separate writable scratch
directory. An unsandboxed same-UID control could read the private sentinel and
write the task. Inside the Codex/Bubblewrap boundary the task remained readable,
scratch remained writable, and both task writes and private sentinel reads were
rejected. This was a credential-free test with no real model calls.

The Codex distribution requires its matching bundled Bubblewrap, not an
arbitrary executable placed at `codex-resources/bwrap`. The tested binary digest
was `3a81c19ad10a70436529c58e77898e2a447abe80167f813fc20ec34bd9eafdeb`.
Keep the expected helper layout, including `codex-path/codex-linux-sandbox`.
Do not disable isolation or digest verification to work around missing helpers.
This does not establish a container escape guarantee or unrestricted code
execution safety.

Custom shell variables requested through `shell_environment_policy.set` were
absent in actual tool execution. Extending `include_only`, inheriting explicitly
set variables, and disabling shell snapshots did not fix this observation. A
mock Responses endpoint verified that an explicit per-command `env` prefix sets
scratch variables and allows a scratch write while fake provider credentials
and unrelated inherited variables remain absent. The reviewer instructions now
supply the absolute scratch path and this fallback. These are mock transport
checks, not model quality results.

## Actual review and remaining work

The first ACS quality review used the designated DawnFM account and
`deepseek-v4.1-flash-1017`, the original six-dimension rubric, and the unmodified
public task. It completed 23 shell calls, 22 successfully, but timed out after
600 seconds without a valid report. No quality acceptance follows. The task
inventory was unchanged, exact known-secret scans found nothing, and the Pod
and all four resource categories were confirmed released.

The follow-up `qa-live-a5cfc4896e` completed in 777.95 seconds using the
pipeline's default 1800-second budget and the scratch fallback. The original
validator accepted its report: 63.75/100, no confirmed blocker, difficulty 4/5
with confounding noted. All 27 completed shell calls succeeded. These are model
judgments, not independently verified scientific conclusions. The model also
reports a scratch reference-solution check; the original task was unchanged.
Token usage was 739342 input, 649216 cached input and 81674 output (including 74911
reasoning output); these nested counts must not be added as independent totals.
After the completed turn and valid JSON, the existing pipeline terminated a
lingering CLI process (`exit_after_completion_forced=true`, agent return -9);
the review driver exited 0. This is recorded, not concealed as an ordinary native
CLI exit.

Exact known-secret scanning passed and confirmed cleanup passed. The retained
receipt reader accepted the actual report. An actual evaluator UID 21002 read
the sanitized receipt, could not write it, and had neither the provider key nor
host kubeconfig. This was a zero-model read test, not autonomous queue dispatch
or an independent evaluator approval. The receipt is staged read-only at
`/evaluation/diagnostics/qa-live-a5cfc4896e.json` inside the evaluator root. All four existing public Science
trial inputs passed the trajectory input contract without model calls or input
changes. Their `LimitsExceeded` solver exits must remain visible; this is not
full-budget difficulty calibration.

Before wiring autonomous review, verify the final JSON with the project's own
validator; bind it to task/source/harness inventories and confirmed cleanup;
scan for secrets; expose only the diagnostic result to the evaluator role.
A valid schema or high score must never automatically grant scientific
acceptance, merge approval or startup approval.

## Latest upstream native harness

Upstream `Callo42/gewu-multiverse` at
`706cafde67d61ae3501c720978c3471c3cfef254` (0.1.39) supports Pi, Codex,
DeepSeek Harness and OpenCode. Its native execution requires enforced Landlock.
The development host probe failed and the actual Beijing ACS kernel returned
ENOSYS for Landlock, although user namespaces worked. The upstream native
harness has therefore not been deployed. The tested existing Codex/Bubblewrap
route does not prove that upstream's Landlock requirement has been met.

The unified five-strategy orchestrator still explicitly depends on ECS workers,
SSH and rsync. ACS solver and review proofs do not replace that scheduler.
A full ACS backend needs cancellation, result inventories, resource ownership
and cleanup support, as well as the original evidence contracts. Production
roles remain stopped until independent reviews and the user's final approval.

Detailed private receipts are under
`.state/harbor-eval/unified-harness-integration/`; governance status is in
`universes/my-terminal-bench-science/governance/unified-quality-harness-integration.md`.

## Operator receipt check

`deploy/science/read_unified_quality_receipt.py --run-id qa-live-<id>` is a
read-only validation entrypoint for retained ACS evidence. It requires a
successful original driver result, unchanged task inputs, the designated model,
two empty resource snapshots and known-Pod404, a mode0600 exact-secret audit
bound to the final review hash, and an input inventory matching the complete
current private evaluator implementation. It then invokes the original quality
validator and returns only the standard diagnostic fields and aggregate usage.
Known task paths are mapped to `/task`; raw runtime metadata and trajectories
are excluded. It deliberately cannot create acceptance or launch approval.

The exact-secret audit is an operator artifact named `exact-secret-audit.json`
inside the private run directory, containing `run_id`, `findings`,
`secret_encodings_checked`, and `review_sha256`. It must be generated by scanning
actual retained evidence against the configured credentials; an empty manually
written list is not scanning evidence. This reader is not yet wired into the
autonomous evaluator queue. Its seven mock regression cases are separate from the completed live review
and actual evaluator read test described above.


## Deployed evaluator instructions

The deployed private evaluator instruction now explains the read-only
`/evaluation/diagnostics/` handoff separately from queue results. It requires
an assigned issue, matching task/version evidence, explicit uncertainty for
unverified model findings, and sanitized author feedback. It forbids forwarding
whole diagnostic reports containing reference-solution or hidden-test analysis.
The source and deployed instruction hashes were checked equal while the role
was stopped. This is configuration deployment, not a new model session,
autonomous ACS dispatch, or independent approval. The private instruction is
not copied into this public repository.

The earlier frozen procedural review manifest predates this instruction change.
Preserve it as historical evidence; an independent final review must bind a new
manifest including the current instruction audit rather than reuse the old role
hashes as proof of the current deployment.

## Reusable Pod worker (integration in progress)

`deploy/science/acs_quality_worker.py` replaces the hard-coded task selection in
the experimental Pod-side script with `--root` and `--task-name`. It accepts
only a fresh `qa-live-<id>` directory below workspace state, rejects task links
and missing standard Harbor inputs, fixes the designated DawnFM model/endpoint,
and receives the credential through stdin. It retains the original project's
quality-review entrypoint and 1800-second budget. It records input immutability,
redacts actual key matches before output retention, and terminates its owned
process group on interruption/timeout. Credential redaction is not a substitute
for the controller's full known-secret scan.

Six local contract tests cover input mutation, traversal, links, missing files,
fixed invocation and refusal to reuse old state. They do not validate the new
worker on ACS, model behavior or Pod deletion. The operator controller still
needs source-bound packaging, live worker validation, queue integration,
cancellation and independent four-resource cleanup before this worker can be
advertised as an autonomous ACS backend. No queue entry or production setting
was changed by adding it.

The reusable worker's lifecycle was subsequently tested in a real Beijing ACS
Pod (`qa-live-6c0f2a2947`), with its exact source hash verified. The supplied
public task's 20-file inventory remained unchanged. An explicitly substituted
mock quality module exercised normal completion and SIGTERM cancellation,
including a descendant that ignored SIGTERM. The descendant was no longer
running after worker cleanup. Actual model calls were zero. Pod404 and two
empty snapshots of all four resource categories were confirmed. This proves
the tested worker lifecycle on ACS; the mock report is not a schema-validated
quality judgment or a live LLM review. Queue integration and a real review of
the reusable worker remain incomplete.

## Operator controller (preflight verified, live integration pending)

`deploy/science/run_acs_quality.py --settings <operator-json> --validate-only`
checks the immutable task tree, complete private pipeline tree, worker/Codex/
Bubblewrap hashes, project image digest, and matching successful boundary smoke.
It accepts no caller-provided shell command. The four refusal tests and the
actual local pinned configuration preflight passed without model calls or cloud
creation. The controller writes an inventory of the packed files before cloud
execution. Runtime secrets are not part of that input archive.

The reusable worker's first actual designated-model review is tracked separately
as `qa-live-fc9e283eb1`; at the time of this update it is still running through
the experimental controller, not this newly extracted controller. Do not claim
that the new controller or autonomous queue is live-validated from this run.
The operator controller still requires live cancellation/cleanup testing and
registration into the protected role dispatch before autonomous use.

## Reusable worker completion and protected ACS dispatch

The reusable worker's real run `qa-live-fc9e283eb1` has now completed: 1158.72
seconds, 28 completed shell calls (27 successful), an unchanged 20-file task
inventory, and an original-validator-accepted report. The model score was
81.25/100. The earlier run scored 63.75/100 on the same task; these differing
judgments reinforce that scores are diagnostic and cannot grant acceptance.
Input usage was 1232748 tokens, including 1106432 cached tokens; output usage
was 90953, including 78474 reasoning tokens. The pipeline again stopped its
lingering Codex process after a completed turn and valid report. Known-secret
scans passed, Pod404 and two empty four-resource snapshots were confirmed.
This real worker run used the experimental controller, not the extracted one.

The extracted controller was separately cancelled after its actual ACS Pod was
observed (`qa-live-3e0c1595b3`), before any worker/model invocation. It retained
its cancelled report, exited nonzero, and confirmed Pod404 and two empty
four-resource snapshots. This is a zero-model live cancellation test.

The protected quality queue now supports an explicit operator-registered
`quality_backend=acs`, with a hash-bound settings file and an exact match to the
registered snapshot path and digest. `register_quality_diagnostic.py` accepts
`--acs-settings` instead of `--review-root` for this backend. The queue calls
`run-acs-quality`, which selects the designated account and executes the
source-bound controller. The controller invokes `finalize_acs_quality.py` to
scan extracted outputs, the guard report and original upload members against
actual known credentials before calling the receipt reader and original
validator. Only the validated diagnostic is placed in the requested summary.
An absent ACS summary is unconfirmed cleanup, regardless of local UID process
counts. Existing queue claims and daily limits are preserved.

The new queue route passed credential-free mock dispatch/refusal tests. The
finalizer also validated the actual completed reusable-worker evidence. No
production registration or role dispatch was enabled by these code changes;
a full live queue-to-controller review remains unverified. Independent role
approvals and user startup approval remain pending.
