# Finite-band impedance inference — research draft

This is a synthetic research exercise, not real instrument data or an accepted
benchmark. Solve every case in `/app/data/cases.json` and write a JSON object
mapping its case IDs to reports in `/app/report.json`. Use the public data only.
Python's standard library is available; public networking is allowed.

The family is Z(w)=Rs+sum_k Rk/(1+i*w*tauk). Angular frequency w is in rad/s,
impedance in ohm and tau in seconds. Real and imaginary predictions for each
branch are R/(1+(w*tau)^2) and -R*w*tau/(1+(w*tau)^2). Rs adds only to real.
Parameter boxes are inclusive, branch resistances/tau positive, Rs nonnegative.
All boxes, observation centers, componentwise absolute error bounds, and future
measurement options/costs are in each case. These costs are synthetic acquisition
units, with no asserted physical instrument calibration. Observation intervals
are closed, deterministic bounds; do not infer Gaussian confidence or posterior
probability. A feasible witness fits BOTH components of EVERY observation and
all parameter boxes. Recovering the generator's parameters is not required.

Numeric report fields must be JSON integers (not booleans) or exact decimal /
rational STRINGS. For example `"0.001"`, `"1e-3"` or `"1/1000"`. Scientific
notation is exact; whitespace/underscore separators are not allowed. JSON floating numbers,
NaN and infinity are refused. Rational strings must have a positive denominator.
Represent indices as JSON integers. D vectors must be exact rational values
(strings like `"3/2"`), not approximate/truncated floating displays. Each report:

* `two_branch`: `{"rs":"...","branches":[{"r":"...","tau":"..."}, ...]}`
  with exactly two branches and STRICTLY DISTINCT tau. Branch permutations
  are accepted. Equal-tau branches reduce exactly to one and do not count.
* `single_branch_status`: `"feasible"` or `"excluded"`.
* For `"feasible"`, supply `one_branch` in the same format with exactly one
  branch, and `interpretation: "finite_band_ambiguity_for_submitted_witnesses"`.
  Both witnesses must fit all data. This establishes alternatives within the
  declared family, not unique mechanisms or complete feasible parameter regions.
* For `"excluded"`, supply `certificate: [i,j,k]`, strictly increasing zero-based
  observation indices. The exact interval proof below must exclude every positive
  single branch. Exclusion is NOT proof of exactly two physical mechanisms.

For a feasible report compute a D for EVERY future measurement option, in list
order, using your two submitted witnesses a (one branch) and b (two branches):
D=max(abs(ReZa-ReZb)/(2*error_real), abs(ImZa-ImZb)/(2*error_imag)). Return
`d_vector` and `next_measurement`. Their bounded-error prediction rectangles
are strictly disjoint iff D>1; D=1 means touching and is not separation. Choose
the lowest-cost strictly separating option, breaking cost ties by lowest index.
If every D<=1, `next_measurement` is `"not_resolvable"` ONLY in conditional mode.
An index is an integer, not a string/float/bool.

The public `measurement_goal` is either `"conditional_pair"` (also the default
if absent) or `"separating_witness_pair"`. Conditional mode allows ANY feasible
pair, including a near-merged pair with `not_resolvable`. Separating mode
EXPLICITLY asks you to construct a feasible pair with at least one D>1; a
nonseparating pair is not a solution to this objective. At least one such pair
exists in each supplied separating case. This is a conditional contrast
construction, not globally optimal experimental design or discrimination of
entire feasible model families. An excluded report does not need a one-branch
witness or measurement design, irrespective of the goal field.

## Accepted exclusion certificate

For selected frequencies w1<w2<w3, define q bounds from imaginary observation y
and its absolute error e: qL=(-y-e)/w and qU=(-y+e)/w. A single positive branch
would have q=A/(1+w*w*x), where A=R*tau>0 and x=tau^2>0. Let
N=[q1L-q2U,q1U-q2L] and
B=[w2^2*q2L-w1^2*q1U,w2^2*q2U-w1^2*q1L].
This certificate requires q1L>0, NL>0 and BL>0. Then
xL=NL/BU, xU=NU/BL;
AL=q1L*(1+w1^2*xL), AU=q1U*(1+w1^2*xU).
The predicted third q lies in
[AL/(1+w3^2*xU), AU/(1+w3^2*xL)].
It must be STRICTLY disjoint from observed [q3L,q3U]. Otherwise the certificate
is inconclusive and rejected. Choose a different triple or supply a feasible
one-branch witness; overlap does not establish existence. At least one valid
triple exists for any supplied case without a feasible single-branch model.
This conservative proof uses imaginary components only; witness fitting still
checks both components. All proof arithmetic and grading are exact rational.

The task accepts alternate feasible parameters and algorithms. Do not claim
unmeasured scientific difficulty, physical uniqueness or probabilistic coverage.
All cases must pass for reward1. Resource target:2CPU/4GiB; timeout300seconds.
