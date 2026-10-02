#!/usr/bin/env python3
"""Preview of the Fibonacci tile colouring: edge-type key, the 18 tiles and
the forced tiling.  PYTHONPATH=. python3 tools/fib_preview.py -> fib_preview.pdf"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import make_wang as mw
import fibtiles as ft
from make_poster import SLATE, GREY_T, INK, PAPER, W, H

c = canvas.Canvas('fib_preview.pdf', pagesize=letter)
c.setFillColor(PAPER); c.rect(0, 0, W, H, stroke=0, fill=1)
c.setFont('Serif-Bold', 13); c.setFillColor(SLATE)
c.drawString(54, H - 50, 'Fibonacci Wang tiles: proposed edge-type colouring')

# --- edge-type key
def swatch(c, look, cx, cy, s, vertical):
    """diamond straddling an edge: vertical=True for a top/bottom edge"""
    view = mw.View(cx, cy, s)
    dia = [(0, -0.5), (0.5, 0), (0, 0.5), (-0.5, 0)]
    g = mw.GLAZE_OF_BASE[look[0]]
    mw.fill_regions(c, {mw.GLAZE[g]: [dia]}, view)
    n = len(look[1]); lines = []
    for k, kind in enumerate(look[1]):
        o = (k + 1) / (n + 1) - 0.5
        w = 0.2 if kind == 'thick' else 0.1
        lines.append(((o, -0.5), (o, 0.5), w) if vertical else ((-0.5, o), (0.5, o), w))
    mw.draw_lines_by_glaze(c, {g: [dia]}, lines, view)
    mw.poly(c, [view(p) for p in dia], stroke=SLATE, lw=0.4)

y0 = H - 80
c.setFont('Serif-Bold', 9); c.setFillColor(INK)
c.drawString(54, y0, 'edge types   (left: as a left/right edge, right: as a top/bottom edge)')
for t in range(13):
    col, row = divmod(t, 7)
    x = 54 + col * 270; y = y0 - 30 - row * 34
    h, v = ft.LOOKS[t]
    c.setFont('Serif-Bold', 9); c.setFillColor(SLATE); c.drawRightString(x + 14, y - 3, str(t))
    if h: swatch(c, h, x + 34, y, 26, False)
    if v: swatch(c, v, x + 66, y, 26, True)
    c.setFont('Serif', 8.5); c.setFillColor(INK)
    c.drawString(x + 86, y - 3, ft.NOTES[t])

# --- the 18 tiles
y1 = y0 - 30 - 7 * 34 - 4
c.setFont('Serif-Bold', 9); c.drawString(54, y1, 'the 18 tiles')
ts, gap = 24, 4.5
for k, t in enumerate(ft.TILES):
    cx = 54 + ts / 2 + k * (ts + gap); cy = y1 - 12 - ts / 2
    mw.draw_wang_tile(c, t, mw.View(cx, cy, ts))
    c.setFont('Serif', 6); c.setFillColor(GREY_T)
    c.drawCentredString(cx, cy - ts / 2 - 7, t.name or '·')

# --- forced tiling, laid in 2" x 8" subway tile
rows = ft.forced(22, 14)
y2 = y1 - 12 - ts - 30
c.setFont('Serif-Bold', 9); c.setFillColor(INK)
c.drawString(54, y2, 'the forced tiling, laid in 2″ × 8″ subway tile (full tiles wherever they fit)')
s = (W - 108) / 22
view = mw.View(54 + s / 2, y2 - 18 - s / 2, s)
regions = {}
for base, run in ft.lay_tiles(rows):
    regions.setdefault(mw.GLAZE_OF_BASE[base], []).append(ft.piece_polygon(run))
# basalt border: the black triangles along the top and left, inset by half a joint
import numpy as np
for j, row in enumerate(rows):
    for i, t in enumerate(row):
        for side in ('top', 'left'):
            if t.edge(side) == 0:
                tri = np.array(mw.side_triangle(side, i, j)); m = tri.mean(0)
                regions.setdefault('basalt', []).append([tuple(m + 0.9 * (p - m)) for p in tri])
lines = [ln for j, row in enumerate(rows) for i, t in enumerate(row) for ln in mw.tile_lines(t, i, j)]
x0, y0_ = view((-0.5, -0.5)); x1, y1_ = view((21.5, 13.5))
c.saveState()
p = c.beginPath(); p.rect(x0, y1_, x1 - x0, y0_ - y1_); c.clipPath(p, stroke=0, fill=0)
c.setFillColor(mw.GROUT); c.rect(x0, y1_, x1 - x0, y0_ - y1_, stroke=0, fill=1)
mw.fill_regions(c, {mw.GLAZE[g]: polys for g, polys in regions.items()}, view)
mw.draw_lines_by_glaze(c, regions, lines, view)
c.restoreState()
for i, t in enumerate(rows[0]):
    px, _ = view((i, 0))
    isF = t.name.startswith('F')
    c.setFont('Serif-Bold' if isF else 'Serif', 7.5 if isF else 6.5)
    c.setFillColor(mw.ACCENT if isF else GREY_T)
    c.drawCentredString(px, y2 - 14, str(i + 1))
st = ft.tile_stats(ft.lay_tiles(rows))
c.setFont('Serif', 8); c.setFillColor(GREY_T)
c.drawString(54, y1_ - 14, f'{sum(st.values())} tiles: {st[4]} whole, and {st[3]} / {st[2]} / {st[1]} cut to 3 / 2 / 1 diamonds')
c.showPage(); c.save()
print('wrote fib_preview.pdf')
