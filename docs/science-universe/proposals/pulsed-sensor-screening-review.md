# Independent pulsed-sensor direction screening

Decision: do not approve a mixed-ion concentration-prediction or generalization
task from current metadata. Continue file/provenance inspection only. No task
implementation, live evaluation or scientific acceptance is authorized.

The independent reviewer read local repository and primary-paper metadata,
without accessing actual Parquet contents, network, API or ACS. The declaration
of4595153timepoints represents at most53electrode×mixture conditions
(3polymers×3electrodes×6mixtures minusPAN03mix4). If11files exist per condition,
that implies583files, not independent experiment replication. Actual coverage
must be checked. A concentration/mix label, pC, reversible filename or ID in
predictor input could directly expose the answer. Row-level random splits and
same-experiment steps crossing folds cannot demonstrate independent transfer.
Six fixed mixtures cannot establish a general continuous three-ion response
surface; recipe classification or lookup is not proof of quantification.

The associated preprint's metadata abstract describes mixtures synthesized from
individual-ion responses for ML, while the repository describes experimentally
measured mixed-ion traces. These may be complementary training/validation
assets rather than a contradiction; their mapping has NOT been verified.
Do not merge their identities or treat a scaled parallel-RC assumption as truth.
Three electrode IDs do not establish manufacturing batches/dates/replicates.

Possible narrower decisions require additional evidence: independently validate
an RC mixture-combination rule using calibration inputs and separate real
mixtures; evaluate multisensor information only for the measured recipes with
strict experiment grouping and simple baselines; assess pulse acquisition costs
only with actual timing/state-dependence controls; or study batch transfer only
with documented independent batches. No such evidence is currently verified.

Required file inspection includes checksum, units, actual condition coverage,
file duplication, experiment hierarchy, time resets, sequence/drift confounding,
and actual current versus nominal protocol. If necessary calibration assets or
independent replication do not exist, stop generalization/mechanism-task design
rather than manufacture a difficulty claim. A large real dataset alone does not
satisfy the universe's scientific task-value requirement.
