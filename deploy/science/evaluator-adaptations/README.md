# Local evaluator adaptations

Base: unified-evaluator-pipeline commit
`8650fd5821da347e64716ee96e799ba34b8b3951`.

Apply the patch at that repository root and copy `test_runtime_storage.py` into
its `tests/` directory. These changes are retained here for reproducibility;
they have not been pushed to the private upstream repository.

The runtime accepts the specific FUSE filesystem only when
`UE_VERIFIED_RUNTIME_ROOT` exactly matches the requested root, outside the
task, and its atomic replacement and SQLite WAL checks pass. Default rejection
remains. This opt-in does not provide namespace isolation.

Mock subprocess tests mock only filesystem-type detection. Timing assertions
now measure actual process overlap and bounded completion rather than assuming
sub-70ms shared-filesystem writes. Run tests with workspace Python3.12 on PATH,
workspace TMPDIR and PYTHONDONTWRITEBYTECODE=1. No live API account is used by
these tests. Focused 27-test recheck passed; full rerun status is recorded in
the launch report.
