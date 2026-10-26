# Raw pulsed-sensor data screening

Research only; independent screening rejects current concentration/generalization
task design pending provenance, experimental grouping and scientific-value checks.
No Harbor task, model run, ACS run or scientific acceptance is provided.

`inspect_parquet.py` uses pyarrow21.0.0installed in workspace-local
`.local/research-arrow`; run with that directory on PYTHONPATH and the existing
ACS virtualenv Python. Input must be the pinned Zenodo20058832Parquet.
All downloads/state/output remain workspace-local; do not commit the raw172MBfile.

The full-file inventory verified repository MD5 and measured4595153rows,
27columns,583row groups/fileIDs,583protocol combinations and53electrode×mixture
conditions. Several protocol/current fields have5353nulls; whether they map to
OCV must be checked, not guessed. No finite-value/timing/duplicate/experimental
independence audit has yet been done. Concentration, pC and mixture labels are
present: exposing them in a concentration-prediction input would leak targets.
See public structural summary and independent screening in the proposal docs.

`audit_protocol.py` now checks all rows for selected signal finiteness, nulls by
step, stored-order time monotonicity, file identity consistency and exact
selected-payload duplicates. All5353OCVrows lack current/nominal current;CProws
do not. Time and potential are finite, no file-local time decreases/adjacent
duplicate times or identity changes were found. Eleven duplicate payload groups
were found across distinctfileIDs, including PVC01/PVC02mix1records. This is
identity of(time,potential,current) sequences, not all columns and not evidence
of misconduct or a proven acquisition cause. It must be accounted for before
claiming electrode-held-out independence. Public report retains the affected
anonymized fileIDs/conditions for reproducibility. No training or task approved.
