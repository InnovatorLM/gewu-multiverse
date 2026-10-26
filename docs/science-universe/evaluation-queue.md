# Registered solver evaluation queue

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

This queue currently dispatches registered solver trials. It does not build new
candidate images, register arbitrary author commits, run independent quality or
semantic novelty reviews, produce acceptance receipts or merge tasks. Those
workflow stages still require implementation/validation before unattended
scientific production can be declared ready. The calibration task remains an
infrastructure pilot, not an accepted scientific task.


## Register another immutable task (operator)

`register_evaluation.py` accepts `--evaluation-id`, `--repo`, `--commit`
(full 40-character commit), `--task-path` (relative directory), and `--template`
(root-owned trusted solver configuration). Run with the controller stopped.
The tool reads Git objects rather than the mutable checkout, rejects links and
special files, requires standard Harbor files, and preserves source commit/path
in private provenance. It freezes the snapshot, rewrites the dataset selection,
validates the existing designated-provider/image rules, and publishes only the
ID/hash in the evaluator catalog. Existing IDs cannot be overwritten.

This is operator registration, not automatic author registration or a build
service. The operator must first verify that the trusted template's digest-pinned
images match the task environment. No image/task correspondence or scientific
acceptance is inferred by this command. If publication of the catalog fails after
registry persistence, repair the catalog from the registry; do not reuse the ID.
Offline boundary checks: `deploy/science/test_register_evaluation.py`.
