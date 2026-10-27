# Independent re-proposal sketch: inventory/state observability

Status: PROBLEM-DEFINITION RESEARCH ONLY. Independent new direction, not reopening the old charge-control implementation gate. No simulation or task implementation authorized/performed here.

## Exact primary-paper evidence and limits

Moura author manuscript main text §II-B [A1]–[A4]: electrode solid concentration/reaction flux homogeneous in x, exchange current replaced by its x average, solid/electrolyte lithium inventories conserved, symmetric transfer coefficients. §II output derivation [A5]–[A6] additionally approximate spatial kinetic factor and electrolyte conductivity. §III-E [A7] requires solid inventory known; initial observer must obey the identical inventory integral. §III-F [A8] requires electrolyte inventory known; later [A9] approximates electrolyte diffusivity as constant. §III-E local output inversion assumes the other inputs/states known or convergently estimated; local invertibility is not a global identifiability guarantee.

§V-C/Fig10 deliberately makes observer solid inventory5% too large. After an approximately750s transient, reported surface-concentration RMS errors5.20%/2.87%, versus voltage RMS7.4mV, near the correctly initialized case6.7mV (§V-B). These are reported numerical results under the paper's parameter/model/UDDS protocol, not independently reproduced results, instrument error bounds or universal thresholds. §V-D/Fig11 treats electrolyte inventory separately; endpoint logarithmic concentration difference can remain right while absolute concentration is wrong. Conclusion explicitly states biases depend on which internal state is to be monitored.

CRUCIAL: an OBSERVER with output correction can fit voltage while internal estimates are biased. This is NOT automatically two autonomous physical forward-model solutions fitting the same bounded data, nor proof of structural nonobservability. A 7.4mV RMS residual does NOT imply componentwise residual within7.4mV. Do not transplant this number into a bounded-error grader.

The known conservation/offset mechanism and OCP near-flatness are already in literature. Asking to repeat a5% inventory perturbation or explain these mechanisms is not a new research task. Same caution for computing an OCP lookup inversion or a fixed rank test.

## New finite-instance hypothesis (not established)

Select a specific inventory/state monitoring claim whose acceptance matters for an independently sourced BMS validation use case. Provide a real documented or explicitly synthetic measurement protocol, current waveform, voltage series, temperature, timing, known parameters, physically justified calibration ranges and measurement error specification. Declare which quantities are known and which initial inventories/states may vary. Initial profiles must belong to an explicitly justified restricted physical family; do not allow arbitrary high-dimensional functions merely to force ambiguity.

For a finite negative sufficiency question: two distinct admissible forward explanations that both fit all public observations but give decision-relevant different inventory or internal-state values would be a valid counterexample. Need ACTUAL numerical existence evidence before any task proposal; current observer plots do not provide it. They may not exist once all known calibration constraints are imposed.

If evaluating an estimator rather than forward equivalence, freeze its publicly specified input/initialization/calibration class and target internal state. Independently recompute observer trajectory and assess whether a public voltage-only validation rule incorrectly accepts it on a trusted synthetic validation plant. This is a model-validation experiment, not proof all estimators fail. Defining a new justified validation rule, rather than reproducing known observer biases, is the possible scientific contribution. No arbitrary thresholds, forced negative answer or undisclosed plant parameters.

## Candidate executable-data contract, not implementation

Inputs: complete frozen model/parameter source references; timestamped I,V and optional documented auxiliary measurements; unit/time conventions; measurement residual norm and noise interpretation; admissible initial/parameter constraints and conservation laws; exact target internal quantity and monitoring decision. No hidden true-state key used for uniqueness grading.

Output mode N: submit two admissible initializations/calibration hypotheses and their reproduced evidence manifest. Trusted solver computes predictions independently. Accept any pair satisfying all declared public data and physical constraints plus the predeclared scientifically meaningful decision disagreement. Reject infeasible conservation, copied self-reported trajectories, failure/events before required observation horizon. Use numerical uncertainty margin supported by independently converged calculations; thresholds exposed before trials. This proves a finite insufficiency claim only.

Output mode P/unknown: do not require everyone to find a counterexample or label inability to find one as positive certification. A positive answer needs a checkable exclusion argument/validated bound for the declared restricted family, or a finite specified hypothesis list covering ONLY that list. Until both possible outcomes are fairly checkable, do not publish a general yes/no task. An explicitly counterexample-construction instance is fair only if public wording states that objective and independent existence witnesses exist; that alone does not establish scientific value.

Extra measurement: a proposed current pulse or independent calibration/measurement can be scored only if measurement availability, cost and forward response are scientifically grounded. To show two submitted hypotheses separate is easy but only pairwise; it is NOT proof all initial-state/inventory uncertainty is resolved. Distinguish a measurement planning suggestion from globally sufficient experiment design. No ‘find best next pulse’ filler.

## Nontriviality and independent evidence path

1. Establish named decision/variable from first-hand BMS practice; obtain legitimate residual/noise and calibration accuracy scope. No scientific deployment contract has yet been found here.
2. Determine whether exact conservation/constant offsets or simple OCP algebra settle the candidate instance. If yes, pedagogical regression only unless independently useful additional inference remains. Do not hide the symmetry or add irrelevant mechanisms to increase failure.
3. Use multiple plausible inventory/initialization constraints and sufficiently informative protocols motivated BEFORE seeing solver outcomes. Need genuinely different supported conclusions, not simply driving a fixed known failure. This is a future authorized study, not permission to run it now.
4. Independently obtain valid witnesses or exclusion controls; test conservation, full time horizon, solver/grid uncertainty and whether small uncertainty changes reverse verdicts. Distinguish state mis-estimation from model mismatch and sensor error.
5. Compare against OCV/SOC lookup, simple calibration/least squares, the paper's direct observer algorithm and existing PyBaMM demos. If copying a plot, swapping two models or routine bounded fitting suffices for whole result, STOP.
6. Compare full scientific workflow with Science reactor-safety-control: do not submit new controls under hard constraints. The potential distinct core is whether measurements support an INTERNAL inference. This remains a hypothesis of value, not novelty acceptance.
7. Do not use hidden ground truth, priors or private error tolerances; allow all equivalent parameterizations and scientific alternatives. Empirical model difficulty comes only after valid question exists, never guides threshold choice.

## Decision

CONTINUE a narrowly scoped inventory/state-observability scientific contract review, because first-hand scientific need is now explicit. STOP implementation/live trials until the independent physical/noise/decision contract and feasible nontrivial instance are established. No new proposal acceptance yet. Existing charge-control NO-GO remains.

## Reuse

Paper HAL Autorisation permits reading/citation but not blanket redistribution/adaptation. Keep PDF/private extracted text out of task/public repo; independently author any code or use separately licensed verified implementations. PyBaMM BSD-3-Clause and Marquis CC-BY4.0 are separate. Citation does not grant code rights and neither paper's convergence assumptions automatically hold for installed canonical PyBaMM SPMe.
