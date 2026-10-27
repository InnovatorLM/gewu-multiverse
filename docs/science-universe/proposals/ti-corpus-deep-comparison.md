# Ti public contract corpus comparison

Compared the Ti public contract draft against all 138 complete instruction texts in the fixed active manifest. This is an instruction-only novelty screen: no assets, hidden solutions, verifier outputs, API tests, or ACS were used.

## Closest comparisons

`physical-sciences/materials-science/si-fracture-fbc` is the strongest domain overlap. It combines a Stillinger-Weber atomistic potential with continuum elasticity, Cauchy-Born correction, force-balanced configurations, finite-difference energy checks, and lattice-trapping folds. The Ti draft instead reconstructs a published Ti EAM finite-displacement Hessian on a finite periodic bcc supercell, diagonalizes commensurate Bloch dynamical matrices, and verifies an unstable real displacement by energy curvature. The Si task is a loaded Mode-I crack with hybrid coupling and crack-fold QoI; no input model, geometry, observable, or output contract is shared. This is high domain/method-family overlap without duplicated science.

`physical-sciences/materials-science/stacking-disorder-diffraction` recovers stacking-disorder probabilities from neutron counts using crystallite structure factors, orientation averaging, convolution, and an inverse Markov model. It shares periodic crystal bookkeeping and reciprocal-space numerics, but has no atomistic forces, Hessian, masses, Bloch modes, or instability.

`physical-sciences/materials-science/xrd-multiphase-qpa` fits phases from XRD powder profiles with scale/background/texture parameters. It shares crystallographic language only; Ti uses force derivatives and eigenvalues, not diffraction or mixture analysis.

`physical-sciences/physics/leaky-bloch-meep` validates a silicon grating coupler with mode parity, port normalization, and independent full-wave simulation. Both demand careful mode observables and numerical verification, but one is electromagnetic radiation/device design and the other static EAM lattice dynamics.

`physical-sciences/physics/inverse-waveguide-shape` infers an axial refractive-index profile from entrance/target fields through Helmholtz solves. It is an inverse numerical physics workflow with no shared material system or quantity.

`physical-sciences/materials-science/nanoindentation-property-extraction` estimates modulus, hardness, fracture, adhesion, and creep from calibrated load-depth curves. It is broad mechanics only and has no periodic lattice Hessian or Bloch spectrum.

`physical-sciences/physics/spin-glass-groundstate` optimizes discrete Ising energies on periodic 3-D lattices. Periodicity and energy scoring are superficial overlaps; it has no force/displacement response, masses, or phonons.

`physical-sciences/materials-science/roy-polymorph-cn` fits molecular dihedral angle to nitrile stretch and color. It is atomistic/spectroscopy-adjacent but has no periodic force constants or instability.

All other instructions were screened individually in the per-entry JSON files. Generic similarities (arrays, numerical tolerances, simulation, periodicity, independent recomputation) are recorded as methodological overlap only. This screen does not assert license clearance, benchmark acceptance, difficulty, or scientific correctness.
