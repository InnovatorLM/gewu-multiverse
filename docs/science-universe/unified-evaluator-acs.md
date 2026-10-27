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

A follow-up uses the pipeline's default 1800-second budget and the scratch
fallback. Its result must be read from the retained run evidence; do not infer
completion from a live Pod or working shell. All four existing public Science
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
autonomous evaluator queue. Its seven mock regression cases do not substitute
for a completed live review.
