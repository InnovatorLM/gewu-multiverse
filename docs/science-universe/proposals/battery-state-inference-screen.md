# Battery reopening screening: internal-state deployment, not charge optimization

Origin: independent control-plane research; not production-author delivery or use of its session allowance. Existing battery NO-GO remains unchanged. No simulation, task implementation, LLM/API testing, ACS, role workspace or credentials used.

## Decision

CONTINUE only a new scientific-problem/contract review, not implementation. There is first-hand evidence of a useful, distinct scientific decision: whether agreement with measured terminal voltage is enough to deploy a reduced electrochemical state estimator for a specified INTERNAL state. There is not yet sufficient evidence to approve a Harbor candidate or live difficulty trials. If a concrete nontrivial and fair evidence contract cannot be established, STOP this new direction as well.

This revises one overly broad possible interpretation of the old rejection: calling an existing simulator does NOT itself remove scientific value. Selecting a valid state-estimation inference under measurement limitations can be substantive. The previous version was rejected because of unspecified performance needs, physical extrapolation and control-template overlap, not because PyBaMM is available.

## Primary evidence actually read

1. Existing retained Marquis2019 arXiv1905.12553v2 LaTex and PDF, DOI10.1149/2.0341915jes. Introduction explicitly motivates reduced models for BMS speed/memory/convergence and pack modeling. It gives input-parameter asymptotic applicability conditions, not a universal certified finite error bound. Its terminal voltage averaging discussion is not a theorem for arbitrary internal local potentials.
2. NEW: Moura et al., Battery State Estimation for a Single Particle Model With Electrolyte Dynamics, IEEE TCST25(2),453–468, DOI10.1109/TCST.2016.2571663. Crossref title/DOI -> OpenAlex discovery -> HAL01478641v1 document. Actual PDF1,819,782bytes, title/authors/DOI matched. PDF includes author-version cover submitted2Apr2019; do not call it publisher version. Extracted text retained.
   Abstract: BMS internal-state estimation from current/voltage, convergence assuming total lithium known. §V/Fig10–11 and conclusions discuss biased solid/electrolyte states when lithium inventories are incorrect. Text explicitly explains voltage can agree when electrolyte endpoint log-concentration DIFFERENCE agrees even if absolute concentrations are wrong. It says robustness to diffusivity/conductivity uncertainty needs further work. This is a limitation of a particular analysis, not a claim nothing has been published since2017.
3. Existing Chen Crossref abstract and PyBaMM source/licence: room-temperature discharge/relaxation validation does not establish fast-charge internal-state fidelity. No new Chen full text obtained. No claim current Chen package is validated for the proposed deployment.

## Distinct decision and potential evidence contract

Decision owner: BMS model-validation engineer deciding whether a voltage-calibrated estimator can support a named internal-state monitoring claim over a declared measurement protocol, or whether further calibration/measurement is required. Select one scientifically sourced state/claim BEFORE designing instances; do not demand arbitrary accurate hidden fields.

A defensible finite negative contract could ask for two physically admissible explanations/initializations or parameter-calibration hypotheses that satisfy the SAME public current/voltage measurement envelopes yet disagree on the selected internal monitoring claim by an independently justified amount. Freeze allowed model family, positive physical ranges, mass balance/initialization, measurement units/timestamps/error justification and state variable. Any valid witness pair accepted; trustworthy evaluator resimulates it with convergence checks. Self-reported trajectories are evidence to reproduce, not ground truth. An actual finite counterexample disproves the stated sufficiency claim; it does NOT prove global unobservability or that every protocol fails.

Do NOT copy the EIS pattern without scientific justification. This is potentially a nonlinear distributed-state inference problem, but merely splitting nearly equal hypotheses or giving two precomputed labels would be the same low-value witness exercise. The disagreement must change a prior real monitoring decision, under credible sensor/calibration uncertainty. If those cannot be sourced, no task.

A positive deployment conclusion is substantially harder: failing to find a pair is not proof of observability or a uniform guarantee. Do not grade absence-of-witness as acceptance. A complete positive contract would require a proved restricted family/estimator validity theorem or an explicitly finite validation suite with limited claims, independently justified coverage and conservative unknown option. No such contract currently established; therefore cannot yet propose a compulsory yes/no deployment verdict.

No prescribed optimizer/observer gains. No exact author parameters privileged. No statistical confidence claim for arbitrary boxes. No real plating safety inference. No hidden parameter scenarios, no post-hoc tightened thresholds, no need to beat a contrived charging-performance score.

## Comparison with existing work

Science reactor-safety-control: submits control under faults/mismatch, reward from hard constraints/performance on trusted simulator. New question concerns inference from available measurements and whether an internal-state claim is supported, NOT finding safe control. This is a potentially substantive distinction, but no full semantic/novelty review yet. Root retained exact benchmark instruction hashes in battery-benchmark-comparison.json; this screen relies on that local comparison record, not a new corpus-wide search.

Official PyBaMM lithium-plating.ipynb: already demonstrates DFN, rate-sweep CCCV and plating-model comparisons. Repeating it is rejected. Moura paper also contains an estimator algorithm and example biases; implementing those figures verbatim is likewise rejected. A task would need a newly specified and independently useful measurement/initialization validation decision, not an instruction to reproduce Fig10.

Existing offline42runs establish model differences and local/average disagreement for nominal Chen models, but DO NOT establish two hypotheses matching identical noisy voltage observations with different scientifically important internal states. They cannot be recycled as the required inverse-problem witnesses. No new simulation performed during this screen.

## Minimum reopening gates

A. Identify exact target internal state, deployment decision and measurement/calibration uncertainty from a primary scientific/engineering source. Neither arbitrary20mV nor a paper's plot error can be imported as tolerance.
B. Establish model/parameter applicability for that decision; avoid treating DFN as experiment. Use an actual known model-family inference problem if appropriate, labelled simulation-only.
C. Independent preliminary feasibility evidence: admissible hypotheses, matched PUBLIC observations, meaningful distinct internal conclusions, conservation and mesh/tolerance checks. Need numeric sensitivity to uncertainty and simple baselines. No executable research is authorized by this document itself.
D. Demonstrate that ordinary OCV/SOC lookup, exact online code/paper example or one-off model switch does not settle the core decision. Conversely, do not reject a scientifically valid simple solution merely to manufacture difficulty.
E. Define a fair non-hardcoded negative/positive/unknown grading contract BEFORE model trials; reject global positive claims unsupported by theorem/coverage.
F. Separate semantic novelty and difficulty reviews. Paper availability or an open research topic is not proof of task novelty/difficulty.

## Licence and reuse

Moura HAL landing explicitly labels Autorisation HAL, not Creative Commons. Its linked first-party policy says documents remain copyrighted: users may read/consult/cite with authors/source; reproduction/adaptation/use beyond legal exceptions requires rights-holder permission. Do not redistribute this PDF, its figures, text or algorithm source in a task without clearance. The policy site's own CC-BY footer is NOT the paper licence. Stored privately for research review only.

Marquis arXiv article's CC-BY4.0 was checked in existing version-confirmation receipt; future redistribution must attribute/link/mark changes. PyBaMM fixed source BSD-3-Clause distinct from article licences. Any new code must be independently authored or sourced under a checked licence. Chen paper registered NC-ND terms do not transfer to unrelated software assets.

Final position: a first-hand scientific need now supports asking whether voltage accuracy suffices for internal-state deployment. This justifies a NEW problem-definition review only. Without A–F, do not reopen implementation or live evaluation; current charge-control candidate remains NO-GO.
