# Decision-contract source review — terminate current task proposal

Decision: STOP current battery-degradation Harbor direction and further threshold hunting. Existing evidence supports a capacity-trajectory METHOD COMPARISON, not a justified real recalibration-trigger decision. Do not implement or spend live evaluation budget. Reopening needs a concrete external monitoring/maintenance requirement and independent validation design, not another convenient percentage.

## New first-hand source actually retrieved

Liu et al., official PHM Society article DOI10.36001/phmconf.2021.v13i1.3053, current landing title “An End-to-End Learning Framework for Early Prediction of Battery Capacity Trajectory”. Crossref metadata carries an earlier/different title and abstract values; source conclusions below come from actual publisher PDF, not discovery metadata. Publisher landing and full PDF saved; first PDF GET timed out with partial bytes, second completed. Extracted text retained.

Its §metrics and cycle-life discussion explicitly DEFINE EoL for that study as80% of manufacturer nominal capacity, for124LFP/graphite cells nominal1.1Ah, hence0.88Ah. It also evaluates90% and says the predicted capacity trajectory can be evaluated at different thresholds without retraining. This establishes a published study convention and usefulness of trajectory prediction for design/operation/maintenance/second life; it is not a universal battery standard, Oxford-cell criterion or recalibration rule. Its threshold cannot be applied to a cell's FIRST MEASURED capacity as if that were manufacturer nominal.

Publisher explicitly grants Creative Commons Attribution3.0 (body says Unported, policy also links United States variant). For this research only paraphrase/cite; verify exact licence variant before redistributing article assets. Paper licence does not license the Oxford data; ODbL/DBCL applies separately. Nothing here authorizes copying the paper model/figures into a task as novel work.

NREL candidate report request failed DNS; no contents/standard asserted. No manufacturer/standard source was obtained tying Oxford740mAh cells, our observed error, or a particular capacity percentage to recalibration. This is a limited search, not proof no such standard exists. It is sufficient to avoid claiming one has been found.

## Dataset and baseline evidence corrections

Root's full MAT audit reports eight cells and519checkpoints. Four characterization fields C1ch/C1dc/OCVch/OCVdc each have t/v/q/T. Within-trace time values have no duplicates; A subsequent exact v/q/T payload audit found all four traces duplicated between Cell1/cyc7000 and Cell1/cyc7100. Keep these in a single group or explicitly deduplicate; no other exact v/q/T duplicates were found. Approximate similarity and scientific independence remain unproven. Systematic missing checkpoints must be preserved rather than filled as observations. Raw timestamps around735954 conflict with readme's seconds label and resemble MATLAB datenum; encoding remains unresolved, so do not use time-dependent features or integrate against them.

Observed capacity uses absolute C1dc q endpoint difference in mAh; it is NOT current integration. First measured capacities about728–739mAh and last about456–581mAh show degradation, not an external decision contract. First measured capacity is distinct from manufacturer740mAh nominal.

LOCO descriptive baseline: eight folds trained on other cells' eligible late cycles, using held-out cell's first capacity plus cycle. Mean fold RMSE about17.06mAh; corrected across-training-mean constant baseline mean39.917mAh (not earlier42.4); unchanged-first-capacity baseline about114.56mAh. It is cross-cell descriptive comparison, NOT a chronological untouched forecast; training sets overlap and eight folds do not provide eight independent evaluation replications. Residual error is not task difficulty.

Root threshold scan using each cell's first measured capacity is explicitly post-hoc sensitivity:80% crossing observed in all8,70% only2, remaining cells right-censored. Those percentages are not scientifically adopted EoL/recalibration values. First observed crossing does not determine exact/sustained crossing, particularly with missing checkpoints and recovery.

## Why current task should stop

The actual data can support a transparent comparative forecasting exercise. But a new Harbor task claiming actionable recalibration requires a predefined error budget, false-trigger/missed-trigger costs, measurement scheduling constraint and deployment context. None is sourced. Retrofitting80% EoL into “request new calibration” would conflate replacement/life convention with estimator maintenance. Introducing private SOH thresholds or target RMSE would manufacture a decision.

The remaining proposed work would be ordinary capacity regression/temporal interpolation plus grouping and missing-data care, with only8 independent physical subjects. These are useful analysis practices, but no independent hard scientific decision or task value over established battery-prediction benchmarks has been demonstrated. More model trials or threshold scans will not resolve that conceptual deficit.

## What could reverse this decision

A first-party battery-management/test requirement for a SPECIFIC deployment: allowable capacity-estimation error and confidence/coverage interpretation, when an additional reference-performance test is triggered, cost/scheduling and consequence of mistakes, plus suitable independently observed validation data. It must match these cells/protocol or justify transfer. Then predefine temporal/cell split and compare simple methods before deciding whether a new scientific task is warranted. A cited80%end-of-life convention alone does not meet this requirement.

Current proposal is superseded by this STOP review. Keep source/evidence for future studies, do not present it as accepted science-task work or ongoing production author progress. No implementation, LLM/API test or ACS performed in this source review.
