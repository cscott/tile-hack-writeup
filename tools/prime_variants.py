#!/usr/bin/env python3
"""Experiments with simplified versions of the PRIME2b tile set.

    PYTHONPATH=. python3 tools/prime_variants.py

V1: D4c top 9 -> 1.  V2: plus Acc (commented out in wangprime.js) and the
thin-line (composite) tiles removed.  V3: plus the triple-line label 14 removed.
V4: thin line kept, only label 14 removed.  See README, "Notes on the Wang page".
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import wangtiles as wt

class Timeout(Exception): pass

def solve(raw, w, h, limit=2e7):
    tiles = [wt.Tile(i, *t) for i, t in enumerate(raw)]
    g = wt.Grid(w, h)
    sys.setrecursionlimit(max(10000, 4 * w * h))
    order = [(x, y) for x in range(w) for y in range(h)]
    cand = {}
    for t in tiles:
        cand.setdefault((t.top, t.left), []).append(t)
    n = [0]
    def rec(k):
        if k == len(order): return True
        n[0] += 1
        if n[0] > limit: raise Timeout
        x, y = order[k]
        for t in cand.get((g.color(x, y - 1, 'bottom'), g.color(x - 1, y, 'right')), ()):
            if g.ok(x, y, t):
                g.g[x][y] = t
                if rec(k + 1): return True
                g.g[x][y] = None
        return False
    try:
        ok = rec(0)
    except Timeout:
        return None, 'timeout'
    return (g if ok else None), ('ok' if ok else 'no tiling')

def report(name, raw, sizes=((21, 27), (30, 40))):
    print('==', name)
    for w, h in sizes:
        t0 = time.time()
        g, status = solve(raw, w, h)
        if not g:
            print(f'  {w}x{h}: {status} ({time.time()-t0:.1f}s)'); continue
        ps = [x + 1 for x in range(w) if g.g[x][0].name.strip() == 'p'] + ([2] if g.g[1][0].name.strip()=='B*' else [])
        top = [g.g[x][0].name.strip() for x in range(w)]
        primes = [n for n in range(2, w + 1) if wt.is_prime(n)]
        used = {g.g[x][y].name.strip() for x in range(w) for y in range(h)}
        labels = {g.g[x][y].edge(s) for x in range(w) for y in range(h) for s in wt.SIDES}
        unused = [t[0].strip() for t in raw if t[0].strip() not in used]
        print(f'  {w}x{h}: p at {sorted(ps)}  {"OK" if sorted(ps)==primes else "primes "+str(primes)}')
        print(f'     unused tiles: {unused}; labels used: {sorted(labels)}')
    return g


def edit(raw, changes=None, drop=(), add=()):
    out = []
    for t in raw:
        n = t[0].strip()
        if n in drop: continue
        if changes and n in changes: t = (t[0],) + tuple(changes[n])
        out.append(t)
    return out + list(add)

P = wt.PRIME2B
V1 = edit(P, {'D4c': (1, 11, 14, 3)})
V2 = edit(P, {'D4c': (1, 11, 14, 3), 'd1c': (13, 3, 4, 11), 'd2c': (13, 3, 1, 3)},
          drop={'Ac', 'Ec', 'Fc', 'Gc', 'D1c', 'D2c'}, add=[('Acc', 8, 2, 1, 1)])
V3 = edit(P, {'d1p': (2, 3, 7, 11), 'd2p': (2, 3, 6, 3)},
          drop={'Ac', 'Ec', 'Fc', 'Gc', 'D1c', 'D2c', 'D4c', 'D5c', 'D6c', 'd1c', 'd2c', 'd4c'},
          add=[('Acc', 8, 2, 1, 1)])
# keep the thin composite line, but drop the triple-line marker 14 (and the
# v-13 it feeds): boxes under a composite line become ordinary boxes
V4 = edit(P, {'D4c': (9, 11, 3, 3), 'd1p': (2, 3, 7, 11), 'd2p': (2, 3, 6, 3),
              'd1c': (2, 3, 10, 11), 'd2c': (2, 3, 9, 3)},
          drop={'D5c', 'D6c', 'd4c'})


if __name__ == '__main__':
    for name, raw in [('PRIME2b as built', P), ('V1', V1), ('V2', V2), ('V3', V3), ('V4', V4)]:
        report(f'{name} ({len(raw)} tiles)', raw, sizes=((21, 27), (30, 30)))
