# Codex default harness validation

Validation date: 2026-10-24. Baseline: af2e2b9.

## Changes

Codex is the default in production and tests; GEWU_HARNESS=native is the
explicit compatibility switch. Native endpoint/key setup no longer blocks Codex.
Codex goes through run_shell rather than bypassing confinement and AskPass.
It uses workspace-write, per-run HOME/CODEX_HOME/XDG/cache/temp directories,
private authentication, bounded output capture, and a timeout.

## Automated results

- cargo check and cargo fmt --all --check passed.
- Eight new black-box tests passed: default selection without native key;
  instruction/workspace/AskPass; nonzero exit; missing final message;
  missing executable; timeout; output beyond pipe capture limits; Git commit and
  local remote push preserving author; credential permissions/redaction/cleanup.
  Several assertions are grouped into individual tests.
- Original unit suite: 325 passed, five failed. Both serial and parallel runs
  reproduced the failures. An archived checkout of af2e2b9 reproduced all five:
  askpass/Landlock fixture, temporary executable namespace fixture,
  editor stop deadline, and two inaccessible-pidfd fixtures.
- Broad native regression run passed the unit tests with those five excluded and
  12 subsequent targets before stopping at correction-6-guards. That target had
  two denied-write failures; an archived af2e2b9 checkout reproduced both.
  These tests assume file permissions deny writes, which does not hold for this
  root environment.
- Targeted Forgejo, confinement, engine recovery and run-count tests were also run.
  Live Forgejo tests marked ignored by upstream were not forced on this installation.

## Real Codex attempt and limit

The installed Codex CLI was started by the actual --run-agent supervisor with
an isolated fixture repository. This exposed and fixed a missing provider env_key
handoff. After that fix Codex emitted thread.started and turn.started, but the
configured DawnFM Responses provider did not complete within the 120 second
fixture timeout. A direct Responses HTTP request to the same configured provider
also timed out after 25 seconds. Thus live-model code editing/commit/push is not
verified; only the deterministic CLI/Git integration is verified.

## Remaining boundaries

Native Forgejo functions are not bridged into Codex yet. Codex's own tool calls
are captured as bounded JSON output rather than separate native tool records.
The native max_turns limit does not govern Codex. Abruptly killed unconfined runs
can leave private runtime credential copies in their workspace; confined runs use
the existing temporary tree cleanup. Provider availability and supported sandbox
features remain required for a real Codex run.
