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

`prototype.py` now builds two nine-frequency synthetic cases with explicit
parameter boxes, component envelopes and a finite measurement menu. Run
`PYTHONDONTWRITEBYTECODE=1 python3 prototype.py`; the retained output is
`docs/science-universe/proposals/eis-prototype-fixtures.json` from repository root.
Known witnesses are research fixtures only; this is not a numerical fitting
solution or a solver-visible Harbor package. `prototype_checker.py` separately
implements rational forward evaluation and interval exclusion without importing
`feasibility.py` or the generator. The generator calls the checker to validate
its fixture reports; this is not independent scientific review of their design.

Seven test methods now pass, including serialized feasibility slack greater
than0.009ohm for both fixture witness types, branch permutations, alternative
series resistance, false certificates/statuses, fabricated D vectors, wrong
units/negative resistances, equal-tau reductions and binary float refusal.
The earlier486single-branch controls and7203rectangle controls remain passing.

The original close-tau pair is so similar that1e-6ohm future precision does not
separate it in this menu. The explicit fixture therefore uses1e-9ohm precision
for two options solely to exercise the strictly-separating/tied-cost interface.
These are synthetic acquisition units and hypothetical precision, not a claim
of attainable instrument accuracy or meaningful scientific measurement costs.
This is a concrete warning for redesign: a realistic harder candidate needs
physically justified measurement precision/cost and less trivial ambiguity,
followed by numerical fitting/resource measurement and independent review.
The checker trusts operator-authored public case metadata; it is not yet a
hardened general input-schema validator or a release-ready Harbor verifier.
No models, ACS instances or acceptance workflows are invoked by these checks.
