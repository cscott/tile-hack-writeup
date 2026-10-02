#!/usr/bin/env python3
"""Check kitedomino.py against the original tile-hack/mksvg.js.

    python3 tools/verify_port.py /path/to/tile-hack [perm ...]

Runs mksvg.js (STYLES/MAXCOLORS overridden through a patched copy), flattens
the SVG with tools/extract_svg.py, and compares every piece's centroid and
colour with the Python port.  Needs node (+ `npm install` in tile-hack),
svgelements and scipy.
"""
import os, re, subprocess, sys, tempfile
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
import kitedomino as kd
from extract_svg import extract

def harness(tilehack):
    s = open(os.path.join(tilehack, 'mksvg.js')).read()
    a, b = s.index('let STYLES=['), s.index('let TALLER=')
    s = s[:a] + "let STYLES=(process.env.STYLES||'perm2560').split(',');\n" + s[b:]
    s = s.replace('for (let mx of [2,3]) {', 'for (let mx of [Number(process.env.MX||3)]) {')
    path = os.path.join(tilehack, '_mksvg_harness.js')
    open(path, 'w').write(s)
    return path

def centroid(pts):
    P = np.array(pts)
    if np.allclose(P[0], P[-1]):
        P = P[:-1]
    return P.mean(0)

def check(tilehack, js, perm, ncolors):
    env = dict(os.environ, STYLES=f'perm{perm}', MX=str(ncolors))
    svg = subprocess.run(['node', js], cwd=tilehack, env=env, capture_output=True,
                         text=True, check=True).stdout
    with tempfile.NamedTemporaryFile('w', suffix='.svg', delete=False) as f:
        f.write(svg)
    ref = extract(f.name)
    A = np.array([centroid(p['pts']) for p in ref]) / 96.0      # px -> inches
    mine = [(np.mean(pg, 0), c) for _, c, pgs in kd.tiles(perm, ncolors) for pg in pgs]
    B = np.array([m for m, _ in mine])
    d, idx = cKDTree(B).query(A)
    geom = len(A) == len(B) and d.max() < 1e-6
    cols = all(ref[i]['c'] == mine[j][1] for i, j in enumerate(idx))
    print(f'perm{perm} ({ncolors} colours): {len(A)} pieces, geometry {"OK" if geom else "DIFFERS"}, '
          f'colours {"OK" if cols else "DIFFER"}')
    return geom and cols

if __name__ == '__main__':
    tilehack = sys.argv[1]
    perms = [int(p) for p in sys.argv[2:]] or [2560, 1225, 4366555233]
    js = harness(tilehack)
    try:
        ok = all(check(tilehack, js, p, n) for p in perms for n in (2, 3))
    finally:
        os.remove(js)
    sys.exit(0 if ok else 1)
