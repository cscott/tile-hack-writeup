#!/usr/bin/env python3
"""A patch of the Jeandel-Rao tiling in the poster's colors.

    PYTHONPATH=. python3 tools/jr_patch.py   -> jr_patch.pdf, jr_patch.json  (needs ortools)

jr_patch.json holds the middle of the solved patch as rows of indices into
wangtiles.JEANDEL_RAO; make_wang.py draws a piece of it in section I.

Solves a larger patch with CP-SAT and shows its middle, which is more likely
to be part of a tiling of the whole plane than the edges of a finite patch.
"""
import json
import sys
from ortools.sat.python import cp_model
from reportlab.pdfgen import canvas
import wangtiles as wt
from make_wang import (View, JR_COLOR, draw_colour_tile, draw_grid, side_triangle, fill_regions,
                       SLATE, GREY_T, PAPER)

W_SOLVE, H_SOLVE, MARGIN = 44, 34, 5
T = wt.JEANDEL_RAO
m = cp_model.CpModel()
x = {(i, j, k): m.NewBoolVar('') for i in range(W_SOLVE) for j in range(H_SOLVE) for k in range(len(T))}
for i in range(W_SOLVE):
    for j in range(H_SOLVE):
        m.AddExactlyOne(x[i, j, k] for k in range(len(T)))
        for k, t in enumerate(T):
            if i + 1 < W_SOLVE:      # right edge matches neighbour's left
                m.AddBoolOr([x[i, j, k].Not()] + [x[i + 1, j, q] for q, u in enumerate(T) if u[3] == t[1]])
            if j + 1 < H_SOLVE:      # bottom edge matches top of the tile below
                m.AddBoolOr([x[i, j, k].Not()] + [x[i, j + 1, q] for q, u in enumerate(T) if u[0] == t[2]])
s = cp_model.CpSolver()
s.parameters.max_time_in_seconds = 120
s.parameters.num_workers = 8
s.parameters.random_seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
assert s.Solve(m) in (cp_model.OPTIMAL, cp_model.FEASIBLE)
grid = [[next(T[k] for k in range(len(T)) if s.Value(x[i, j, k])) for i in range(W_SOLVE)]
        for j in range(H_SOLVE)]
patch = [row[MARGIN:W_SOLVE - MARGIN] for row in grid[MARGIN:H_SOLVE - MARGIN]]
cols, rows = len(patch[0]), len(patch)
json.dump([[T.index(t) for t in row] for row in patch], open('jr_patch.json', 'w'))

size = 15.0
pw, ph = cols * size + 60, rows * size + 80
c = canvas.Canvas('jr_patch.pdf', pagesize=(pw, ph))
c.setFillColor(PAPER); c.rect(0, 0, pw, ph, stroke=0, fill=1)
view = View(30 + size / 2, ph - 40 - size / 2, size)
regions = {}
for j, row in enumerate(patch):
    for i, t in enumerate(row):
        for side, e in zip(wt.SIDES, t):
            regions.setdefault(JR_COLOR[e], []).append(side_triangle(side, i, j))
fill_regions(c, regions, view)
draw_grid(c, view, cols, rows)
c.setStrokeColor(SLATE); c.setLineWidth(0.6); c.rect(30, 40, cols * size, rows * size)
c.setFont('Serif-Italic', 9); c.setFillColor(GREY_T)
c.drawCentredString(pw / 2, 22, f'Jeandel & Rao: a {cols} × {rows} patch, in the colors of the poster')
c.save()
print('wrote jr_patch.pdf', cols, 'x', rows)
