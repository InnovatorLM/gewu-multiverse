# Calibration pilot: author feedback before scientific production

`robust-sensor-calibration` is an infrastructure pilot, not an accepted science
task. Three normal designated-model solver trials succeeded. This small sample
does not estimate a pass rate, but it supplies no evidence for the requested
below50%target (ideally below30%). A harder scientific candidate is needed;
ambiguous instructions or grader surprises must not be used to lower success.

Clarify the residual population, final fit and median-centering convention in
the public contract. The grader's fixed index20 is an implementation fact, not
by itself proof that a valid answer is rejected. A diagnostic reviewer cited a
command which deliberately adds0.001to the correct scale as an alternative
algorithm; that inference is invalid. The same command shows six-decimal rounding
passes. Do not implement reviewer suggestions without checking their evidence.

Comparison scope is current `tasks/` instructions at fixed commits: TB4
`e67a2cb7db4d9795c212909b3395d8c22ad60aec` (66), TBScience
`490884e24647f9b1f7e26457af56428d7763396c` (72). The earlier381instruction sweep
also included historical tasks, CI fixtures and templates; those are not all
current benchmark tasks. An exact-source subset preserves138existing comparisons
without new model judgments. The model labels13as shared-method and125as
unrelated, with no reported near duplicates. It infers the pilot is easier than
all138from instruction text. These are uncalibrated diagnostic judgments, not
proof of novelty or an empirical difficulty ranking.

Useful author comparisons include science tasks
`engineering-sciences/electrical-engineering/navigation-sensor-calibration`,
`earth-sciences/geosciences/hbv-calibration-1`, and
`earth-sciences/environmental-sciences/hysteretic-aquifer-control`. Inspect their
actual fixed-version inputs, outputs and scientific decisions. The model's
shared-method labels can be too broad; numerical computation alone does not
establish a shared research method. Do not copy or repackage benchmark tasks.

For a new proposal, identify a real scientific decision or identification problem
whose answer is cheap to verify but requires nontrivial analysis. Specify data
provenance/license, identifiability assumptions, an explicit output contract,
independent executable verifier, intended scientific difficulty and concrete
comparison with existing tasks. Freeze the author commit and image digests
before blind solver trials. Report infrastructure errors separately from wrong
answers, record all outcomes and aggregate tokens/tool calls, and retain cleanup
proof. Scientific acceptance, first-pilot user approval and curator merge remain
separate pending steps.
