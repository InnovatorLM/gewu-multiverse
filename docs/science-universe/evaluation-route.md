# Science-universe evaluation route

The synthesis target is a standard Harbor task following Terminal-Bench-Science
format. Current registration checks the immutable source, source-bound published
images, installed Harbor schema, nonempty required files and shell entry-point
syntax. These mechanical checks execute no task code and cannot establish
scientific quality, valid licensing, solvability or runtime correctness.

The ACS solver route uses DawnFM `deepseek-v4.1-flash-1017`, one trial, one
concurrent job, zero retries and direct Pods. Shanghai public ACR images are
used in Beijing ACS. The configured pull Secret is checked against current
cluster state before launch. Each run independently verifies resource deletion;
infrastructure failures and uncertain cleanup cannot count as model failures.

Solver results expose aggregate reward, token counts, model/tool-call counts
and errors. Raw solver trajectories stay private and are not exported to roles
or source control. A hand-written Markdown narrative is not a model trajectory.
The historical plan listed four unified-evaluator views: task direct review,
Science-style task WinRate, trajectory direct review and trajectory WinRate.
Current live evidence covers solver dispatch and task quality diagnostics;
Science-style WinRate and trajectory-view integration have not been verified.
Do not represent those four views as completed or silently synthesize missing
trajectories. Any additional private trajectory processing needs its own
validated data boundary.

The target difficulty is below30% correct where feasible; below50% overall is
acceptable. A few successful trials do not establish a reliable pass-rate
estimate. Token/tool usage supports difficulty assessment but cannot replace
scientific quality. Existing calibration trials are infrastructure evidence,
not an accepted scientific task or a validated low-success-rate candidate.

Quality diagnostics use separate credential-free reviewer tools. Semantic
comparison uses138current benchmark tasks at fixed commits (66TB4,72TBScience),
not the broader381-file fixture/history inventory. Exact citations and factual
adjudication ledgers validate evidence identity, not the truth of every model
inference. Independent factual/scientific review remains required.

Public networking remains enabled as requested. Credential, role and filesystem
boundaries remain in force. Tests and reference solutions are kept out of the
solver image/input; verifier staging is separate. Do not describe the current
nonroot chroots as kernel/container namespace isolation. First-pilot acceptance
requires a complete concrete review package and the user's final approval,
followed by the protected evaluator+owner approvals and curator merge.

The current ACS quality-runtime proof, helper layout, scratch-variable fallback
and latest native-harness limitations are documented in
[Unified evaluator and ACS integration](unified-evaluator-acs.md). This route
remains diagnostic until the complete evaluator dispatch is verified.
