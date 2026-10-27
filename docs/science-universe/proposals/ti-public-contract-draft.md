# Ti finite-periodic lattice-stability contract — draft for review

Status: proposed public task contract, not approved implementation. Original potential redistribution and computed-data publication basis remain unresolved. Do not publish raw potential, construct a distributable image or start difficulty trials from this draft.

## Scientific scope

Recover the harmonic response of the specified published Ti1 EAM model at the fixed0K bcc reference structure, then find and verify its lowest harmonic mode on the stated finite periodic grid. This is a model calculation, not experimental titanium, a high-temperature free-energy prediction, a complete hcp transformation or a global Brillouin-zone minimum.

The conventional cubic lattice parameter is3.251Å, with Ti atoms at(0,0,0) and(1/2,1/2,1/2), each mass47.867amu. The6x6x6 conventional supercell has432atoms. Input metadata must list each atom's immutable ID, conventional-cell integer translation, basis ID, Cartesian position and displacement used in every force calculation; arrays are indexed by those IDs, not an undocumented library order. Energies are eV, forces eV/Å, displacements Å.

## Proposed inputs and required outputs

Proposed public inputs are the reference structure/forces and paired plus/minus single-atom displacement forces for both basis atoms and all three Cartesian directions at amplitudes0.001Å and0.002Å. These are actual model calculations, not observations. Publication of these derived inputs remains a rights decision. Raw potential and reference spectra are not assumed to be public inputs.

Return a real translation kernel K[aR,alpha;b0,beta]=−dF[aR,alpha]/du[b0,beta], a spectrum on all216q=(i,j,k)/6 with i,j,k in0..5, and a real432x3displacement pattern for a minimum-grid mode. A small JSON metadata file and numerical array files suffice; exact serialization is to be frozen with actual inputs, before trials. Any equivalent representation convertible using the public metadata is acceptable.

The dynamical matrix uses the basis-CELL convention D_ab(q)=sum_R K[aR,b0]exp(−2πi q·R)/mass. No basis-position phase is included in this convention. A different consistent gauge is acceptable if converted or declared. Each q has six folded conventional-cell branches; grade sorted eigenvalue multisets, not branch labels or eigenvector signs. Report eigenvalues in eV/(Å²amu); do not label them THz² without conversion. Negative eigenvalues mean unstable harmonic directions.

The kernel represents an ALIASED finite periodic Hessian. EAM coupling may extend to twice its6.9Åcutoff. The6a supercell does not establish an unaliased infinite-lattice kernel. Only commensurate q are covered; no arbitrary-q interpolation is graded or claimed.

## Equivalent results and physical verification

Accept any grid point attaining the minimum within a public numerical margin, including all tied symmetry-related minima. q and−q modulo conventional reciprocal integers are equivalent. Do not require the particular q or basis vector returned by one eigensolver. At degeneracies, accept any normalized vector in the lowest eigenspace. A real displacement may use either nonzero real or imaginary component of the conjugate Bloch pair, with any phase/sign/translation, provided it is nonzero and normalized to mean squared Cartesian displacement per atom1.

Trusted verification independently rebuilds D from the submitted kernel and checks the spectrum, eigen-residual and real-space Hessian Rayleigh quotient. It also checks kernel reciprocity and uniform-translation response. Negative Gamma numerical drift alone does not establish a physical instability. Do not clip negative eigenvalues in the submitted spectrum.

An energy check evaluates the supplied real pattern at both signs of small RMS amplitudes using the fixed model and compares symmetric energy curvature against its reconstructed harmonic Rayleigh quotient. It must measure a decrease beyond numerical uncertainty, not trust solver-reported energies. Independent force predictions on fixed, publicly specified displacements validate the kernel beyond one selected mode. The model calculator is not a control-plane API: it receives only finite positions in the fixed cell, no filesystem paths or executable expressions, and returns only energy/forces. It has no reference spectrum, credentials or private review data. Whether such calculator may be packaged depends on the unresolved potential licence.

Direct full1296x1296finite-supercell Hessian diagonalization has also reproduced the minimum eigenvalue without Bloch reconstruction. It is an allowed alternative. Frequency labels/process requirements must not exclude it; computational feasibility of this short route is a concrete difficulty risk, not grounds to ban the method.

## Numerical tolerances: not frozen yet

Two amplitudes currently give the same minimum-grid index and minimum-eigenvalue difference about5.64e−6eV/(Å²amu). The independent energy-versus-kernel curvature difference at0.001ÅRMS is about1.61e−5eV/Å²/atom. Random-force derivative relative errors are around1.1e−5to3.7e−5. These are measured feasibility observations, NOT rigorous error bounds or finalized grader tolerances.

Before implementation, freeze explicit finite/shape/unit checks, absolute+relative tolerances, norms and denominators, spectral ties, eigen-residual criteria, allowed amplitude/convergence treatment and negative/near-zero controls. Validate the choices against correct alternative finite-difference fits, equivalent gauges/degenerate modes, deliberately wrong mass/sign/index/phase results and empty outputs. Do not set tolerances using target-model failures or add hidden criteria. Until these margins and controls are tested this remains a draft, not a well-specified publishable task.

## Remaining acceptance work

Resolve raw/derived-data licensing, expose the exact immutable input metadata, run the shortest correct ASE/Phonopy route, compare complete candidate workflow with both fixed benchmark corpora, and obtain independent proposal feedback. Reference feasibility is established only for the current finite model; empirical difficulty and Harbor lifecycle remain untested.

## Prospective spectrum calibration v1

All216six-branch spectra were compared across the two actual finite-displacement amplitudes. Maximum absolute eigenvalue difference is9.65e−6eV/(Å²amu). A prospective absolute margin5e−5 admits that measured alternative and rejects opposite force sign, missing mass weighting, a mismatched atom permutation and the zero kernel. This margin was proposed before target-model trials. It remains provisional: it does not cover every legitimate fit or substitute for gauge/mode controls and independent approval. A consistent atom permutation is allowed; the negative control deliberately permutes forces WITHOUT updating metadata.
