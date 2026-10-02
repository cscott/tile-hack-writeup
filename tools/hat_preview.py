#!/usr/bin/env python3
"""Quick look at an unbuilt 'einstein' (hat) wall in the upstairs colours.

    PYTHONPATH=. python3 tools/hat_preview.py   -> hat_preview.pdf
"""
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import FILL_EVEN_ODD
import hattiles as ht
from make_poster import (W, H, X0, X1, CW, SLATE, INK, GREY_T, PAPER, TILE_GRAY, TILE_BLUE,
                         para, small, poly)

GROUT = HexColor('#E3E0DA')       # light, as on the pinwheel border
JOINT = 0.06                      # grout width, in units of the short leg (~3/16" at 3")

hats = ht.hat_tiling(3)


def hat_pieces(T):
    return [ht.inset_triangle([ht.tpt(T, p) for p in tri], JOINT / 2) for tri in ht.HAT_TRIANGLES]


def draw_patch(c, x0, y0, w, h, scale, centre, outlines=False):
    cx, cy = centre

    def to(p):
        return (x0 + w / 2 + scale * (p[0] - cx), y0 + h / 2 + scale * (p[1] - cy))
    c.saveState()
    p = c.beginPath(); p.rect(x0, y0, w, h); c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(GROUT); c.rect(x0, y0, w, h, stroke=0, fill=1)
    reach = (math.hypot(w, h) / 2) / scale + 6
    groups = {TILE_BLUE: [], TILE_GRAY: []}
    shown = []
    for T, label in hats:
        if math.hypot(T[2] - cx, T[5] - cy) > reach:
            continue
        shown.append((T, label))
        groups[TILE_BLUE if ht.is_reflected(T) else TILE_GRAY] += hat_pieces(T)
    for col, polys in groups.items():
        c.setFillColor(col)
        path = c.beginPath()
        for pg in polys:
            q = [to(v) for v in pg]
            path.moveTo(*q[0])
            for v in q[1:]:
                path.lineTo(*v)
            path.close()
        c.drawPath(path, stroke=0, fill=1, fillMode=FILL_EVEN_ODD)
    if outlines:
        c.setStrokeColor(SLATE); c.setLineWidth(0.7); c.setLineJoin(1)
        for T, label in shown:
            q = [to(ht.tpt(T, v)) for v in ht.HAT]
            path = c.beginPath(); path.moveTo(*q[0])
            for v in q[1:]:
                path.lineTo(*v)
            path.close()
            c.drawPath(path, stroke=1, fill=0)
    c.restoreState()
    c.setStrokeColor(SLATE); c.setLineWidth(0.6); c.rect(x0, y0, w, h, stroke=1, fill=0)
    return shown


c = canvas.Canvas('hat_preview.pdf', pagesize=letter)
c.setFillColor(PAPER); c.rect(0, 0, W, H, stroke=0, fill=1)
c.setFont('Serif-Bold', 13); c.setFillColor(SLATE)
c.drawString(X0, H - 60, 'An “einstein” wall: hats from diagonally cut tiles')
centre = (sum(T[2] for T, _ in hats) / len(hats), sum(T[5] for T, _ in hats) / len(hats))
fig_h = 330
draw_patch(c, X0, H - 80 - fig_h, CW, fig_h, 15.5, centre)
c.setFont('Serif-Italic', 7.6); c.setFillColor(GREY_T)
c.drawCentredString(X0 + CW / 2, H - 80 - fig_h - 11,
                    'as laid: reflected hats blue-grey, all others light; uniform grout between every piece')

y2 = H - 80 - fig_h - 30
w2 = (CW - 14) / 2
draw_patch(c, X0, y2 - 190, w2, 190, 13, centre, outlines=True)
c.setFont('Serif-Italic', 7.6); c.setFillColor(GREY_T)
c.drawCentredString(X0 + w2 / 2, y2 - 201, 'the same, with the hats outlined')

# why a 1:2 tile cannot make these kites
x3 = X0 + w2 + 14
ox, oy, s = x3 + 95, y2 - 72, 26
for k in range(6):
    a = math.radians(k * 2 * math.degrees(math.atan(0.5)))   # six 1:2 kites, 53.13 deg each
    half = math.atan(0.5)
    long_ = 2.0
    pts = [(0, 0)]
    for d, r in ((-half, long_), (0, math.hypot(1, 2)), (half, long_)):
        pts.append((r * math.cos(a + half + d), r * math.sin(a + half + d)))
    poly(c, [(ox + s * x, oy + s * y) for x, y in pts], fill=TILE_GRAY, stroke=SLATE, lw=0.6)
gap0 = 6 * 2 * math.atan(0.5)
for ang in (gap0, 2 * math.pi):
    c.setStrokeColor(HexColor('#A5312F')); c.setLineWidth(0.8)
    c.line(ox, oy, ox + 2.4 * s * math.cos(ang), oy + 2.4 * s * math.sin(ang))
c.setFont('Serif', 7.5); c.setFillColor(HexColor('#A5312F'))
mid = (gap0 + 2 * math.pi) / 2
c.drawCentredString(ox + 1.7 * s * math.cos(mid), oy + 1.7 * s * math.sin(mid) - 3,
                    '%.1f° short' % math.degrees(2 * math.pi - gap0))
para(c, 'Six kites made from 1 : 2 triangles meet at only 318.8° (6 × 53.13°), not 360°. '
        'A hat kite needs triangles with legs 1 : √3, angles 30° and 60°.',
     x3, y2 - 140, w2, small)

c.showPage()

# ---------------------------------------------------------------- page 2: rhombus tile
c.setFillColor(PAPER); c.rect(0, 0, W, H, stroke=0, fill=1)
c.setFont('Serif-Bold', 13); c.setFillColor(SLATE)
c.drawString(X0, H - 60, 'The same wall in 60° rhombus tile')
near = [h for h in hats if math.hypot(h[0][2] - centre[0], h[0][5] - centre[1]) < 42]
LAYOUT = 'hat_layout.json'      # cached solution of ht.optimal_layout(near); delete to re-solve


def load_layout():
    import json, os, sys
    if os.path.exists(LAYOUT) and '--resolve' not in sys.argv:
        return [(c, k, [tuple(p) for p in pg], h) for c, k, pg, h in json.load(open(LAYOUT))]
    print('solving for the fewest cuts (a few minutes; needs ortools)...')
    pcs = ht.optimal_layout(near, verbose=True)
    json.dump([(c, k, [(round(x, 5), round(y, 5)) for x, y in pg], h) for c, k, pg, h in pcs],
              open(LAYOUT, 'w'), separators=(',', ':'))
    return pcs


pieces = load_layout()
COL = {'blue': TILE_BLUE, 'light': TILE_GRAY}
TINT = {'blue': HexColor('#8A9CB0'), 'light': HexColor('#BDBBB8')}   # offset rhombi, small panel


def draw_rhombi(c, x0, y0, w, h, scale, outlines=False):
    def to(p):
        return (x0 + w / 2 + scale * (p[0] - centre[0]), y0 + h / 2 + scale * (p[1] - centre[1]))
    c.saveState()
    p = c.beginPath(); p.rect(x0, y0, w, h); c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(GROUT); c.rect(x0, y0, w, h, stroke=0, fill=1)
    groups = [(COL[col], col, False) for col in ('light', 'blue')]
    if outlines:
        groups += [(TINT[col], col, True) for col in ('light', 'blue')]
    for fill, col, offset in groups:
        c.setFillColor(fill)
        path = c.beginPath()
        for pc in pieces:
            if pc[0] != col or (outlines and (pc[1] == 'offset rhombus') != offset):
                continue
            q = [to(v) for v in ht.inset_polygon(pc[2], JOINT / 2)]
            path.moveTo(*q[0])
            for v in q[1:]:
                path.lineTo(*v)
            path.close()
        c.drawPath(path, stroke=0, fill=1, fillMode=FILL_EVEN_ODD)
    if outlines:
        c.setStrokeColor(SLATE); c.setLineWidth(0.7); c.setLineJoin(1)
        for T, label in near:
            q = [to(ht.tpt(T, v)) for v in ht.HAT]
            path = c.beginPath(); path.moveTo(*q[0])
            for v in q[1:]:
                path.lineTo(*v)
            path.close()
            c.drawPath(path, stroke=1, fill=0)
    c.restoreState()
    c.setStrokeColor(SLATE); c.setLineWidth(0.6); c.rect(x0, y0, w, h, stroke=1, fill=0)


draw_rhombi(c, X0, H - 80 - fig_h, CW, fig_h, 15.5)
c.setFont('Serif-Italic', 7.6); c.setFillColor(GREY_T)
c.drawCentredString(X0 + CW / 2, H - 80 - fig_h - 11,
                    'laid for the fewest cuts: whole rhombi almost everywhere, cut pieces only around the blue hats')
draw_rhombi(c, X0, y2 - 190, w2, 190, 13, outlines=True)
c.drawCentredString(X0 + w2 / 2, y2 - 201, 'hats outlined; rhombi laid across a kite axis shaded')

# the five kinds of piece
kinds = [('rhombus', 'whole rhombus', 'uncut, on the tumbling-blocks grid'),
         ('offset rhombus', 'offset rhombus', 'uncut, across a kite axis (shaded)'),
         ('equilateral', 'equilateral half', 'short diagonal: ½ cut each'),
         ('obtuse', 'obtuse half', 'long diagonal: avoided, never needed'),
         ('right', 'right triangle', 'both diagonals: ¾ cut each')]
proto = {}
for pc in pieces:
    proto.setdefault(pc[1], pc[2])
proto.setdefault('obtuse', [(0, 0), (2 * ht.R3, 0), (ht.R3, 1)])
ky = y2 - 18
for kind, name, how in kinds:
    pts = proto[kind]
    mx = sum(p[0] for p in pts) / len(pts); my = sum(p[1] for p in pts) / len(pts)
    sc = 9
    poly(c, [(x3 + 26 + sc * (p[0] - mx), ky - 12 + sc * (p[1] - my)) for p in pts],
         fill=TILE_GRAY, stroke=SLATE, lw=0.5)
    c.setFont('Serif-Bold', 8); c.setFillColor(INK); c.drawString(x3 + 58, ky - 9, name)
    c.setFont('Serif', 7.5); c.setFillColor(GREY_T); c.drawString(x3 + 58, ky - 19, how)
    ky -= 33
R = 30
inside = lambda pc: math.hypot(sum(q[0] for q in pc[2]) / len(pc[2]) - centre[0],
                               sum(q[1] for q in pc[2]) / len(pc[2]) - centre[1]) < R
nh = sum(1 for T, _ in hats if math.hypot(T[2] - centre[0], T[5] - centre[1]) < R)
new = ht.cut_stats([pc for pc in pieces if inside(pc)])
old = ht.cut_stats([pc for pc in ht.rhombus_layout(near) if inside(pc)])
tot = lambda st: sum(v['cuts'] for v in st.values())
para(c, f'Within {R} units of the centre ({nh} hats): {tot(new):,.0f} cuts, against '
        f'{tot(old):,.0f} using only the tumbling-blocks grid and {8 * nh:,} cutting every '
        f'half-kite from 1 : √3 rectangles. Each blue hat is two whole rhombi, one equilateral '
        f'half and six right triangles: 5 cuts. The light field takes about six more right '
        f'triangles per blue hat. The shaded chains of offset rhombi link the blue hats in '
        f'pairs, so the light tile closes up around each hat without further cuts. Cuts '
        f'count ½ per half and ¾ per right triangle.',
     x3, ky - 4, w2, small)
c.showPage(); c.save()
print('wrote hat_preview.pdf;', sum(1 for T, l in hats), 'hats generated;', new, old)
