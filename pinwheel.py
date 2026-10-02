"""The pinwheel substitution on single triangles (Conway / Radin).

The canonical triangle has vertices A0 (smallest angle, arctan 1/2),
B0 (right angle) and C0; legs 2 and 1, hypotenuse sqrt(5).  It splits into
five copies scaled by 1/sqrt(5):
  child 0: split off by the altitude from the right angle B0 (foot F)
  children 1-4: the remaining triangle A0-B0-F (similar, ratio 2/sqrt(5))
     cut at the midpoints M, N, Q; children 3 and 4 share the hypotenuse FM
     and together form a 2:1 rectangle -- an uncut subway tile.
Children 0-2 are mirror images of the parent, 3-4 are not; that mix is what
makes the tile directions k*theta accumulate without bound.

A triangle is represented by an affine map (L, t) taking the canonical
triangle to it: x -> L x + t.
"""
import numpy as np

A0, B0, C0 = np.array([0, 0.]), np.array([2, 0.]), np.array([2, 1.])
F = np.array([1.6, 0.8])   # foot of the altitude from B0
M = np.array([1, 0.])      # midpoint of A0-B0
N = np.array([0.8, 0.4])   # midpoint of A0-F
Q = np.array([1.8, 0.4])   # midpoint of B0-F

# each child as (small-angle vertex, right-angle vertex, third vertex)
CHILD = [(B0, F, C0), (A0, N, M), (M, Q, B0), (F, N, M), (M, Q, F)]


def affine_from(tri):
    """affine map taking the canonical triangle to `tri`."""
    a, b, c = tri
    L = np.column_stack([(b - a) / 2, (c - b)])   # B0-A0 = (2,0), C0-B0 = (0,1)
    return L, a


CH_AFF = [affine_from(t) for t in CHILD]


def subdivide(L, t, n, path=()):
    """Yield (L, t, path) for the 5**n triangles after n substitutions."""
    if n == 0:
        yield L, t, path
        return
    for i, (l2, t2) in enumerate(CH_AFF):
        yield from subdivide(L @ l2, L @ t2 + t, n - 1, path + (i,))


def verts(L, t):
    return [L @ A0 + t, L @ B0 + t, L @ C0 + t]
