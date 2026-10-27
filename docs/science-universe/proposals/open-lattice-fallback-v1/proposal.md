# Open fallback proposal

The candidate is a fully specified model-material lattice problem. A solver receives public paired force responses for single-coordinate perturbations on a 6x6x6 periodic cell, masses, indexing metadata, and a public energy API. It must reconstruct the finite-periodic Hessian, mass-weight it, search the 216 commensurate wavevectors, and return the lowest non-Gamma mode plus a real normalized displacement whose independently evaluated energy decreases for sufficiently small amplitude. Grading compares spectra as multisets and accepts phase, sign, translation, and degenerate-subspace equivalents.

The model and generator are CC0-compatible and contain no third-party potential. The Ti candidate remains a motivating comparison only and is not packaged.
