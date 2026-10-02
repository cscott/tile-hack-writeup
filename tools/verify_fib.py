#!/usr/bin/env python3
"""Check the corrected Fibonacci tiles: with black top and left edges, every
tiling of a W x H patch has the same top row, 1, 2, 3, 5, 8, 13, 21, ...
Also checks the tiles *as drawn* (edges that look alike merged) and the
Lucas-number variant mentioned on the poster.

    PYTHONPATH=. python3 tools/verify_fib.py
"""
import sys
import fibtiles as ft
import wangtiles as wt
sys.setrecursionlimit(100000)


def tilings(tiles, W, H, cap=5000):
    """Count tilings of a W x H patch (black top/left, open bottom/right) and
    collect the F columns of each one's top row."""
    cand = {}
    for t in tiles:
        cand.setdefault((t[0], t[3]), []).append(t)
    g, n, tops = {}, [0], set()
    order = [(x, y) for x in range(W) for y in range(H)]

    def col(x, y, i):
        if x < 0 or y < 0:
            return 0
        t = g.get((x, y))
        return None if t is None else t[i]

    def rec(k):
        if n[0] >= cap:
            return
        if k == len(order):
            n[0] += 1
            tops.add(tuple(x + 1 for x in range(W) if g[(x, 0)][4].startswith('F')))
            return
        x, y = order[k]
        for t in cand.get((col(x, y - 1, 2), col(x - 1, y, 1)), ()):
            g[(x, y)] = t
            rec(k + 1)
            del g[(x, y)]
    rec(0)
    return n[0], tops


raw = [(t.top, t.right, t.bottom, t.left, t.name) for t in ft.TILES]
ok = True
for name, ts in (('18 tiles', raw), ('as drawn', ft.visual_set())):
    n, tops = tilings(ts, 34, 24)
    good = n == 1 and tops == {(1, 2, 3, 5, 8, 13, 21, 34)}
    print(f'{name:9s} 34 x 24: {n} tiling(s), top row {sorted(tops)}', 'OK' if good else 'FAIL')
    ok &= good
extra = [(0, 2, 1, 2, ''), (1, 5, 1, 5, '')]
pins = {(0, 0): raw[0], (1, 0): extra[0], (2, 0): raw[1]}
rows = wt.solve(raw + extra, 32, 20, pins)
lucas = [x + 1 for x, t in enumerate(rows[0]) if t[4].startswith('F')]
print('F″ at column 3 ->', lucas, 'OK' if lucas == [1, 3, 4, 7, 11, 18, 29] else 'FAIL')
ok &= lucas == [1, 3, 4, 7, 11, 18, 29]
sys.exit(0 if ok else 1)
