# Independent diagnostic proposal review

Reviewer: delegated Codex agent `eis_proposal_review`, separate review context.
Reviewed proposal/research at commitd892068; no edits, external API/model tests,
network access or ACS launches. This is diagnostic review, not evaluator-role
acceptance, a human signature or permission to release a task.

Decision: **full Harbor task implementation not approved as-is**.

No fatal defect was found in the positive-single-Debye bounded-error exclusion
argument. Its algebraic expression for tau² is correct; conservative interval
propagation permits exclusion when predicted and observed intervals are
separated. Overlap must remain inconclusive. The reviewer independently ran the
three then-existing tests. It also reported a deterministic randomized
cross-check against linear feasibility in amplitude/tau²; that auxiliary
script/seed was not retained, so no reproducible randomized-validation claim is
made in the published readiness evidence.

Blocking findings:

- The proposal mixes replicate covariance, weighted residuals, statistical
  confidence/profile intervals and bounded absolute-error feasibility. Choose
  the interpretation and specify it before implementation.
- Excluding the single-Debye family does not prove exactly two mechanisms,
  unique two-branch parameters, or physical meaning of equivalent elements.
- Uncertainty and next-measurement deliverables need explicit acceptance
  criteria and independent verification.
- The short feasibility exercise does not establish realistic research
  difficulty. Data/model justification, convergence costs and actual
  designated-model trials are still required.
- A certificate interface must specify angular-frequency units and exact
  decimal/rational parsing rather than silently taking binary floating input.

The controller addressed the input-precision item: the research prototype now
accepts integer, decimal/rational-string and Fraction values; float/bool/null
are refused. Four tests pass, including explicit0.1vs1/10and float refusal.
This change does not resolve the scientific contract findings or turn the
proposal into an approved implementation. Literature retrieval was not
independently checked by this reviewer.

## Revised v2 scope review

The same independent reviewer subsequently read eis-contract-v2.md and the
updated rational research interface. Decision: **conditional approval for
research-prototype generation, fitting and an independently written checker**.
This is not approval of a Harbor candidate, release, scientific acceptance or
empirical difficulty.

The revised contract resolves the earlier conceptual blockers by specifying
bounded-component feasibility; limiting witness/exclusion claims; refusing
exact equal-tau reducible branches; normalizing permutations; requiring exact
rational D with D=1not separated; and limiting measurement discrimination to
the submitted pair. The reviewer checked the interval algebra and closed-error
rectangle criterion. Existing4tests passed in the review environment. Additional
randomized diagnostics were reported in-memory without retained scripts/results;
they are not treated as reproducible launch evidence here.

Conditions for the prototype: publish concrete boxes/error bounds/measurement
options and physical costs; preserve the Debye equation used by the proof;
demonstrate feasibility slack after exact serialization, both case types,
alternative solutions and negative controls. Near-coincident witnesses may still
make measurement selection trivial, and the small feasibility example is not
sufficient benchmark difficulty. Scientific suitability, originality, numerical
resource costs and actual designated-model performance remain unverified.

A retained standard-library measurement_geometry.py additionally reproduces7203
exact closed-rectangle controls in the controller environment. This supports
the conditional pairwise scoring formula, not full-family identifiability or
proposal completion. Next authorized step is the research prototype under the
specified scope, followed by further independent review before Harbor release.


## Concrete finite-band prototype review

The independent reviewer subsequently ran all9then-existing offline tests and
both public-data-only reference fits. Both exact checks passed; local fits took
approximately0.06/0.10seconds. Future precision0.01ohm is sufficient for the
new low-band ambiguous case; fitted-witness D values were approximately
[0.126,843.805,582.819], selecting index1. Generated parameter matching is not
required; a different feasible Rsnear20illustrates parameter ambiguity.
This resolves the initial hypothetical1e-9precision issue for this synthetic
exercise, not instrument/cost realism or scientific/benchmark difficulty.

The reviewer found a valid v2difficulty bypass: split a fitted single branch's
resistance equally with tau±1e-10. Both branches fit; all future D<5e-13;
`not_resolvable` is accepted. This conforms to the current conditional-pair
contract and must not be retrospectively penalized. The controller retained
this reproduction as test_v2_near_merged_pair_is_a_legal_easy_answer.
The reviewer does not approve scientific release or target-model difficulty;
local normal-equation fitting is not global optimization. A public objective
amendment, with fairness/feasibility review, is required if the task must demand
a distinguishable pair of explanations.


## Public contrast-objective amendment review

The same independent reviewer approved v3only for research-interface prototyping.
The reviewer judged that explicitly requiring a feasible witness pair with
max(D)>1changes the public objective fairly, while preserving v2conditional
mode. It must not be marketed as full-family identifiability, mechanism
uniqueness or optimal experimental design. Unknown modes must be rejected;
missing mode may retain v2; excluded cases do not need a single-branch pair.
The document now explicitly limits distinction to bounded-error prediction
rectangles being disjoint, not identification of a real physical mechanism.
This is not Harbor-release permission or empirical difficulty qualification.

The reviewer then checked the actual v3implementation read-only: all10tests
passed, both public-data fits were exact-verified, unknown/missing goal handling
and near-merged conditional/contrast behavior matched the approved scope.
An additional direct check confirmed that an excluded case remains accepted
even with the separating goal, since no feasible single-branch pair is required.
No source edits, API calls or ACS launches were made by the reviewer.

## Standard Harbor draft packaging review

The independent reviewer approved reproducible standard-Harbor research
packaging without release, enabled registration, models or ACS. It then read
the actual generated package and ran all12offline tests: source-file hashes
matched provenance; solver context contained only Dockerfile/public cases;
tests used authoritative public copies; independent numerical solution passed.
No blocking scientific/interface defect was found for this draft scope.

The reviewer identified numeric lexical ambiguity and D-string inconsistency.
The controller made scientific notation explicit in the public instruction,
rejected whitespace/underscore/negative-denominator string forms, and required
D entries to be strings. The reviewer reran12tests successfully and confirmed
these fixes. Its review did not inspect Docker or actual Harbor lifecycle
isolation; separate local layer evidence has a narrower stated scope.
