# EIS proposal: literature and contract review

Status: historical literature review plus current limitations. Research-only
v2/v3 prototyping and standard Harbor draft packaging subsequently received
independent scope review. No scientific acceptance, novelty proof or benchmark
release follows. The consequences/gates below describe the earlier proposal;
current normative interfaces are eis-contract-v2.md and
eis-contrast-contract-v3.md. In particular covariance/confidence/profile-bound
requirements were replaced by explicit deterministic component-error feasibility.
Do not reintroduce those historical statistical requirements into the draft.

## Primary literature actually checked

Crossref metadata identifies:

- *Structural identifiability of impedance spectroscopy fractional-order
  equivalent circuit models with two constant phase elements*,
  DOI10.1016/j.automatica.2022.110463.
- *Revisiting parameter identification in electrochemical impedance
  spectroscopy: Weighted least squares and optimal experimental design*,
  DOI10.1016/j.electacta.2012.09.073.

OpenAlex links the first paper to arXiv2103.00226. The arXiv abstract, HTML
full text and PDF were retrieved with TLS verification and stored privately.
The full text identifies itself as arXiv2103.00226v1,27Feb2021. This preprint
must not be silently treated as identical to the2022journal version. Only
metadata was read for the second paper; no specific scientific result from its
unavailable full text is asserted here.

The first preprint explicitly limits its analysis to noise-free structural
identifiability, excluding excitation selection, parameter estimation and noise
from its practical-identifiability claims. Its conclusion states global
identifiability for a broad range of battery parameters in its specified
two-CPE/Grünwald-Letnikov model. It does **not** establish generic
non-identifiability of all two-branch circuits. Its assumptions and model differ
from the proposed Debye illustrative equation. It supports the distinction
between structural and practical questions, not the proposal's quantitative
noise threshold or a claim that its own method fails.

The arXiv page states a perpetual non-exclusive arXiv license. Availability is
not a permissive source-code/data license. No paper text, figure, Matlab code
or dataset is redistributed in the proposal. Private retrieval hashes are
recorded in the source receipt. License/version checks remain required before
including any third-party implementation/data in a Harbor package.

## Consequences for the proposed scientific contract

1. Use "finite-band practical distinguishability" for the noisy-data question.
   Do not label a poorly conditioned numerical fit "structurally unidentifiable"
   unless there is a structural proof. Distinct ideal Debye poles can be
   structurally separable even when noisy observations cannot resolve them.
2. Define noise covariance and a public feasible-residual criterion. A witness
   consisting of two distinct admissible models which both satisfy that
   criterion can establish practical ambiguity under that criterion. It does
   not prove a full confidence region or posterior probability statement.
3. Do not accept fabricated wide uncertainty intervals by checking only their
   endpoints. Before requesting confidence intervals, define a statistical
   coverage interpretation and an independently verifiable computation. If
   that cannot be done, request explicitly labeled feasible witness sets
   instead; do not call them confidence intervals.
4. A next-measurement score must be defined on a public frequency/precision/cost
   domain and evaluated independently. The nearly coincident illustrative
   branches may remain indistinguishable at all affordable frequencies.
   "No available measurement resolves this at the stated precision" must be
   accepted when demonstrated. An unconstrained best-frequency request would
   be scientifically misleading.
5. Require both a practically ambiguous case and a resolvable case, with
   independent reference calculations. An always-ambiguous report cannot
   pass. No generating circuit label is privileged when equally adequate
   alternatives exist.

## Outstanding proposal gates

The primary-literature search now has a verified relevant full text, but does
not finish physical model selection, uncertainty validation, identifiable-case
construction, experiment-design calibration, independent proposal review,
semantic comparison or licensing. Remain at proposal stage. A scientific
inverse problem is not ready simply because a nonlinear solver can fit it.


## Current source integrity and scientific evidence boundary

An offline byte audit verified all10retained successful source records:
three documentation pages, twoCrossref searches, twoOpenAlex metadata records
and the preprint abstract/HTML/PDF. See eis-source-integrity-audit.json, which
binds the historical source-receipt file by SHA256. The failed license fetch
is excluded from successful retrievals, not silently treated as resolved.
Hash agreement proves retained-record integrity, not scientific truth or reuse
permission. No third-party code or experimental data is needed by the current
standard-library/synthetic draft; package code follows repository licensing.

The revised narrow-band fixture and broad-band exclusion have exact-verified
witnesses and independently scoped interface checks. They do not provide a
primary-source justification for a real instrument's bounded errors, a validated
physical interpretation of the Debye elements or calibrated acquisition costs.
The near-merged-pair regression remains valid under conditional mode; v3explicitly
requests a contrast pair with disjoint predicted-error rectangles. None of these
is full-family identifiability or real mechanism discovery. Primary scientific
suitability, semantic comparison and designated-model difficulty are still open.
The local subsecond reference fits are a reason to investigate task difficulty,
not evidence that the desired<30%/<50%target has been reached.
