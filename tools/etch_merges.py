#!/usr/bin/env python3
"""Which etched patterns on the prime wall can be merged, keeping the tile
colors (already on the wall) fixed?  Needs ortools.

    PYTHONPATH=. python3 tools/etch_merges.py [--quick]

A merge identifies two edge looks with the same tile color on the same pair
of sides.  It is accepted if the 21 x 27 designed tiling is still the only
tiling of that region inside a patch tall enough to hold every band up to 21
(with --quick: the 15 x 27 region of a 17 x 66 patch).  The as-built set
passes.  Result: only the vertical red etches (5 thick, 12 double thick, 8
plain) can be merged; every other merge lets a different tiling in.
"""
import sys, time, itertools
import os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import wangtiles as wt
from ortools.sat.python import cp_model

W, H = 23, 124           # patch solved: tall enough to hold the bands up to 21
# (pass --quick to screen on a 17 x 66 patch, region 15 x 27)
RW, RH = 21, 27          # region that must be forced (the designed tiling)
if '--quick' in sys.argv:
    W, H, RW, RH = 17, 66, 15, 27
SIDES = wt.SIDES
ORI = {'top': 'v', 'bottom': 'v', 'left': 'h', 'right': 'h'}

def keyed_tiles(merge):
    """merge: dict (o, label) -> canonical (o, label).  Returns list of
    unique tiles as 4-tuples of keys, and map from original tile index."""
    k = lambda o, e: merge.get((o, e), (o, e))
    out, idx = [], {}
    for t in wt.TILES:
        kt = tuple(k(ORI[s], t.edge(s)) for s in SIDES)
        if kt not in out:
            out.append(kt)
        idx[t.index] = out.index(kt)
    return out, idx

BLACK = {('v', 0), ('h', 0)}

def model(tiles):
    m = cp_model.CpModel()
    x = {(i, j, t): m.NewBoolVar('') for i in range(W) for j in range(H) for t in range(len(tiles))}
    for i in range(W):
        for j in range(H):
            m.AddExactlyOne(x[i, j, t] for t in range(len(tiles)))
            for t, kt in enumerate(tiles):
                top, right, bottom, left = kt
                if j == 0 and top not in BLACK: m.Add(x[i, j, t] == 0)
                if i == 0 and left not in BLACK: m.Add(x[i, j, t] == 0)
                if j > 0 and top in BLACK: m.Add(x[i, j, t] == 0)
                if i > 0 and left in BLACK: m.Add(x[i, j, t] == 0)
                if i + 1 < W:
                    m.AddBoolOr([x[i, j, t].Not()] + [x[i + 1, j, u] for u, ku in enumerate(tiles) if ku[3] == right])
                if j + 1 < H:
                    m.AddBoolOr([x[i, j, t].Not()] + [x[i, j + 1, u] for u, ku in enumerate(tiles) if ku[0] == bottom])
    return m, x

def solver(t=120):
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = t; s.parameters.num_workers = 8
    return s

# reference tiling from the original set
_tiles0, _ = keyed_tiles({})
m, x = model(_tiles0)
s = solver(); assert s.Solve(m) in (cp_model.OPTIMAL, cp_model.FEASIBLE)
REF = {(i, j): next(t for t in range(len(_tiles0)) if s.Value(x[i, j, t])) for i in range(W) for j in range(H)}
# reference as original tile indices
REF_ORIG = {c: wt.TILES[[k for k in range(len(wt.TILES)) if keyed_tiles({})[1][k] == t][0]].index for c, t in REF.items()}

def forced(merge, t=120):
    """True if every solution agrees with the reference in the region."""
    tiles, idx = keyed_tiles(merge)
    m, x = model(tiles)
    ref = {c: idx[REF_ORIG[c]] for c in REF}
    m.Add(sum(x[i, j, ref[i, j]] for i in range(RW) for j in range(RH)) <= RW * RH - 1)
    st = solver(t).Solve(m)
    if st == cp_model.INFEASIBLE: return True, len(tiles)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE): return False, len(tiles)
    return None, len(tiles)

GROUPS = {
    ('v', 'tan'): [1, 3, 6, 9, 14], ('v', 'grey'): [4, 2, 7, 10, 13], ('v', 'brown'): [8, 5, 12],
    ('h', 'tan'): [1, 3, 13], ('h', 'grey'): [4, 11], ('h', 'brown'): [2, 12],
}


if __name__ == '__main__':
    look = lambda o, e: (wt.COLORS[e][0] if o == 'h' else wt.COLORS[e][1])
    print('as built:', forced({}, t=600))
    for (o, col), labels in GROUPS.items():
        for a, b in itertools.combinations(labels, 2):
            ok, n = forced({(o, b): (o, a)}, t=600)
            print(f'{o} {col}: {b} {look(o, b)[1]} -> {a} {look(o, a)[1]}: '
                  f'{"FORCED" if ok else ("not forced" if ok is False else "unknown")}, {n} tiles', flush=True)
    print('red verticals 5, 12 -> 8:', forced({('v', 5): ('v', 8), ('v', 12): ('v', 8)}, t=600))
