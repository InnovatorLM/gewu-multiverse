# Role trajectory retention

The deployed role Codex runner streams stdout JSON events and stderr to each role's persistent home. No engine restart is required: atomic replacement of the role script affects new processes only. Existing runs cannot retroactively acquire missing events.

Host path:

`universes/my-terminal-bench-science/.config/gewu-multiverse/agents/<role>/home/role/trajectories/<timestamp>-<uuid>/`

Each directory contains `events.jsonl`, `stderr.log`, `metadata.json`, and, when Codex returns one, `final-message.txt`. The report includes `trajectory_dir` (the corresponding chroot path). Metadata records the role, designated provider/model, timestamps, exit code, and completion/timeout status. A hard kill may leave status running or missing metadata; this must be interpreted as interrupted, not completed. Newline-delimited output is flushed as lines arrive. Timeout terminates the child process group and retains partial lines received before termination.

Gateway tokens and the role Git token are redacted before writing. Files are mode 0600 and archives 0700 inside the role's private home. Raw trajectories can contain task data and should remain private; these logs are not immutable or protected from the role's own UID. No retention deletion is enabled.

Operator index:

```bash
python gewu-multiverse/deploy/science/list_role_trajectories.py
```

Read a selected `events.jsonl` directly as operator. Avoid publishing private evaluator trajectories or placing them in shared Git. The index tolerates interrupted metadata and prints only paths/status/size.

Deployment backup and receipts: `.state/trajectory-rollout/1793282987810172653/`. Rollback replaces each role's runner atomically with its backed-up `<role>.py`, preserving root ownership and mode 0755. Do not rerun full role provisioning (which also touches credentials and configuration) just to update this script.

## Operator website

The loopback monitor on port 8765 includes a complete archive panel. Choose a
role/run and load successive pages; appended events are fetched every 60 seconds.
Native transcripts and Codex JSON archives are both indexed without automatic
deletion. Incomplete trailing lines are retried. Displayed data is redacted.
This operator view does not expose evaluator data to author agents.

The engine already limits tool outputs sent to the model. Archives preserve the
recorded events; they cannot reconstruct previously discarded data or model
reasoning that was never returned by the provider.

The archive selector also includes log: runs, exposing retained run.log output
with the same byte-cursor pagination and redaction as event archives.
