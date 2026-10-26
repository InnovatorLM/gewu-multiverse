# Possible separate direction: mixed-ion pulse-response sensor modeling

Research screening only; not approved for task implementation. This is not
an EIS dataset, not the Lissajous article's data and not a synthetic replacement
for missing raw sinusoidal traces.

Zenodo record20058832, DOI10.5281/zenodo.20058832, provides a repository-declared
CCBY4.0raw mixed-ion sensor dataset. Its actual record lists
mixed_ion_raw_public.parquet,172069948bytes,MD5
7498e959c450654adc0ef5fb4a5fc3b5. No data downloaded yet. Repository metadata
claims4595153rows/27columns across PAN/PVA/PVC electrode sets, six mixtures,
OCV/current-pulse protocols and current/potential/time channels. These counts
are unverified until actual file inspection. PAN03mix4is explicitly missing.

Possible scientific decision: whether a shared mixed-ion response model generalizes
across held-out electrode/mixture conditions after accounting for acquisition
protocol and drift, rather than merely reproducing training fits. A valid task
would need domain-grounded motivation, scientifically defensible held-out
splits/metrics and independent verification, not a generic machine-learning
leaderboard with an electrochemical title. Do not turn the metadata's scaled
parallel-RC assumptions into physical truth or a privileged exact parameter key.

Before proposing a task: inspect checksummed bytes/schema/units/time-reset and
condition coverage; find the associated primary experiment/protocol; verify
redistribution attribution and version; audit personal/path metadata; compare
against both science benchmark families; independently review scientific value,
fair metrics and solvability. The larger file or row count alone adds no value.
The existing EIS regression candidate remains disabled and rejected as first task.
