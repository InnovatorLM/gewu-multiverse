# Universe progress and trajectory audit

Operator audit performed during this work; host wall clock reports October 29
while session date is October 30, so observed timestamps are retained without
claiming an exact elapsed duration.

## Improvements since startup

- Shanghai ACR/public pull to Beijing ACS validation and credential/image mapping work.
- Separate role roots/UIDs, workspaces, private evaluator material and local credentials.
- Role package tools and independent environments; nonroot Python 3.11 + NumPy 2.4.6
  import and arange(5).sum()==10 verified in dedicated test identity in role chroot.
- Persistent native/Codex event archives and loopback website with history, logs,
  redaction, 60-second refresh and Chinese briefs.
- Task completeness gate, author self-solve/iteration, trajectory evidence and
  timeout infrastructure-vs-model classification rules.
- Exclusive PR-version review dispatch deployed; PR30 commit1d8173f7 assigned to
  evaluator-01 issue32; generic issues26/27/28 closed; other reviewers await work.

## Previously identified problems

One structured candidate PR30 exists, but image build/frozen execution registration,
five independent ACS trials and acceptance remain absent. PR31 is proposal-only.
PR30 description still claims interference correction omitted by its contract;
public decay constant differs from the truth metadata. Existing evaluators repeat
reviews without a task binding; /evaluation tools are absent from current roles.
Runtime instructions still contained old unified-pipeline, approval and resource
requirements. Dispatch guidance now overrides these for live roles. Current
resource policy is 4CPU/8GiB, up to8CPU/16GiB when resource failures justify it.

## Additional trajectory observations

Recent three sessions sampled for nine roles; findings are observations, not a
benchmark of agent capability. Raw operator audit stays outside Git.

- Many recent sessions terminate at max_turns24 and restart with repeated repository
  and handoff reading. This bound remains deployed; it has not been removed here.
- Author01 spends repeated calls fetching Debian packages after missing libstdc++,
  seq and nohup; author07 repeatedly attempts NumPy installs with120s timeouts.
- Author09 encountered missing libbz2 in the system Python and truncated downloads.
  Package tool installation alone does not certify all runtime shared libraries.
- Author03 is genuinely prototyping, but repeated log-domain/None errors and long
  optimization timeouts indicate missing numerical domain checks in its prototype.
- Author07 previously printed its Git credential JSON with an inadequate password-only
  sed mask. Role credentials remain readable by that role; controller-side sanitization
  must cover exact role tokens before native logs/model messages are persisted.
- Curator was writing research proposals and toy verifiers instead of coordinating;
  new live guidance prioritizes coordination and forbids new task authoring.
- Some shell results exit0 despite internal errors because trailing commands/pipelines
  succeed. Exit status alone cannot prove installation or tests passed.
- Completeness requirements were applied before implementation, creating a circular
  dependency; author clarification now applies the gate to runnable/submittable packages.
- Permissions and identifiers block actual evaluation, while repeated status comments
  inflate apparent activity. Website activity should not be interpreted as delivery.

## Remaining work

Complete execution registration/build service, wire missing evaluator entrypoints,
fix the24-turn/120s lifecycle and library coverage, and validate real blocked-state
receipts through new sessions. No five-rollout success or full universe readiness
is claimed by the new dispatcher.
