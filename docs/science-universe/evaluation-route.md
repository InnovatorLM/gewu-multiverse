# Science-universe evaluation route

The synthesis target is a standard Harbor task package following the Terminal-Bench-Science data shape. Use ACS first to generate a complete trial with `config.json`, `result.json`, ATIF `agent/trajectory.json`, verifier output, and the immutable task package. Then run the four evaluation views supplied by `unified-evaluator-pipeline`: task direct review, task Science-style WinRate, trajectory direct review, and trajectory WinRate. A hand-written Markdown trajectory is evidence for humans but cannot replace an ATIF trajectory.

The ACS run uses the workspace DawnFM account and model `deepseek-v4.1-flash-1017`, with one trial, one concurrent job, no retries, direct Pod deletion, and independent cleanup verification. Keep task failures, infrastructure failures, verifier defects, and sandbox leaks as separate findings.

The target model difficulty is below 30% correct when feasible and below 50% is acceptable. Report reward, input/output tokens, model calls, tool calls, retries, and elapsed time; these are supporting difficulty evidence, not substitutes for scientific quality.

The synthesis process should preserve stage boundaries: Seed Enhancer, Task Builder, and Verifier each use a fresh sandbox and only declared mounts. The verifier must independently run a clean reference solution into an empty output directory and pass only declared artifacts to a fresh no-network test container. Retain failed packages and reports for diagnosis, but never publish credentials, runtime metadata, private tests, reference answers, or raw sensitive trajectories.
