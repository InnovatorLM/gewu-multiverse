# First original candidate: robust sensor calibration

The first original candidate lives in the universe workspace at
`universes/my-terminal-bench-science/workspaces/author/candidates/robust-sensor-calibration`.
It is a standard Harbor-shaped package for a measurement-science task: infer a
linear sensor calibration from noisy paired observations containing one gross
outlier, report a robust residual scale, and predict at a query value.

The host-side reference solution and independent verifier pass. Negative checks
reject a wrong prediction, extra fields, and Boolean values used as numbers.
The verifier runs from fixed fixture data and the intended verifier container is
network-disabled. `COMPARISON-REPORT.json` records the local comparison against
71 Terminal-Bench-Science tasks and 223 Terminal-Bench 4.0 tasks; the report
correctly leaves semantic novelty and difficulty as pending evaluator findings.

The candidate is explicitly not release eligible yet. Docker image construction
is currently blocked because this host's Docker daemon returns `unknown` while
pulling `python:3.11-slim`. After registry access is restored, run the Harbor
container build, the clean reference-solution trial, and a DawnFM trial with one
attempt and no retries. Preserve ATIF trajectory, token/tool-call counts, and
cleanup evidence before changing the candidate state.
