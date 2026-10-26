# Primary-source screening: time-domain impedance validity evidence

Research only; not an approved task proposal or permission to copy experimental
data. This is a new route after rejection of the ideal-Debye fitting first task.

Retrieved the11page repository PDF of Zabara et al., *Utility of Lissajous Plots
for Electrochemical Impedance Spectroscopy Measurements: Detection of
Non-Linearity and Non-Stationarity*, DOI10.1149/1945-7111/ad19eb, published
10January2024. PDF SHA256:
`d0da564748d83d05bb0fc17bbe427d454e8e856433b8886f031879e5eb422032`.
Source: https://repository.bilkent.edu.tr/bitstreams/37085292-e3c5-4aa9-b25e-aa85bd981770/download
Private PDF/text retained; no figures, paper text or experimental traces copied
into a candidate. OpenAlex marks the repository location CC-BY, but extracted
PDF text shows publisher copyright and no explicit CC statement was found in
this pass. Do not treat indexing metadata as independently verified permission
to redistribute its traces. Raw experimental-data availability remains unresolved.

## Relevant findings read in the full text

Page1distinguishes linear response and stationarity and describes limits of
finite-frequency KK compatibility checks. Excitation amplitude adequacy depends
on the sample; there is no universal amplitude threshold to import into grading.
The paper specifically excludes changing-system impedance across an entire
spectrum from its subsequent nonstationarity analysis; its treatment focuses
on drifting/decaying response backgrounds and initial transients. A task must
not cite it as covering every possible cause of acquisition drift.

The paper studies current/potential time traces, cycle averaging and Fourier
analysis. Its stated examples show why a single averaged complex spectrum may
lose diagnostic information and why raw cycles/harmonics can inform the
analysis. The conclusion on page10 discusses its investigated scenarios;
it is not a theorem that a distorted curve uniquely identifies a physical fault
or that passing a single graphical diagnostic proves all EIS assumptions.

## Consequence for a potential new task

A stronger scientific decision could concern whether retained raw excitation /
response cycles support a small-signal stationary impedance estimate, which
cycles/frequencies require reacquisition, and how averaging changes the usable
estimate. Any such task needs independently justified acquisition assumptions,
sampling/timing conventions, uncertainty, control evidence and an objective
acceptance rule that tolerates inconclusive diagnoses. Fourier leakage, baseline
transients, excitation harmonics and response harmonics must not be conflated;
a simplistic amplitude threshold or direct linKK call would still be too routine.

Next research gates: verify data/code availability and licenses; obtain or justify
an acquisition protocol with amplitude and sampling controls; distinguish signal
artifacts from actual inferential decisions; independently review a precise
public contract and expected scientific value before implementation. No task,
reference, verifier, model run or ACS execution is authorized by this note.

The original2014Lin-KK paper remains metadata-only in this investigation:
OpenAlex supplied only a closed publisher location. This2024primary source does
not silently replace that missing full-text review for claims specific to Lin-KK.


## Direct repository rights and asset follow-up

The repository landing page and its own REST item metadata now independently
confirm the article's declaredCCBY4.0license, including dc.rights and
https://creativecommons.org/licenses/by/4.0/. This resolves the earlier
third-party-index-only license evidence gap for this article. Attribution and
scope still matter; this does not license some separately hosted dataset.
The complete returned bundle and bitstream lists were inspected (pagination
totals checked): ORIGINALcontains only the paperPDF, with LICENSE/TEXT/THUMBNAIL
supporting files. No raw experimental trace file was found in this item.
This is not proof no data exists elsewhere. See
[eis-repository-rights-and-assets.json](eis-repository-rights-and-assets.json).
The data prerequisite for a scientific task remains unmet.
