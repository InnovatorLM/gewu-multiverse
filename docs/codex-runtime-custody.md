# Codex runtime custody audit — 2026-10-25

This audit covers the supervised Codex harness. It does not certify the science
universe as ready for unattended runs.

## Fixes

- Create each `.gewu-codex-<run-id>` runtime freshly with mode 0700. Refuse an
  existing directory or symlink instead of reusing old output or writing secrets
  through a workspace-provided link.
- A runtime owner removes the entire temporary tree on every ordinary return,
  including configuration/credential preparation failure, transcript failure,
  CLI failure and timeout. This also removes Codex session traces, configuration,
  prompt copies and caches, not only `auth.json` and `provider-env.sh`.
- Durable supervisor logs and transcripts remain in the run directory with the
  existing redaction mechanism. Source credentials are not removed.

## Verification

- `cargo test --test codex-harness`: 11 passed. These are deterministic fake-CLI
  tests, not fresh live model tests. Two new regressions cover partial preparation
  cleanup and refusal to follow/reuse a stale runtime symlink.
- `cargo check` and `cargo fmt --all --check`: passed.
- The actual `--landlock-probe` entry, given an allowed control file and a
  forbidden file, exited 126 on this host: Landlock is unavailable. Therefore an
  outer Landlock boundary cannot justify `danger-full-access` on this host.
- Previous live supervisor tests are documented separately in
  `codex-harness-validation.md`; they do not prove isolation or Forgejo access.

## Remaining requirements

Cleanup uses best-effort filesystem removal; SIGKILL, host loss, changed file
permissions or an actively hostile same-UID process can prevent it. Independent
recovery must inspect interrupted runs and verify resource deletion. Never remove
a directory solely because its name matches the runtime prefix while its
supervisor/children are live.

Codex `workspace-write` remains the default. No automatic sandbox relaxation has
been introduced. If the host rejects Codex's namespace sandbox and also has no
outer confinement, production startup must refuse rather than treat a directory
layout as isolation. An explicitly selected `danger-full-access` mode does not
create a filesystem, process, network or evaluator-methodology boundary.

The existing role accounts and Forgejo repository visibility must enforce author
versus evaluator access independently. Shell/environment access includes the
selected model credential; filesystem privacy does not make that credential
unavailable to the model's tools. Production needs appropriately scoped
credentials and isolated role runtimes.

Official Codex configuration documentation was requested via the documentation
tools; the direct official config-reference request returned HTTP 403 in this
environment. This audit therefore verifies local implementation and tests, not
new upstream documentation claims.
