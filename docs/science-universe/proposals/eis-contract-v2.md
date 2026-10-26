# EIS finite-band inference: proposed contract v2

Status: proposed replacement for the unsettled inference/uncertainty clauses;
not approved, not implemented as a Harbor task, no scientific acceptance.
This version keeps the research goal of finding what measurements establish
and what additional measurement can discriminate. It replaces unsupported
statistical language with explicit deterministic feasibility claims.

## Scientific meaning and data

Use independent synthetic measurements from the positive Debye-relaxation family
`Z(w)=Rs+sum Rk/(1+i*w*tauk)`, with angular frequency w in rad/s, impedance in
ohm, tau in seconds, positive branch values and nonnegative Rs. The public
package states the exact parameter boxes, allowed branch counts, frequency grid,
per-component absolute error bounds and any calibration constraints. Values are
finite decimal strings interpreted exactly, never implicitly binary floats.
Submitted numeric values may also use exact rational strings `numerator/denominator`
with a positive denominator. D vectors use exact rational strings, not truncated
decimals; branch counts and indices use integers. Reject JSON floats/bools for
these numeric fields. Data are explicitly synthetic; physical motivation and the limits of using
Debye elements for actual electrochemistry must be stated.

No Gaussian distribution, covariance estimate, confidence percentage or posterior
probability is asserted. Each observed real/imaginary component is an interval
centered on the published value with its published absolute-error bound. A
model is feasible if all predicted components lie in all intervals and all
public parameter/calibration constraints hold. The data generator's labels or
parameters have no privileged grading status. Model counts beyond the declared
family are outside scope, rather than falsely ruled out.

Prepare at least two cases: one with a feasible one-branch model and a feasible
two-branch model; another with a feasible two-branch model and an independently
checkable exclusion of every one-branch model. Include enough observations and
parameter scaling to require substantive inference; do not assume the tiny
three-frequency feasibility study achieves benchmark difficulty. Numerical
values, rounding precision and runtime costs need calibration before release.

## Solver outputs and acceptance

For each case return a JSON report containing:

1. A feasible two-branch witness, with branches sorted by tau solely for
   serialization. Require two strictly distinct tau values: equal-tau branches
   combine exactly by summing R and cannot count as two-process evidence, even
   when their resistance values differ. Normalize branch permutations rather
   than reject an otherwise equivalent parameterization. No exact match to
   reference or generator parameters is required.
2. `single_branch_status` equal to `feasible` or `excluded`. A `feasible` status
   requires an explicit one-branch witness satisfying every observation and
   public constraint. An `excluded` status requires a certificate that the
   independent checker validates over all positive single-branch parameters.
   The initial accepted certificate grammar is a strictly increasing triple of
   observation indices; the verifier applies exact rational interval reasoning
   to imaginary components. The complete public data must admit at least one
   such triple for every case labeled excluded. Overlap/inconclusive triples
   fail as exclusion evidence; this is a restricted proof interface, not a
   mandate on how the solver fits or reasons.
3. When both witness models fit, a statement of finite-band ambiguity between
   those supplied models. This is existence of alternatives, not a complete
   parameter region or proof that all possible mechanisms are understood.
4. For an ambiguous case, choose one next measurement from the published finite
   candidate list. Every candidate lists angular frequency, separate real/imag
   future absolute-error bounds, measurement cost and any instrument constraints.
   For the two submitted feasible witnesses compute
   `D(w)=max(|Re Za-Re Zb|/(2*err_real), |Im Za-Im Zb|/(2*err_imag))`.
   Their future component-error rectangles are strictly disjoint iff D>1.
   This asserts only pairwise discrimination for the submitted witnesses.
   It does not guarantee distinction between entire feasible model families.
   Return the full D vector, the cheapest strictly separating option if one
   exists (ties broken by the published candidate index), or `not_resolvable`
   if every candidate has D<=1. Compare exact rational D values recomputed by
   the verifier: D=1 means touching/overlapping closed rectangles and does not
   count as separation, irrespective of rounded display values. The verifier
   recomputes all values; choosing
   one weak pair cannot establish family-wide identifiability.

The scientific objective of the measurement step is an operational cost decision
under a bounded precision model. Use strictly positive future error bounds and
public costs. The pairwise conditional nature must be explicit in instruction
and report; do not call it globally optimal experimental design.

## Independent checks and integrity

A verifier uses a separately written rational forward equation for component
feasibility and measurement scoring; it does not import the author's fitter or
generator. Source review checks the exclusion algebra and implementation.
Reference fitting uses a distinct numerical strategy, followed by exact
verification of serialized values. Inputs must be rounded with slack larger
than serialization error; do not grade near a fabricated floating-point cliff.
Reject nonfinite fields, out-of-bounds witnesses, invalid indices, unsupported
status strings, wrong units/sign conventions, false certificates and fabricated
measurement vectors. Accept valid alternate witnesses and parameter order
permutations after canonicalization. An always-feasible/always-excluded response
must fail on the opposite case. Zero/noisy interval precision must not make
future discrimination undefined. Real and imaginary feasibility are both
checked even though exclusion can use imaginary data alone.

All data, boxes, tolerances, admissible models and certificate grammar are public.
No test/solution files or credentials enter the solver image. Standard Harbor
structure, independent reference/negative checks, image/source binding and ACS
cleanup apply. Public networking remains enabled. Initial resource target is
2CPU/4GiB, pending measured convergence costs; no empirical difficulty is claimed.

## Review and implementation boundary

If this scientific scope is independently approved, prototype generation,
fitting and the independent checker may begin. A prototype must then demonstrate
both required cases, precision slack, alternative-solution acceptance, rejection
controls and resource feasibility. Failure to achieve meaningful research work
or target-model difficulty requires redesign before release, not hidden tests.
This scope decision never grants candidate acceptance, curator merge or user
approval for the first completed pilot. Complete benchmark comparison and
primary-source/model suitability review remain part of scientific evaluation.
