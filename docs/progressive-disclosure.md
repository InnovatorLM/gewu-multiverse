# Progressive disclosure for agent collaboration

This document proposes the context layer for `gewu-multiverse`. It keeps the
existing Git and Forgejo workflow as the source of truth, while preventing every
agent from receiving a full repository, issue thread, or README on every turn.
The same layer can serve the native chat loop, a Codex-style harness, and a future
DeepSeek harness.

## Goals and non-goals

The context layer should:

- make the first model request small and useful;
- let an agent expand only the object it is currently investigating;
- return stable references and line ranges, so a later turn can ask for the same
  material without repeating a large payload;
- share summaries and hashes between agents, while keeping branches, commits, and
  Forgejo ownership separate;
- preserve raw Git and Forgejo operations for the final action;
- make every supplied fact traceable to a repository path, Git object, issue, PR, or
  generated summary.

It should not replace Git, invent a second task tracker, or silently treat README,
issue, comment, or source text as product instructions. Those are work material;
the harness instructions remain separate.

## The disclosure ladder

Every repository object has four disclosure levels. A tool returns level 0 or 1 by
default and a model explicitly requests higher levels.

| Level | Contents | Typical size |
| --- | --- | --- |
| 0 — identity | repository, branch, commit, dirty state, issue/PR number, title, labels, assignees, and links | 1–2 KiB |
| 1 — map | directory tree, README table of contents, changed-file list, issue/PR synopsis, and symbol/module names | 4–8 KiB |
| 2 — evidence | matching lines, selected README section, issue body, or a bounded comment window with references | 8–32 KiB |
| 3 — source | an explicitly requested file/range, complete issue thread, diff, or patch | bounded per call |

The response always carries a `ref` and `content_hash`. A level-2 or level-3
response can therefore be cited in a hand-off without copying it into every other
agent's context.

### Initial context

Before the first model call, the harness sends only:

1. the task instruction and the agent identity;
2. a repository manifest at level 0;
3. assigned issue/PR identities at level 0;
4. a small level-1 map for the assigned repository and the README's headings;
5. the disclosure tool schemas and the current branch/commit.

The first request must not contain all files, all issues, or all comments. If an
instruction names a path or issue, the indexer may include that object's level-1
map as a task-specific hint.

## The shared index

Each agent workspace gets a local, disposable index under `.gewu/index/`. The index
is keyed by the Git commit and Forgejo update timestamp, so it can be invalidated
without changing the working tree. It contains:

- `repositories.jsonl`: repository identity, branches, HEAD, dirty files, and
  clone status;
- `tree/<commit>.json`: paths, file sizes, language, and generated module/symbol
  names;
- `readme/<blob>.json`: headings, links, and short section summaries;
- `issues/<repo>/<number>.json`: issue/PR identity, bounded synopsis, labels,
  assignees, and comment cursors;
- `summaries/<content_hash>.json`: summaries produced from immutable content;
- `refs.jsonl`: the disclosure references returned to agents.

Indexes are rebuilt incrementally. A changed Git blob invalidates only its own
summary and dependent directory/module summaries. Forgejo comments use a cursor and
etag/timestamp, so an unchanged thread is not downloaded again. Raw content remains
in Git or Forgejo; the index is a cache and can be deleted.

The indexer should start with Git's own plumbing (`git ls-tree`, `git diff`,
`git log`, and `git grep`). Language-specific symbol extraction is an optional
provider; failure to parse a language must leave the tree and text search usable.

## Disclosure tools

The harness exposes the same JSON tools to every model backend. Results are bounded,
include a continuation token when cut, and never fetch a repository outside the
run's cloned-repository allow-list.

### Repository tools

- `repo_overview(repo, ref?)` — level 0 identity and level-1 map;
- `repo_tree(repo, path?, depth?, ref?)` — a bounded tree with child counts;
- `repo_search(repo, query, path?, ref?, limit?)` — matching paths and line spans,
  not full files;
- `repo_read(repo, path, start_line?, end_line?, ref?)` — an explicit level-3
  range, with a byte/line cap and a continuation token;
- `repo_diff(repo, base?, head?)` — changed paths first, then an expandable patch;
- `repo_history(repo, path?, limit?)` — commit identities and subjects before full
  commit bodies.

### README and Forgejo tools

- `readme_outline(repo, ref?)` — headings, links, and section references;
- `readme_section(repo, ref, section_ref)` — one selected section;
- `issue_overview(repo, number)` — level 0 identity plus a bounded synopsis;
- `issue_search(repo, query, state?, assignee?)` — identities and matching terms;
- `issue_comments(repo, number, after?, limit?)` — a bounded comment window with a
  cursor;
- `issue_expand(repo, number, field, ref?)` — explicit body, diff, or comment
  expansion;
- `context_expand(ref, level, cursor?)` — a uniform escape hatch for a previously
  returned reference.

Existing `forgejo_list_assigned_issues`, `forgejo_read_issue_or_pull`, and
`forgejo_comment` remain available. The new disclosure tools are read-oriented;
write tools still perform the actual comment, branch, commit, and pull-request
operations and keep the existing per-run write limit.

## Context ledger and budgets

The run keeps a `ContextLedger` beside the message list. It records the references
already disclosed, their hashes, the current branch/commit, and a per-run token
budget. Each entry has:

```text
ref, level, hash, source, first_seen_turn, last_used_turn, bytes, importance
```

The ledger prevents duplicate payloads. If a model asks for a reference it already
has, the harness returns the reference and hash rather than appending the same text
again. Importance is assigned from the task, assigned issue, current diff, explicit
model requests, and recent tool failures; it is never inferred from untrusted issue
or README wording.

When the estimated context reaches the configured soft limit, the harness keeps the
system instruction, the original task, the active hand-off, the current diff, and
the most recently used evidence. Older evidence is replaced with reference/hash
cards. When it reaches the hard limit, it compacts complete turn groups into a
model-generated summary plus a deterministic ledger of refs. Tool-call and
tool-result messages are never split in the middle of a turn.

Compaction is recorded as a transcript event with the old and new reference sets,
hashes, and byte counts. The summary is cached by content hash and can be reused by
another agent without copying a full conversation. A failed summarization falls back
to deterministic reference cards and continues with a visible warning.

## Multi-agent hand-off

Agents communicate through durable, small artifacts rather than copying source into
issues:

```text
.gewu/collab/<repo>/<branch>/handoff.json
```

The hand-off contains the task, base/head commits, owned paths, refs, hashes, tests
run, blockers, and the next suggested disclosure. It never contains credentials or
an unbounded transcript. A later agent starts at level 0/1, verifies the hashes
against its clone, and expands only the named refs.

The scheduler can use `owned_paths` and the base commit to warn about overlapping
work. Git remains the merge and review authority; a hand-off does not grant another
agent permission to push, comment, or update a pull request.

## Harness integration

The disclosure layer should be independent of model transport:

- the current native loop receives the tools as ordinary function schemas;
- a Codex adapter receives the same initial context manifest and exposes the same
  read tools through its tool bridge, while its own compaction/session state remains
  in the run directory;
- a DeepSeek/OpenAI-compatible adapter receives the same messages and schemas, with
  the same ledger and compaction policy;
- an external harness adapter may consume a JSONL event protocol, but it must return
  refs, tool events, and a final summary so `transcript.jsonl` stays authoritative.

The backend must never bypass the repository allow-list, the per-run write limit,
secret redaction, or the process-group lifetime. A richer harness changes how the
agent reasons; it does not widen what it may modify.

## Delivery plan

1. **Index and references.** Add the local index, `repo_overview`, `repo_tree`,
   `repo_search`, `repo_read`, and README outline tools. Add bounded results and
   provenance to the transcript.
2. **Forgejo disclosure.** Add issue/PR overview, search, comment cursors, and
   explicit expansion on top of the existing repository gate.
3. **Context ledger.** Replace the unbounded message append in `model_loop` with
   reference cards, a configurable soft/hard budget, and hash-based deduplication.
4. **Compaction and hand-off.** Add cached summaries, `context_compacted` records,
   durable hand-off files, and overlap checks.
5. **Harness adapters.** Put the native, Codex, and DeepSeek transports behind one
   `Harness` interface and run the same disclosure contract through each backend.

Each step should retain the current `shell`, Git identity, clone/fetch behavior,
Forgejo write controls, and append-only transcript. A feature flag can keep the
existing full-history behavior during migration, so a failed indexer or unsupported
language never prevents an agent from doing ordinary Git work.
