# Proposal: impedance model identifiability under finite-band noisy measurements

Status: proposal only; not approved for implementation, not a Harbor task,
not scientifically accepted, and no empirical difficulty result. Proposed ID:
`eis-identifiability`. Domain: physical sciences / electrochemistry.

The research work is deciding which relaxation mechanisms and parameter
combinations are actually supported by finite-frequency electrochemical
impedance measurements. An experimentalist needs a defensible equivalent-model
interpretation and a follow-up measurement plan, rather than one plausible
least-squares fit. Synthetic observations will be explicitly labeled as such;
no claim of real battery/instrument measurements will be made.

## Verified sources and scope

Retrieved with TLS verification on2026-10-26:

- https://impedancepy.readthedocs.io/en/latest/faq.html: simultaneous real/imaginary
  least-squares fitting; sensitivity to initial conditions and global search.
- https://impedancepy.readthedocs.io/en/latest/examples.html: navigation to the
  documented example workflows. This landing page alone is not evidence for
  a particular physical circuit, numerical tolerance or model-validity claim.
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html:
  local bounded nonlinear optimization, Jacobians and scaling considerations.

Private source receipts retain exact bytes, URLs, UTC dates and SHA256. The
attempt to retrieve impedance.py's GitHub license failed TLS validation. No
license was inferred and no upstream code/data is included. If that package
is used, verify its exact version/license before implementation. Scientific
primary-literature support for the selected physical mechanism remains open;
software documentation supports numerical workflow, not physical authenticity.

## Proposed public contract

Supply a finite-band complex spectrum, units, frequency convention, replicate
noise covariance and calibration information, plus a fully specified family of
physically admissible relaxation models and parameter bounds. The simplest
research prototype is

`Z(f) = Rs + sum_k Rk / (1 + 2*pi*i*f*tau_k)`.

Whether a constant-phase or diffusion component is justified must be decided
from cited scientific motivation before adding it. More terms alone do not
create meaningful scientific difficulty. All data-generation and scoring
assumptions, objective functions, noise treatment and numerical thresholds
must appear in the public task contract.

Require a machine-readable report with fitted admissible models, objective
values, supported parameter combinations, profile bounds/identifiability
classification, prediction uncertainty, and a proposed additional measurement.
A correct non-identifiability conclusion must be accepted when the data do not
distinguish models. No hidden requirement to recover generator labels, an exact
random draw or an arbitrary optimizer-specific parameter vector is allowed.
Ordering tau values resolves branch-label symmetry only; it does not establish
physical identifiability. Exact report fields, uncertainty definition,
measurement-choice objective and tolerances remain to be finalized in review.

## Feasibility counterexample already calculated

A standard-library complex-arithmetic calculation used101log-spaced frequencies
from0.1to10000Hz, Rs=5ohm, two branches (80ohm,0.01s) and
(120ohm,0.010001s). A single (200ohm,0.0100006s) branch differs by at most
2.2626730289660313e-9in relative complex response. Against a proposed0.002relative
noise scale, this is about1.13e-6times the noise scale. Swapping branches produces
identical predictions. This is a counterexample to a unique-label grader,
not proof that the proposed complete inverse problem is well designed or hard.

## Independent verification plan

Use an independently written forward evaluator and public weighted-residual
objective. Check units, finite outputs, positivity/bounds, stated model
predictions, objective recalculation and uncertainty evidence. Accept equivalent
parameterizations and properly justified ambiguity. Establish any optimization
gap thresholds with independent solvers and convergence studies, not one
reference run. A profile-interval checker cannot merely accept a claimed wide
interval; its mathematical/numerical coverage checks need specification.

Required negative controls include wrong frequency-vs-angular-frequency units,
wrong imaginary sign, unjustified unique two-branch recovery, ignored noise
covariance, fabricated confidence bounds, and trivial infinitely wide intervals.
Required positive controls include permuted equivalent branches and genuinely
indistinguishable models. Include an identifiable case too, so unconditional
"unknown" cannot pass. This plan is not yet implemented or validated.

## Novelty and difficulty review

A keyword scan of138current pinned benchmark instructions found no impedance
model-fitting task; one EEG task mentions impedance. Keyword absence is not
semantic or implementation originality evidence. Complete semantic comparison,
source/provenance audit and comparison to scientific inverse-problem tasks
remain required. Do not claim novelty until that review finishes.

The intended difficulty comes from multistart constrained inference, ill
conditioning, uncertainty and evidence-based experimental design. Independent
DawnFM deepseek-v4.1-flash-1017 trials must measure actual success, tokens and
tool calls after contract/reference/verifier checks. Target below30% where
feasible, below50% overall acceptable; neither has been demonstrated. Planned
resource envelope is2CPU/4GiB and public networking, pending measured convergence
cost. No live model or ACS run has been launched for this proposal.

## Review decisions required before implementation

1. Cite appropriate primary physical-science sources and settle the scientific
   motivation, data provenance/license and model family.
2. Demonstrate both identifiable and non-identifiable cases with independent
   numerical/analytic evidence; define a fair uncertainty-checking contract.
3. Specify a nontrivial, objectively checkable next-measurement criterion, or
   remove that deliverable if it adds ambiguity rather than scientific value.
4. Review proposal against both benchmark families and approve the scope.
5. Only then implement a standard Harbor package with independent reference,
   verifier, provenance record and reproducible dependencies. Final user
   approval applies at first-pilot acceptance after a complete review package.


Follow-up [literature and contract review](eis-literature-review.md) records a
verified primary preprint, the distinction between structural identifiability
and finite-band practical ambiguity, and required corrections to uncertainty
and experimental-design claims. This does not approve implementation.


A subsequent [exact-rational feasibility study](../../../research/eis-identifiability/README.md)
constructs both an explicit practically ambiguous pair and a case with a
three-frequency exclusion certificate against every positive single-Debye
branch. Its bounded absolute-error setting differs from the earlier relative
noise illustration. It does not approve implementation or measure difficulty.
