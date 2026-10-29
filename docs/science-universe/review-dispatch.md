# Exclusive candidate review dispatch

The root operator runs deploy/science/review_dispatcher.py. A singleton flock
protects ledger updates. Each PR+commit receives one owner and one explicit
Forgejo task; role review receipts persist state/stage/reason. Generic evaluator
startup issues are closed. Waiting tasks close their issue and do not wake on
evaluator self-comments. Author/operator PR comments wake waiting tasks. A new
revision waits until the prior review is parked/completed. No automatic reassignment
is allowed while solver work or cleanup may remain unknown.

Role command: role-review-status waiting_author --stage completeness --reason TEXT
States: reviewing, waiting_author, waiting_platform, completed. The generation
field prevents stale receipts from completing a newly awakened assignment.
The dispatcher polls local Forgejo once a minute without calling a model.

The dispatch snapshot_sha256 is explicitly an inventory identity, not the frozen
execution snapshot required by the ACS queue. Image build, execution registration,
solver job identities and cleanup remain separate steps. No acceptance is implied.

Current limitations: one writer is supported, not multi-host distributed locking;
crashed owners require operator inspection rather than automatic lease expiry;
active model sessions read new instructions on their next session. Empty-work
model sessions still depend on the engine's existing idle loop. Platform waiting
is resumed by an explicit operator PR update; build-service event integration
remains future work. Progress files are role-reported and are not proof of passing.
