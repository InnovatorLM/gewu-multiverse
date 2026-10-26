# Exact-rational scientific feasibility study

This directory contains proposal research, not a Harbor task, reference solution,
verifier approval or completed benchmark candidate. It uses Python's standard
library only and runs no model/API/container.

Run `python feasibility.py` and `python -m unittest discover -s .` from here.

For a single positive Debye branch with any real series resistance,
`q(w) = -Im(Z(w))/w = A/(1+w²x)` with `A=R*tau>0`, `x=tau²>0`.
Two observations imply
`x=(q1-q2)/(w2²*q2-w1²*q1)`.
Each measured imaginary component has an explicitly bounded absolute error,
so each q is an interval. If the numerator and denominator intervals are
strictly positive, interval division bounds x. The first observation then
bounds A; these intervals bound the third q. Disjoint predicted/observed
intervals contradict every positive single-branch model satisfying the error
bounds. All these operations use exact rational numbers. No floating-point
rounding or local optimizer result is used for exclusion.

Discarding correlations makes the intervals wider. Overlap proves nothing:
the result is inconclusive, not a certificate that a single branch fits.
Nonpositive interval denominators also produce inconclusive results. This
simple certificate is incomplete and does not assert model count, arbitrary
circuit non-identifiability, uniqueness of two-branch parameters or confidence
coverage. Exclusion uses imaginary data only, which is sufficient for a
contradiction but not for a claim that real-component data have been fitted.

The study includes two-branch data with an explicit single-branch alternative
inside the component error envelope, separated-relaxation data that exclude
all single branches, and an actual single-branch control. Measurements here are
synthetic noiseless centers with an assumed bounded-error envelope; they are
not random Gaussian draws, real observations, or the proposal's earlier
relative-noise example. A branch swap is exactly prediction-equivalent.

Tests include486single-branch cases across resistance/time/series-resistance
settings and all27combinations of negative/zero/positive error-bound endpoints.
None may be excluded. These controls support the implementation but do not
replace mathematical review of the stated interval argument. Tests also require
the two intended feasibility outcomes and reject invalid frequency/error input.

This advances the fair-verification design. It does not establish realistic
scientific difficulty or approve task implementation. Independent review,
physical model justification, a complete public contract, reproducible data,
scientific comparisons and designated-model trials remain open.

The explicit research interface accepts integers, decimal/rational strings and
Fraction values. Binary floats, bools and null values are refused. For example,
"0.1" means exactly1/10; a float0.1is not silently interpreted as that decimal.
Four test methods now cover this boundary in addition to the486controls.
Independent proposal review found no fatal interval-proof issue but withheld
implementation approval over the incomplete scientific grading contract.

`python measurement_geometry.py` independently checks the proposed conditional
measurement criterion on7203pairs of closed error rectangles with unequal
real/imag precision settings. A pair is disjoint iff
max(|delta_real|/(2err_real),|delta_imag|/(2err_imag))>1. Equality means touching
and does not separate. This is witness-pair geometry, not discrimination of
all feasible models, a probabilistic confidence result or a complete design
optimizer. The v2contract allows exact rational output rather than rounding
this threshold classification.

## Concrete interface prototype

`prototype.py` builds two synthetic cases with explicit boxes, error envelopes
and a finite future-measurement menu. The ambiguous case has five low-frequency
observations from0.01to1rad/s and well-separated tau values0.001/0.01s.
A single branch fits this narrow band, but expanded-frequency measurements can
distinguish the supplied alternatives at the same0.01ohm component precision.
The excluded case has nine observations from1to10000rad/s and a valid exact
triple certificate. All future menu precision is0.01ohm; acquisition costs are
synthetic units, not calibrated physical instrument costs. This supersedes the
initial close-tau fixture requiring1e-9ohm hypothetical future precision.

`prototype_checker.py` separately implements rational forward evaluation and
interval exclusion, importing no generator or fitter. Public units, bounds,
ordered frequencies, positive errors and nonnegative costs are validated.
The generator invokes it to check fixture reports; this is not independent
scientific review. Ten test methods pass, including known serialized-witness
slack>0.005ohm, branch permutations, alternative series resistance, false
certificates/statuses, fabricated D vectors, wrong units/negative resistances,
equal-tau reductions, binary float refusal and noninteger measurement indices.
The earlier486single-branch and7203rectangle controls remain passing.

`reference_fit.py` independently fits numeric parameters using public data only:
log-tau grid, variable projection onto linear resistances, eight starting points
and coordinate refinement. It uses floating least squares/normal equations;
ill conditioning and local minima remain possible. Optimizer failure cannot
establish exclusion. Reports are serialized and then independently checked with
exact rational arithmetic. Generated parameters are never privileged.
The low-band case actually yields a different feasible series resistance near
the public upper bound, illustrating parameter ambiguity rather than proving
that bound is scientifically meaningful. Both cases solve in under a second
on the local host in the retained study: this is not target-model difficulty or
an ACS2CPU/4Gi resource measurement, and the toy may be much too easy.

Reproduce using only the public case mapping (no known witnesses):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 research/eis-identifiability/run_reference_study.py \
  docs/science-universe/proposals/eis-prototype-public-cases.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/eis-identifiability -v
```

The retained `eis-reference-study.json` binds source/public-data hashes and
reports exact feasibility slack, numerical search counts and local timings.
Known-witness research fixtures remain in `eis-prototype-fixtures.json`;
none of these files is a packaged solver-visible Harbor task. No models,
ACS instances or acceptance workflows are invoked. Scientific suitability,
realistic acquisition constraints, meaningful difficulty and independent review
remain prerequisites to release.


The independently scoped v3amendment adds an explicitly public
`measurement_goal: separating_witness_pair` to the ambiguous research case.
It asks for a pair with disjoint bounded-error prediction rectangles at one or
more menu points, then the cheapest such point for that pair. Unknown goals
are rejected; missing/`conditional_pair` retains v2. The near-merged bypass is
retained as a regression: legal under conditional mode, rejected under the
explicit contrast objective. This closes that objective loophole without
hidden parameter gaps; it still does not establish target-model difficulty.
The excluded case does not require a feasible single-branch contrast pair.


## Standard Harbor research draft

`package_draft.py --output <fresh-workspace-directory>` generates standard
`task.toml`, `instruction.md`, `environment/`, `tests/`, `solution/` and
`authoring/` assets. This is independently scoped research packaging, not
release or enabled registration. Only Dockerfile and public `data/cases.json`
enter the solver build context. Case IDs are neutral; no known witnesses or
checker enter the environment. Tests grade against their own authoritative
copy of the PUBLIC observations, so editing solver-visible data cannot relax
tolerances. Reference fitting has no generator or original-parameter access.

Twelve offline tests pass, including executing the generated standalone
solution and grading code in a clean working directory, exact-case coverage,
invalid witnesses/certificates/D/index fields, duplicate JSON keys and
solver-data tampering controls. The generated fixture at workspace state
`.state/eis-harbor-draft-v1` passed installed Harbor0.20.0schema and shell syntax
checks with2CPU/4096MiB metadata. A real local Docker build succeeded; all6image
layer inventories were scanned with no draft checker/reference/test paths and
exact public-data bytes. The audit is path/data checking, not exhaustive inherited
base secret analysis. The image was NOT executed, published to ACR or used on
ACS; no actual Harbor lifecycle, model score or scientific acceptance follows.
Public scoped evidence: `docs/science-universe/proposals/eis-harbor-draft-validation.json`.

The retained first draft's provenance binds research source hashes and its
parent repository commit; the builder itself was uncommitted when that local
fixture was generated, so it is not an immutable registered-source receipt.
Before any real evaluation, regenerate from a frozen committed builder, commit
the candidate package, review source/answer isolation, publish matching images
and register the complete bundle disabled pending operator review.


A second draft has now been generated from committed buildera3cb826 at
`research/harbor-drafts/eis-identifiability`. It passed the same official
mechanical check and standalone reference/grader execution. Its environment
context hash exactly matches the layer-audited first draft image; source hashes
match the committed builder's research sources. Candidate package source must
still be frozen/published/registered through the normal operator workflow
before any live evaluation. It is currently unregistered and not launch-approved.
