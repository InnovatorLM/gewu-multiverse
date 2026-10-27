# Harbor batch execution with mini-SWE 2.2.8

The upstream CLI defaults to `InteractiveAgent`. `--yolo` disables command
confirmation and `--exit-immediately` disables submission confirmation, but
neither disables its prompt to increase an exhausted step/cost budget. With
stdin closed, that prompt raises `EOFError` and Harbor reports
`NonZeroAgentExitCodeError`.

Use the supported upstream `default` agent for unattended evaluation:

```json
{"agents": [{"name": "mini-swe-agent-preinstall", "kwargs": {
  "config": {"agent": {"agent_class": "default", "step_limit": 40}}
}}]}
```

`mini_swe_headless.configure_headless_mini_swe(job)` selects that class without
changing the task, model, scoring, resources or budget. Keep recording the
trajectory's `info.exit_status`: `LimitsExceeded` means the solver exhausted
its allowance, not that it submitted a complete answer. Report that separately
from infrastructure errors and the original verifier's reward.

The published 2.2.8 runtime was checked with a fake model and a one-step budget:
the interactive agent reproduced `EOFError`; the default agent returned
`LimitsExceeded`, saved its state and made no stdin request. This local runtime
regression is not a live model evaluation or a benchmark task.
