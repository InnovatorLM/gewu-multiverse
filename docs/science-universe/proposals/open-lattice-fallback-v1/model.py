"""Self-contained periodic two-sublattice soft-mode model (CC0).

The scalar displacement component along x has a finite-range signed coupling
chosen so its minimum is at q=(1/2,0,0), while y/z have positive springs.
The quartic term stabilizes finite displacements but does not alter the Hessian.
"""
from __future__ import annotations
import numpy as np

N = 6
MASS = np.array([1.0, 1.7])
K_ON = np.array([0.18, 0.18])
K_NEIGHBOR = 0.42
K_SOFT = -0.31
BETA = 0.08

def idx(cell, basis, axis):
    c = tuple(np.asarray(cell, dtype=int) % N)
    return ((c[0]*N + c[1])*N + c[2])*6 + basis*3 + axis

def energy(u):
    u = np.asarray(u, float).reshape(N,N,N,2,3)
    e = 0.0
    # positive onsite and nearest-neighbour relative springs
    e += 0.5*np.sum(K_ON[None,None,None,:,None] * u*u)
    for axis in range(3):
        shift = np.roll(u, -1, axis=axis)
        e += 0.5*K_NEIGHBOR*np.sum((shift-u)**2)
    # signed cross-cell x coupling creates a finite-q soft branch
    e += 0.5*K_SOFT*np.sum((np.roll(u[...,0], -1, axis=0)-u[...,1,0])**2)
    e += BETA*np.sum(u**4)
    return float(e)

def forces(u):
    u = np.asarray(u, float).reshape(N,N,N,2,3)
    h = 1e-6
    f = np.zeros_like(u)
    for c in np.ndindex((N,N,N)):
        for b in range(2):
            for a in range(3):
                d=np.zeros_like(u); d[c+(b,a)] = h
                f[c+(b,a)] = -(energy(u+d)-energy(u-d))/(2*h)
    return f.reshape(-1)

def hessian_fd(eps=1e-4):
    z=np.zeros((N,N,N,2,3)); H=np.zeros((z.size,z.size))
    for j in range(z.size):
        d=np.zeros_like(z); d.flat[j]=eps
        H[:,j]=(forces(d)-forces(-d))/(2*eps)
    return -H

if __name__ == '__main__':
    H=hessian_fd(); w=np.linalg.eigvalsh(H)
    print({'dof': H.shape[0], 'min_hessian': float(w[0]), 'max_hessian': float(w[-1]), 'energy_zero': energy(np.zeros((N,N,N,2,3)))})
