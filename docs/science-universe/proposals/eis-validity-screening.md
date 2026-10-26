# Research screening: impedance-data consistency before model interpretation

Status: research direction only; no approved proposal, implementation, candidate
registration or scientific acceptance. The existing EIS fixture remains disabled
and unsuitable as the first science task. This note does not reverse that review.

## Actual scientific decision to investigate

Before interpreting an equivalent-circuit fit, decide whether a collection of
measured spectra supplies sufficient evidence for a stationary small-signal
response at the stated conditions, or needs targeted reacquisition. Potential
inputs include repeated sweeps, acquisition timestamps/order, applied amplitudes,
frequency grids, instrument uncertainty and explicit control measurements.
These are proposed input requirements, not datasets already obtained.

An informative task would distinguish contradictions demonstrated by these
controls from mere inability to fit a chosen circuit. For example, repeat sweeps
can test a declared repeatability bound; amplitude-conditioned measurements can
test a declared small-signal response criterion. A finite spectrum alone cannot
uniquely diagnose drift, nonlinearity, acquisition defects or a physical mechanism.
Accept an explicitly inconclusive finding where available evidence cannot decide.
No generator label or claimed root cause may substitute for observational evidence.

## Sources actually retrieved

TLS-verified official impedance.py documentation pages were retrieved and retained
privately with hashes on2026-10-26:

- https://impedancepy.readthedocs.io/en/latest/examples/validation_example.html
- https://impedancepy.readthedocs.io/en/latest/validation.html

They describe causality/linearity/stability assumptions, KK consistency, practical
finite-frequency limits, Lin-KK fitting and residual analysis. The default mu
cutoff0.85is explicitly a heuristic; it is not a universal physical-validity
threshold. Copying linKK output into a classification is insufficient scientific
work and would repeat the routine-algorithm weakness of the rejected draft.

The cited primary article metadata was independently verified through Crossref:
*A Method for Improving the Robustness of linear Kramers-Kronig Validity Tests*,
DOI10.1016/j.electacta.2014.01.034, publishedJune2014. Only metadata and official
software documentation were read in this screening. Primary full text has NOT
been retrieved or reviewed; no additional theorem, operating threshold, license
or result is attributed to it. No external code, dataset or paper content is
redistributed, and no source-code reuse permission has been established here.

## Conditions before a new proposal can pass

Find accessible primary method evidence and an actual experimental/instrument
context that supports frequency, amplitude, timing and error assumptions. Obtain
redistributable control data, or justify a transparent synthetic acquisition
protocol grounded in that context. Neither dataset nor license exists yet for
this direction; do not implement generated examples and backfill justification.

Specify public bounded/statistical interpretation and independently verifiable
outputs before constructing a grader. Independent repeatability/amplitude checks
may establish contradictions within their declared scope; KK residuals should
be supporting diagnostics rather than a false universal oracle. Investigate
alternative explanations and finite-band limitations. Reacquisition recommendations
must correspond to an explicit observation deficit and actual instrument costs.

Then compare scientifically against both pinned benchmark sources and the
rejected EIS fit fixture, show that a standard library call or generic threshold
cannot complete the actual decision, and obtain independent scientific-value
review before implementation. No live model/ACS budget should be used until
these prerequisites are met. This screening identifies a possible route, not
proof that it is sufficiently difficult, novel, solvable or suitable for launch.
