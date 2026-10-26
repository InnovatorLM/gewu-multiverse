# EIS research scope v3: explicitly seek a distinguishable witness pair

Status: independently approved for research-interface prototyping only.
No Harbor release, scientific acceptance or target-model difficulty claim.
All v2 units, bounded-component interpretation, model family, exact arithmetic,
feasibility and exclusion rules continue unchanged.

## Motivation and public objective

The v2 interface intentionally permits any pair of feasible witnesses and a
`not_resolvable` answer for that pair. A feasible single branch can be split into
two near-coincident branches to satisfy strict distinctness while making every
future D arbitrarily small. This is a scientifically valid answer under v2;
it is not fraud or a grading failure. It defeats the intended measurement-design
exercise, however. Do not silently reject it under v2 or reinterpret a pairwise
failure as impossibility of distinguishing the complete model families.

For a research case with the new public field
`measurement_goal: separating_witness_pair`, the stated task is instead:

Find a feasible one-branch explanation and a feasible two-branch explanation
whose bounded-error prediction rectangles are disjoint at at least one available
measurement. This does not assert a future observation must identify a true
physical mechanism.
For that submitted pair compute all exact D values and select the cheapest
strictly separating option, with index as the tie breaker. The published data
must admit such a pair, demonstrated by an exact-checked reference witness.
A response with all D<=1 does not satisfy this explicitly requested contrast
construction. It does not prove the task impossible or the model families
indistinguishable. `not_resolvable` is therefore not an answer to this case's
contrast-construction objective.

Unknown goal values are rejected; an absent field retains v2 conditional-pair
semantics. For `measurement_goal: conditional_pair`, retain v2 exactly: any feasible pair
is allowed and `not_resolvable` is correct if all its D<=1. This mode is useful
as an honest control, but is not evidence of challenging measurement design.
Excluded cases require no one-branch pair and do not make this contrast claim.

This amendment adds an explicit operational witness criterion, not a minimum
hidden tau gap, a claim of physically unique mechanisms, a global experiment
optimum or discrimination between whole feasible families. The same0.01ohm
future precision and synthetic cost disclaimer remain. Public instructions
must state the new field and criterion before any solver trial. Recompute
schema, data, reference and negative controls after any change; v2 review
approval does not automatically approve this amendment.

## Required prototype validation

1. Retain the near-merged pair and prove it remains accepted in conditional-pair
   mode but fails the explicitly separating objective.
2. Exact-verify feasibility and max(D)>1 for independently numerically fitted
   alternative witnesses in contrast mode. Do not rely on generator parameters.
3. Keep full rational D-vector and cheapest-option checks, permutation acceptance,
   all feasibility/exclusion controls and truthful local-resource limitations.
4. Both modes remain research prototypes. Removing this one bypass does not
   establish difficult inference; empirical target-model and scientific reviews
   remain necessary before a benchmark release.
