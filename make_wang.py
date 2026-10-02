#!/usr/bin/env python3
"""One-page framed print about the Wang-tile prime sieve in the downstairs
bathroom.

    python3 make_wang.py              -> wang-tiling.pdf

Shares fonts, palette and layout helpers with make_poster.py.  The tile set
and solver are in wangtiles.py; the as-built layout of the wall (which tile
went where, extracted from tile-hack/wang3-grout.svg) is wang_wall.json.
"""
import json
import os
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen.canvas import FILL_EVEN_ODD, FILL_NON_ZERO

import wangtiles as wt
from make_poster import (W, H, X0, X1, CW, OUT, IN, SLATE, INK, GREY_T, PAPER,
                         TILE_BLUE, poly, para, heading, title_block, footer,
                         body, small, foot)

HERE = os.path.dirname(os.path.abspath(__file__))
# A few Chinese characters, from Noto Serif CJK TC (see tools/make_cjk_subset.py)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('CJK', os.path.join(HERE, 'fonts', 'NotoSerifTC-subset.ttf')))
SIGNATURE = 'C. Scott Ananian · February 2019'

# ------------------------------------------------------------------ palette
# tile colors on the wall, by eye from photographs: silk is glazed ceramic,
# basalt a dark natural stone, charcoal and auburn colored glass
GLAZE = {
    'silk': HexColor('#EDEAE4'),
    'charcoal': HexColor('#5A5F66'),
    'auburn': HexColor('#A5312F'),
    'basalt': HexColor('#2A2C2F'),
}
GROUT = HexColor('#A39D95')
BORDER_GROUT = HexColor('#CDC8C1')   # lighter, so joints read apart from the etching
# how an etched (frosted) line reads on each glaze
ETCH = {
    'silk': HexColor('#BDB7AE'),
    'charcoal': Color(1, 1, 1, alpha=0.42),
    'auburn': Color(1, 1, 1, alpha=0.45),
    'basalt': Color(1, 1, 1, alpha=0.35),
}
GLAZE_OF_BASE = {base: glaze for base, glaze in wt.BASE_TILE.items()}
ACCENT = GLAZE['auburn']

# ------------------------------------------------------------------ geometry
# Wang tile (i, j) is centred at (i, j) in "units", y down.  An edge
# triangle in local coordinates for the bottom edge, and the maps that turn
# it into the other three (the same transforms as wangprime.js).
TRI = [(0, 0), (0.5, 0.5), (-0.5, 0.5)]
SIDE_MAP = {
    'bottom': lambda x, y: (x, y),
    'top': lambda x, y: (x, -y),
    'right': lambda x, y: (y, -x),
    'left': lambda x, y: (-y, -x),
}


def side_triangle(side, i=0, j=0):
    f = SIDE_MAP[side]
    return [(i + f(x, y)[0], j + f(x, y)[1]) for x, y in TRI]


def side_lines(side, look, i=0, j=0):
    """Etched lines for one edge as wangprime.js draws them, untrimmed:
    list of ((x0, y0), (x1, y1), width)."""
    base, lines = look
    n = len(lines)
    f = SIDE_MAP[side]
    out = []
    for k, kind in enumerate(lines):
        x = (k + 1) / (n + 1) - 0.5
        a, b = f(x, 0.0), f(x, 0.5)
        out.append(((i + a[0], j + a[1]), (i + b[0], j + b[1]), 0.2 if kind == 'thick' else 0.1))
    return out


def _side_offsets(tile, side):
    """[(offset, width)] for the lines on one edge.  Lines from the top and
    bottom are vertical at x = offset; from the left and right, horizontal
    at y = offset (the mapping used in SIDE_MAP)."""
    base, lines = tile.look(side)
    n = len(lines)
    out = []
    for k, kind in enumerate(lines):
        x = (k + 1) / (n + 1) - 0.5
        off = x if side in ('top', 'bottom') else -x
        out.append((round(off, 9), 0.2 if kind == 'thick' else 0.1))
    return sorted(out)


START = {'top': -0.5, 'bottom': 0.5, 'left': -0.5, 'right': 0.5}
VERT = ('top', 'bottom')


def tile_lines(tile, i=0, j=0):
    """Etched lines for a whole tile, joined neatly where they meet.

    Each edge's lines run from the edge towards the centre.  Where one pair
    of opposite edges carries the same lines (they pass straight through)
    and the lines from a third edge do not, those stop at the nearest
    through line, like a T, instead of leaving a stub in the middle.  Where
    nothing passes through, lines from two adjacent edges with the same
    count turn the corner as nested box-drawing corners (as in a double
    line, like the character U+2554); any other lines stop at the first
    line they meet."""
    L = {s: _side_offsets(tile, s) for s in wt.SIDES}
    end = {s: [0.0] * len(L[s]) for s in wt.SIDES}
    offs = lambda s: [o for o, w in L[s]]
    v_thru = offs('top') == offs('bottom')
    h_thru = offs('left') == offs('right')

    def travel(s):           # direction a line from side s moves in
        return 1.0 if START[s] < 0 else -1.0

    if h_thru and not v_thru and L['left']:
        ys = offs('left')
        end['top'] = [min(ys)] * len(L['top'])
        end['bottom'] = [max(ys)] * len(L['bottom'])
    elif v_thru and not h_thru and L['top']:
        xs = offs('top')
        end['left'] = [min(xs)] * len(L['left'])
        end['right'] = [max(xs)] * len(L['right'])
    elif not v_thru and not h_thru:
        done = set()
        for vs in VERT:
            for hs in ('left', 'right'):
                if vs in done or hs in done or not L[vs] or len(L[vs]) != len(L[hs]):
                    continue
                # outermost with outermost: the vertical line farthest from the
                # horizontal lines' edge pairs with the horizontal line farthest
                # from the vertical lines' edge
                vi = sorted(range(len(L[vs])), key=lambda k: -L[vs][k][0] * travel(hs))
                hi = sorted(range(len(L[hs])), key=lambda k: -L[hs][k][0] * travel(vs))
                for a, b in zip(vi, hi):
                    (xo, wv), (yo, wh) = L[vs][a], L[hs][b]
                    end[vs][a] = yo + travel(vs) * wh / 2
                    end[hs][b] = xo + travel(hs) * wv / 2
                done |= {vs, hs}
        # anything left stops at the first line it meets
        for s in wt.SIDES:
            if s in done or not L[s]:
                continue
            others = [p for p in wt.SIDES if p in done and (p in VERT) != (s in VERT)]
            for k, (o, w) in enumerate(L[s]):
                hits = []
                for p in others:
                    for (po, pw), pe in zip(L[p], end[p]):
                        lo, hi_ = sorted((START[p], pe))
                        if lo - 1e-9 <= o <= hi_ + 1e-9:
                            hits.append(po)
                ahead = [h for h in hits if (h - START[s]) * travel(s) > 0]
                if ahead:
                    end[s][k] = min(ahead, key=lambda h: abs(h - START[s]))
    # lines that would just stop in the middle, opposite a black (border)
    # edge, are carried on into the black triangle and clipped by it, so they
    # seem to come out of the border (tiles *, p and D1*)
    opp = {'top': 'bottom', 'bottom': 'top', 'left': 'right', 'right': 'left'}
    skip = {s: () for s in wt.SIDES}
    for s in wt.SIDES:
        perp = ('left', 'right') if s in VERT else VERT
        if (L[s] and all(e == 0.0 for e in end[s]) and tile.edge(opp[s]) == 0
                and not any(L[p] for p in perp)):
            end[s] = [START[opp[s]]] * len(L[s])
            skip[s] = ('basalt',)
    out = []
    for s in wt.SIDES:
        for (o, w), e in zip(L[s], end[s]):
            if s in VERT:
                out.append(((i + o, j + START[s]), (i + o, j + e), w, skip[s]))
            else:
                out.append(((i + START[s], j + o), (i + e, j + o), w, skip[s]))
    return out


class View:
    """Maps Wang units (y down) to page points."""

    def __init__(self, x, y, scale, u0=0.0, v0=0.0):
        self.x, self.y, self.s, self.u0, self.v0 = x, y, scale, u0, v0

    def __call__(self, p):
        return (self.x + self.s * (p[0] - self.u0), self.y - self.s * (p[1] - self.v0))


def path_of(c, polys, view):
    p = c.beginPath()
    for pg in polys:
        q = [view(pt) for pt in pg]
        p.moveTo(*q[0])
        for r in q[1:]:
            p.lineTo(*r)
        p.close()
    return p


def draw_lines_by_glaze(c, regions, lines, view):
    """Draw etched lines in the right tone for whatever glaze is underneath.
    regions: {glaze: [polygon, ...]}; lines: [(p0, p1, width_units)]."""
    for glaze, polys in regions.items():
        if not polys:
            continue
        c.saveState()
        c.clipPath(path_of(c, polys, view), stroke=0, fill=0, fillMode=FILL_EVEN_ODD)
        mine = [ln for ln in lines if len(ln) < 4 or glaze not in ln[3]]
        c.setFillColor(ETCH[glaze])
        c.drawPath(path_of(c, _line_rects(mine), view), stroke=0, fill=1, fillMode=FILL_NON_ZERO)
        c.restoreState()


def _line_rects(lines):
    """Each line as a rectangle, all wound the same way, so that filling them
    as one path (non-zero rule) paints every overlap exactly once."""
    rects = []
    for (x0, y0), (x1, y1), w, *_ in lines:
        dx, dy = x1 - x0, y1 - y0
        n = (dx * dx + dy * dy) ** 0.5
        if n < 1e-9:
            continue
        px, py = -dy / n * w / 2, dx / n * w / 2
        r = [(x0 + px, y0 + py), (x1 + px, y1 + py), (x1 - px, y1 - py), (x0 - px, y0 - py)]
        area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(r, r[1:] + r[:1]))
        rects.append(r if area > 0 else r[::-1])
    return rects


GRID_DOT = Color(0.42, 0.44, 0.47, alpha=0.55)


def draw_grid(c, view, cols, rows, i0=0, j0=0):
    """The Wang squares as a light dotted grid (cells i0..i0+cols-1, j0..)."""
    c.saveState()
    c.setStrokeColor(GRID_DOT)
    c.setLineWidth(0.5)
    c.setLineCap(1)
    c.setDash([0.01, 1.7])
    for k in range(cols + 1):
        a, b = view((i0 - 0.5 + k, j0 - 0.5)), view((i0 - 0.5 + k, j0 - 0.5 + rows))
        c.line(a[0], a[1], b[0], b[1])
    for k in range(rows + 1):
        a, b = view((i0 - 0.5, j0 - 0.5 + k)), view((i0 - 0.5 + cols, j0 - 0.5 + k))
        c.line(a[0], a[1], b[0], b[1])
    c.restoreState()


def fill_regions(c, regions, view):
    """Fill {colour: [polygon]} with one path per colour, so that triangles of
    the same colour merge without a hairline seam between them."""
    for colour, polys in regions.items():
        c.setFillColor(colour)
        c.drawPath(path_of(c, polys, view), stroke=0, fill=1, fillMode=FILL_EVEN_ODD)


def tile_glaze(tile, side):
    return GLAZE_OF_BASE[tile.look(side)[0]]


def draw_wang_tile(c, tile, view, i=0, j=0, outline=True):
    """One Wang tile as four glazed triangles with its etched lines."""
    regions = {}
    for side in wt.SIDES:
        regions.setdefault(tile_glaze(tile, side), []).append(side_triangle(side, i, j))
    fill_regions(c, {GLAZE[g]: polys for g, polys in regions.items()}, view)
    draw_lines_by_glaze(c, regions, tile_lines(tile, i, j), view)
    if outline:
        sq = [(i - .5, j - .5), (i + .5, j - .5), (i + .5, j + .5), (i - .5, j + .5)]
        poly(c, [view(p) for p in sq], stroke=SLATE, lw=0.5)


# ------------------------------------------------------------------ the wall
WALL = json.load(open(os.path.join(HERE, 'wang_wall.json')))
GRID = wt.bathroom_grid()


def wall_pieces(bounds=None):
    """As-built pieces {glaze: [polygon]} whose centre lies inside the Wang grid."""
    out = {}
    for p in WALL['pieces']:
        P = np.array(p['poly'])
        cx, cy = P.mean(0)
        if not (-0.6 < cx < GRID.w - 0.4 and -0.6 < cy < GRID.h - 0.4):
            continue
        out.setdefault(p['glaze'], []).append([tuple(q) for q in P])
    return out


def grid_lines():
    lines = []
    for i in range(GRID.w):
        for j in range(GRID.h):
            lines += tile_lines(GRID.g[i][j], i, j)
    return lines


def _inside(pt, polygon):
    x, y = pt
    inside = False
    n = len(polygon)
    for k in range(n):
        (x1, y1), (x2, y2) = polygon[k], polygon[(k + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def missing_triangles(pieces):
    """Edge triangles of the Wang grid that no as-built piece covers (the
    cutting guide stops short at the bottom and right of the design).  They
    are drawn inset, so the border still shows the whole tiling."""
    allp = [pg for polys in pieces.values() for pg in polys]
    cent = np.array([np.mean(pg, 0) for pg in allp])
    out = {}
    for i in range(GRID.w):
        for j in range(GRID.h):
            t = GRID.g[i][j]
            for side in wt.SIDES:
                tri = side_triangle(side, i, j)
                m = np.mean(tri, 0)
                q = (m + np.mean(tri[1:], 0)) / 2          # towards the edge
                near = np.where(np.abs(cent - q).sum(1) < 3)[0]
                if any(_inside(q, allp[k]) for k in near):
                    continue
                inset = [tuple(m + 0.82 * (np.array(p) - m)) for p in tri]
                out.setdefault(tile_glaze(t, side), []).append(inset)
    return out


PIECES = wall_pieces()
EXTRA = missing_triangles(PIECES)
LINES = grid_lines()


def _triangle_regions():
    out = {}
    for i in range(GRID.w):
        for j in range(GRID.h):
            t = GRID.g[i][j]
            for side in wt.SIDES:
                out.setdefault(tile_glaze(t, side), []).append(side_triangle(side, i, j))
    return out


TRIANGLES = _triangle_regions()


def draw_wall(c, view, clip, built=True, grout=None):
    """Draw the wall clipped to a page rect.  built=True: the tiles as laid,
    with grout (from the cutting guide); built=False: the bare Wang tiling,
    four glazed triangles per square, no grout."""
    x0, y0, x1, y1 = clip
    c.saveState()
    p = c.beginPath()
    p.rect(x0, y0, x1 - x0, y1 - y0)
    c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(grout or GROUT)
    c.rect(x0, y0, x1 - x0, y1 - y0, stroke=0, fill=1)
    if built:
        regions = {g: PIECES.get(g, []) + EXTRA.get(g, []) for g in GLAZE}
    else:
        regions = TRIANGLES
    for glaze, polys in regions.items():
        if polys:
            c.setFillColor(GLAZE[glaze])
            c.drawPath(path_of(c, polys, view), stroke=0, fill=1, fillMode=FILL_EVEN_ODD)
    draw_lines_by_glaze(c, regions, LINES, view)
    c.restoreState()


def draw_frame(c):
    """Border: the whole designed 21 x 27 tiling (the wall shows the top 15 rows)."""
    s = (H - 2 * OUT) / GRID.h
    view = View(OUT, H - OUT, s, -0.5, -0.5)
    c.saveState()
    p = c.beginPath()
    p.rect(OUT, OUT, W - 2 * OUT, H - 2 * OUT)
    p.rect(IN, IN, W - 2 * IN, H - 2 * IN)
    c.clipPath(p, stroke=0, fill=0, fillMode=FILL_EVEN_ODD)
    draw_wall(c, view, (OUT, OUT, W - OUT, H - OUT), grout=BORDER_GROUT)
    c.restoreState()
    c.setStrokeColor(SLATE)
    c.setLineWidth(1.2)
    c.rect(IN, IN, W - 2 * IN, H - 2 * IN, stroke=1, fill=0)
    c.setLineWidth(0.5)
    c.rect(IN + 4, IN + 4, W - 2 * IN - 8, H - 2 * IN - 8, stroke=1, fill=0)
    c.setStrokeColor(GROUT)
    c.setLineWidth(0.6)
    c.rect(OUT, OUT, W - 2 * OUT, H - 2 * OUT, stroke=1, fill=0)


# ------------------------------------------------------------------ small figures
JR_COLOR = {'R': GLAZE['auburn'], 'G': TILE_BLUE, 'B': GLAZE['charcoal'], 'W': GLAZE['silk']}


def draw_colour_tile(c, edges, view, i, j, cmap, outline=SLATE):
    """A tile drawn as four triangles coloured cmap[edge]; edges = (t, r, b, l)."""
    regions = {}
    for side, e in zip(wt.SIDES, edges):
        regions.setdefault(cmap[e], []).append(side_triangle(side, i, j))
    fill_regions(c, regions, view)
    if outline:
        sq = [(i - .5, j - .5), (i + .5, j - .5), (i + .5, j + .5), (i - .5, j + .5)]
        poly(c, [view(p) for p in sq], stroke=outline, lw=0.5)


def draw_jeandel_rao(c, x, y, size, gap):
    """The 11 tiles in two rows (6 + 5), top-left at (x, y)."""
    for k, t in enumerate(wt.JEANDEL_RAO):
        r, q = divmod(k, 6)
        off = 0 if r == 0 else (size + gap) / 2
        view = View(x + off + q * (size + gap) + size / 2, y - r * (size + gap) - size / 2, size)
        draw_colour_tile(c, t, view, 0, 0, JR_COLOR)


SUM_COLOR = {0: GLAZE['basalt'], 1: GLAZE['silk'], 2: TILE_BLUE,
             3: GLAZE['charcoal'], 4: GLAZE['charcoal'], 5: GLAZE['charcoal'],
             6: GLAZE['charcoal'], 7: GLAZE['auburn'], 8: GLAZE['auburn']}


def draw_sum(c, x, y, size, a1=4, a2=7):
    rows, s_cols = wt.sum_example(a1, a2)
    view = View(x + size / 2, y - size / 2, size)
    for j, row in enumerate(rows):
        for i, t in enumerate(row):
            draw_colour_tile(c, t[:4], view, i, j, SUM_COLOR, outline=None)
    draw_grid(c, view, len(rows[0]), len(rows))
    # labels
    for i, t in enumerate(rows[0]):
        px, py = view((i, 0))
        if t[4]:
            c.setFillColor(SLATE)
            c.setFont('Serif-Bold', 8)
            c.drawCentredString(px, y + 11, '★' if t[4] == '*' else t[4])
        c.setFillColor(GREY_T)
        c.setFont('Serif', 6.2)
        c.drawCentredString(px, y + 3, str(i + 1))
    return rows, s_cols


# ------------------------------------------------------------------ the page
def ornament(c, cx, cy):
    t = wt.TILES[[x.name for x in wt.TILES].index('p')]     # the tile that says "prime"
    draw_wang_tile(c, t, View(cx, cy, 15), 0, 0)


def build(path='wang-tiling.pdf', gap=0.0):
    """Draw the page; `gap` is extra space above each section heading.
    Returns the y of the bottom of the footnote."""
    c = canvas.Canvas(path, pagesize=letter)
    c.setTitle('Computing with Tiles')
    c.setAuthor('C. Scott Ananian')
    c.setSubject('A wall of Wang tiles that sieves for primes')
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    draw_frame(c)
    c.setFillColor(PAPER)
    c.rect(IN + 4.5, IN + 4.5, W - 2 * IN - 9, H - 2 * IN - 9, stroke=0, fill=1)

    title_block(c, 'COMPUTING WITH TILES',
                'a wall of Wang tiles that sieves for primes, in ordinary 2″ × 8″ subway tile',
                accent=ACCENT, ornament=ornament)

    # I. Wang tiles -------------------------------------------------------
    y = 650 - gap
    heading(c, 'I', 'Wang tiles', X0, y, CW, accent=ACCENT)
    jr_size, jr_gap = 20, 4
    jr_w = 6 * jr_size + 5 * jr_gap
    tw = CW - jr_w - 16
    yb = para(c, 'A <i>Wang tile</i> is a square with a type on each edge, shown here by color. '
                 'Tiles are laid edge to edge so that touching edges match, and may not be rotated or '
                 'reflected. Hao Wang (<font name="CJK">王浩</font>)<super>†</super> conjectured in 1961 that any set of such tiles that can '
                 'cover the plane can also cover it periodically. Robert Berger (1966) showed '
                 'otherwise: tiles can mimic any computer program, one row per step, so '
                 'whether a set tiles the plane is undecidable. Along the way he found the '
                 'first <i>aperiodic</i> set, 20,426 tiles that tile the plane but never '
                 'periodically. At right is the smallest aperiodic set possible: 11 tiles with 4 edge '
                 'types (Jeandel &amp; Rao, 2015).', X0, y - 12, tw, small)
    draw_jeandel_rao(c, X1 - jr_w, y - 16, jr_size, jr_gap)
    c.setFont('Serif-Italic', 7.4)
    c.setFillColor(GREY_T)
    c.drawCentredString(X1 - jr_w / 2, y - 16 - 2 * jr_size - jr_gap - 11,
                        'an aperiodic set: these tile the plane, never periodically')

    # II. Computing a sum -------------------------------------------------
    y = min(yb, y - 80) - 15 - gap
    heading(c, 'II', 'Tiles that add', X0, y, CW, accent=ACCENT)
    sz = 13.0
    a1, a2 = 4, 7
    fig_w = (a1 + a2 + 1) * sz
    fy = y - 30
    rows, s_cols = draw_sum(c, X0, fy, sz, a1, a2)
    c.setFont('Serif-Italic', 7.4)
    c.setFillColor(GREY_T)
    c.drawCentredString(X0 + fig_w / 2, fy - len(rows) * sz - 10,
                        f'A at {a1} and {a2} force S to {a1 + a2}')
    tx = X0 + fig_w + 16
    yb = para(c, 'Tiles can do arithmetic because a forced tiling carries information. '
                 'Both tilings on this page fill a quarter plane whose top and left edges '
                 'are black: only <b>★</b> fits in the corner, and the rest follows. In '
                 'these 16 tiles (after Grünbaum &amp; Shephard) the edge types draw lines. A light grey line runs down from '
                 'each <b>A</b>; a charcoal diagonal leaves <b>★</b> at 45°, turns along the '
                 'bottom at the first line, and climbs back (red) from the second. Equal '
                 'diagonals carry the first distance across, so the climb reaches the top at '
                 'column A₁&nbsp;+&nbsp;A₂: put the <b>S</b> anywhere else and the tiling cannot be '
                 'completed.', tx, y - 12, X1 - tx, small)
    # the tile set, in a row under the text
    n_sum = len(wt.SUM_TILES)
    st_gap = 3.0
    st = (X1 - tx - (n_sum - 1) * st_gap) / n_sum
    sy = yb - 6
    for k, t in enumerate(wt.SUM_TILES):
        cx = tx + k * (st + st_gap) + st / 2
        draw_colour_tile(c, t[:4], View(cx, sy - st / 2, st), 0, 0, SUM_COLOR, outline=SLATE)
        if t[4]:
            c.setFont('Serif-Bold', 7)
            c.setFillColor(SLATE)
            c.drawCentredString(cx, sy - st - 8, '★' if t[4] == '*' else t[4])
    yb = sy - st - 10

    # III. The sieve ------------------------------------------------------
    y = min(yb, fy - len(rows) * sz - 14) - 15 - gap
    heading(c, 'III', 'A wall that finds primes', X0, y, CW, accent=ACCENT)
    u0, v0, u1, v1 = WALL['wall_units']
    ws = 11.2
    wy = y - 24
    view = View(X0, wy, ws, u0, v0)
    wall_rect = (X0, wy - (v1 - v0) * ws, X0 + (u1 - u0) * ws, wy)
    draw_wall(c, view, wall_rect, built=False)
    c.saveState()
    clip = c.beginPath()
    clip.rect(wall_rect[0], wall_rect[1], wall_rect[2] - wall_rect[0], wall_rect[3] - wall_rect[1])
    c.clipPath(clip, stroke=0, fill=0)
    draw_grid(c, view, int(np.ceil(u1)) + 1, int(np.ceil(v1)) + 1)
    c.restoreState()
    c.setStrokeColor(SLATE)
    c.setLineWidth(0.6)
    c.rect(wall_rect[0], wall_rect[1], wall_rect[2] - wall_rect[0], wall_rect[3] - wall_rect[1])
    for n in range(1, 21):
        px, _ = view((n - 1, 0))
        prime = wt.is_prime(n)
        c.setFont('Serif-Bold' if prime else 'Serif', 7.2 if prime else 6.4)
        c.setFillColor(ACCENT if prime else GREY_T)
        c.drawCentredString(px, wy + 3, str(n))
    wall_w = wall_rect[2] - wall_rect[0]
    tx = X0 + wall_w + 14
    tb = para(c, 'The wall is a tiling with a set of 43 Wang tiles (section IV). Each edge '
            'type is shown by a tile color plus a pattern of etched lines, and a run of '
            'matching edges is laid as a single subway tile set on the diagonal. Column <i>n</i> '
            'stands for the number <i>n</i>, and again the black top and left edges force '
            'everything else.<br/><br/>'
            'The double lines force rows of square boxes with odd sides, repeating across '
            'the wall and growing going down: 3, 5, 7, 9, …, each crossed by a charcoal '
            'diagonal. The first box in each row, drawn with thick double lines, sends a '
            'thick single ray up toward the top. If the ray reaches the top without '
            'hitting the edge of a box above it, it marks a prime; if it hits one, it '
            'turns into a thin line, marking a composite. (Even numbers get no ray; 2 has '
            'a tile of its own.) The thick rays reach the red top row at 2, 3, 5, 7, 11, '
            '13, 17 and 19.', tx, y - 12, X1 - tx, small)

    # IV. The tiles -------------------------------------------------------
    y = min(wall_rect[1], tb) - 15 - gap
    heading(c, 'IV', 'The 43 tiles', X0, y, CW, accent=ACCENT)
    per_row = 22
    ts = 17.0
    gap = (CW - per_row * ts) / (per_row - 1)
    ty = y - 12
    for k, t in enumerate(wt.TILES):
        r, q = divmod(k, per_row)
        cx = X0 + q * (ts + gap) + ts / 2
        cy = ty - r * (ts + 11) - ts / 2
        draw_wang_tile(c, t, View(cx, cy, ts), 0, 0)
        c.setFont('Serif', 5.4)
        c.setFillColor(GREY_T)
        c.drawCentredString(cx, cy - ts / 2 - 6, t.name)
    yb = ty - 2 * (ts + 11) - 1
    yb = para(c, 'Tile color plus etching gives the edge type, 15 in all; edges must match, and that is the only rule. '
            'With the top and left edges black, these tiles fill the quarter plane in '
            'exactly one way, and that tiling is aperiodic: its boxes keep growing and '
            'the primes never repeat.', X0, yb, CW, small)

    fb = para(c, '<super>†</super> In Cantonese, Wang’s surname <font name="CJK">王</font> '
                 'is a homophone of <font name="CJK">黃</font>, Wong: a name held by several '
                 'members of this house.', X0, yb - 6, CW, foot)
    if fb < 80:
        print('warning: footnote runs into the footer by %.1f pt' % (80 - fb))
    footer(c, 'Tile set PRIME2b from github.com/cscott/tile-hack (wangprime.js). '
              'Addition after Grünbaum & Shephard, Tilings and Patterns, §11.4.',
           accent=ACCENT, signature=SIGNATURE)
    c.showPage()
    c.save()
    return fb


if __name__ == '__main__':
    # spread any space left under the footnote evenly above the four headings
    FOOTER_TOP, SLACK = 76, 8
    spare = build() - FOOTER_TOP - SLACK
    if spare > 0:
        build(gap=spare / 4)
