#!/usr/bin/env python3
"""Extract the as-built tile layout from tile-hack/wang3-grout.svg.

    python3 tools/extract_wang_guide.py /path/to/tile-hack/wang3-grout.svg

wang3-grout.svg is the cutting guide for the downstairs wall: every 2"x8"
subway tile (silk, charcoal, auburn) and basalt edge triangle, with grout,
in millimetres.  This writes wang_wall.json with each piece as a polygon in
Wang-grid units (Wang tile (i, j) centred at (i, j), y down), and checks that
every diamond of every tile has the glaze the Wang tiling calls for.
Needs svgelements.
"""
import json, os, sys
import numpy as np
from svgelements import SVG, Path, Shape, Group

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import wangtiles as wt

PX = 96 / 25.4           # svgelements works in 96-dpi px
UNIT = 73.0              # mm per Wang tile (diamond pitch 51.6 mm * sqrt 2)
PITCH = 51.6             # mm: 2" tile (50 mm) + 1/16" joint
GLAZE = {'#fff6d5': 'silk', '#b3b3b3': 'charcoal', '#de8787': 'auburn',
         '#80b3ff': 'basalt'}
BASE_OF = {'silk': 'tan', 'charcoal': 'grey', 'auburn': 'brown'}
WALL_MM = (1473.2, 1066.8)


def main(src, out='wang_wall.json'):
    svg = SVG.parse(src, reify=True)
    pieces = []
    for el in svg.elements():
        if not isinstance(el, Shape) or isinstance(el, Group):
            continue
        if el.values.get('display') == 'none':
            continue
        fill = el.fill.hex if el.fill is not None and el.fill.value is not None else None
        if fill not in GLAZE:
            continue
        for sp in Path(el).as_subpaths():
            pts = [(float(s.end.x) / PX, float(s.end.y) / PX) for s in sp.segments() if s.end is not None]
            if len(pts) > 2 and np.allclose(pts[0], pts[-1]):
                pts = pts[:-1]
            pieces.append((GLAZE[fill], np.array(pts)))

    # grid registration: diamond centres sit on edge midpoints of the Wang grid
    cells = []
    for glaze, P in pieces:
        if glaze == 'basalt' or len(P) != 4:
            continue
        e1, e2 = P[1] - P[0], P[2] - P[1]
        if np.linalg.norm(e1) < np.linalg.norm(e2):
            P = np.roll(P, -1, axis=0)
            e1, e2 = P[1] - P[0], P[2] - P[1]
        L = np.linalg.norm(e1)
        n = int(round((L + 6.4) / PITCH))
        u = e1 / L
        cells += [(glaze, P[0] + e2 / 2 + u * (22.6 + PITCH * i)) for i in range(n)]
    C = np.array([c for _, c in cells])
    fa = np.angle(np.exp(2j * np.pi * (C[:, 0] + C[:, 1]) / UNIT).mean()) / (2 * np.pi)
    fb = np.angle(np.exp(2j * np.pi * (C[:, 0] - C[:, 1]) / UNIT).mean()) / (2 * np.pi)
    s_, d_ = (fa - 0.5) * UNIT, (fb - 0.5) * UNIT
    ox0, oy0 = (s_ + d_) / 2, (s_ - d_) / 2

    g = wt.bathroom_grid()

    def base_at(u, v):
        if abs(u - round(u)) > 0.3:
            cands = [('right', int(np.floor(u)), int(round(v))), ('left', int(np.floor(u)) + 1, int(round(v)))]
        else:
            cands = [('bottom', int(round(u)), int(np.floor(v))), ('top', int(round(u)), int(np.floor(v)) + 1)]
        for side, x, y in cands:
            if 0 <= x < g.w and 0 <= y < g.h:
                return g.g[x][y].look(side)[0]
        return None

    best = None
    for di in range(-3, 4):
        for dj in range(-3, 4):
            ox, oy = ox0 + UNIT * di, oy0 + UNIT * dj
            res = [base_at((c[0] - ox) / UNIT, (c[1] - oy) / UNIT) for _, c in cells]
            ok = sum(r == BASE_OF[gl] for r, (gl, _) in zip(res, cells))
            bad = sum(r is not None and r != BASE_OF[gl] for r, (gl, _) in zip(res, cells))
            if best is None or ok - bad > best[0]:
                best = (ok - bad, ok, bad, ox, oy)
    _, ok, bad, ox, oy = best
    print(f'{len(pieces)} pieces; grid origin ({ox:.2f}, {oy:.2f}) mm; '
          f'{ok} diamonds match the Wang tiling, {bad} do not')

    def to_units(P):
        return [[(x - ox) / UNIT, (y - oy) / UNIT] for x, y in P]
    data = {
        'source': os.path.basename(src),
        'unit_mm': UNIT,
        'wall_units': [(0 - ox) / UNIT, (0 - oy) / UNIT,
                       (WALL_MM[0] - ox) / UNIT, (WALL_MM[1] - oy) / UNIT],
        'pieces': [{'glaze': gl, 'poly': [[round(a, 5), round(b, 5)] for a, b in to_units(P)]}
                   for gl, P in pieces],
    }
    json.dump(data, open(out, 'w'))
    print('wrote', out)
    return bad == 0


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[1]) else 1)
