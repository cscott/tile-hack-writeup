#!/usr/bin/env python3
"""Two-page framed print about the Wang-tile prime sieve in the downstairs
bathroom.  Page 1: Wang tiles, tiles that add, and an unbuilt Fibonacci wall
(with the Fibonacci tiling as its border).  Page 2: the prime wall itself and
its 43 tiles (with the as-laid prime tiling as its border).

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
SIGNATURE = 'C. Scott Ananian · February 2019'         # page 2: the prime wall, as built
SIGNATURE_FIB = 'C. Scott Ananian · October 2026'     # page 1: carries the new Fibonacci design

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


def _triangle_regions(grid=None):
    grid = grid or GRID
    out = {}
    for i in range(grid.w):
        for j in range(grid.h):
            t = grid.g[i][j]
            for side in wt.SIDES:
                out.setdefault(tile_glaze(t, side), []).append(side_triangle(side, i, j))
    return out


TRIANGLES = _triangle_regions()


def draw_wall(c, view, clip, built=True, grout=None, grid=None):
    """Draw the wall clipped to a page rect.  built=True: the tiles as laid,
    with grout (from the cutting guide); built=False: the bare Wang tiling,
    four glazed triangles per square, no grout (from `grid`, default the
    designed 21 x 27 tiling)."""
    x0, y0, x1, y1 = clip
    c.saveState()
    p = c.beginPath()
    p.rect(x0, y0, x1 - x0, y1 - y0)
    c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(grout or GROUT)
    c.rect(x0, y0, x1 - x0, y1 - y0, stroke=0, fill=1)
    lines = LINES
    if built:
        regions = {g: PIECES.get(g, []) + EXTRA.get(g, []) for g in GLAZE}
    elif grid is None or grid is GRID:
        regions = TRIANGLES
    else:
        regions = _triangle_regions(grid)
        lines = [ln for i in range(grid.w) for j in range(grid.h) for ln in tile_lines(grid.g[i][j], i, j)]
    for glaze, polys in regions.items():
        if polys:
            c.setFillColor(GLAZE[glaze])
            c.drawPath(path_of(c, polys, view), stroke=0, fill=1, fillMode=FILL_EVEN_ODD)
    draw_lines_by_glaze(c, regions, lines, view)
    c.restoreState()


def draw_frame(c, painter=None):
    """Border: by default the whole designed 21 x 27 prime tiling (the wall
    shows the top 15 rows); `painter(c, view, clip)` draws something else."""
    s = (H - 2 * OUT) / GRID.h
    view = View(OUT, H - OUT, s, -0.5, -0.5)
    c.saveState()
    p = c.beginPath()
    p.rect(OUT, OUT, W - 2 * OUT, H - 2 * OUT)
    p.rect(IN, IN, W - 2 * IN, H - 2 * IN)
    c.clipPath(p, stroke=0, fill=0, fillMode=FILL_EVEN_ODD)
    if painter:
        painter(c, view, (OUT, OUT, W - OUT, H - OUT))
    else:
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


JR_PATCH = json.load(open(os.path.join(HERE, 'jr_patch.json')))   # from tools/jr_patch.py


def draw_jr_patch(c, x, y, w, r0=7, rows=11):
    """Rows r0 .. r0+rows-1 of the solved Jeandel-Rao patch, scaled to width
    w, top-left at (x, y).  Returns the y of its bottom edge."""
    patch = JR_PATCH[r0:r0 + rows]
    s = w / len(patch[0])
    view = View(x + s / 2, y - s / 2, s)
    regions = {}
    for j, row in enumerate(patch):
        for i, k in enumerate(row):
            for side, e in zip(wt.SIDES, wt.JEANDEL_RAO[k]):
                regions.setdefault(JR_COLOR[e], []).append(side_triangle(side, i, j))
    fill_regions(c, regions, view)
    c.setStrokeColor(SLATE)
    c.setLineWidth(0.5)
    c.rect(x, y - rows * s, w, rows * s, stroke=1, fill=0)
    return y - rows * s


def draw_sum(c, x, y, size, a1=4, a2=7):
    rows, s_cols = wt.sum_example(a1, a2)
    view = View(x + size / 2, y - size / 2, size)
    regions, lines = {}, []
    for j, row in enumerate(rows):
        for i, t in enumerate(row):
            tile = wt.sum_tile(t)
            for side in wt.SIDES:
                regions.setdefault(tile_glaze(tile, side), []).append(side_triangle(side, i, j))
            lines += tile_lines(tile, i, j)
    fill_regions(c, {GLAZE[g]: polys for g, polys in regions.items()}, view)
    draw_lines_by_glaze(c, regions, lines, view)
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


# ------------------------------------------------------------------ Fibonacci
import fibtiles as ft

FIB_ROWS = ft.forced(32, 28)      # extra columns on the right keep the stagger even


def fib_regions(rows):
    regions = {}
    for base, run in ft.lay_tiles(rows):
        regions.setdefault(GLAZE_OF_BASE[base], []).append(ft.piece_polygon(run))
    for j, row in enumerate(rows):                     # basalt border triangles
        for i, t in enumerate(row):
            for side in ('top', 'left'):
                if t.edge(side) == 0:
                    tri = np.array(side_triangle(side, i, j))
                    m = tri.mean(0)
                    regions.setdefault('basalt', []).append([tuple(m + 0.9 * (p - m)) for p in tri])
    lines = [ln for j, row in enumerate(rows) for i, t in enumerate(row)
             for ln in tile_lines(t, i, j)]
    return regions, lines


FIB_REGIONS, FIB_LINES = fib_regions(FIB_ROWS)


def draw_fib(c, view, clip, grout=BORDER_GROUT):
    """The Fibonacci tiling as it could be laid in 2" x 8" tile, clipped."""
    x0, y0, x1, y1 = clip
    c.saveState()
    p = c.beginPath()
    p.rect(x0, y0, x1 - x0, y1 - y0)
    c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(grout)
    c.rect(x0, y0, x1 - x0, y1 - y0, stroke=0, fill=1)
    fill_regions(c, {GLAZE[g]: polys for g, polys in FIB_REGIONS.items()}, view)
    draw_lines_by_glaze(c, FIB_REGIONS, FIB_LINES, view)
    c.restoreState()


# ------------------------------------------------------------------ the pages
def ornament(c, cx, cy):
    t = wt.TILES[[x.name for x in wt.TILES].index('p')]     # the tile that says "prime"
    draw_wang_tile(c, t, View(cx, cy, 15), 0, 0)


def fib_ornament(c, cx, cy):
    draw_wang_tile(c, ft.TILES[2], View(cx, cy, 15), 0, 0)      # F, like p


def framed_page(c, painter=None):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    draw_frame(c, painter)
    c.setFillColor(PAPER)
    c.rect(IN + 4.5, IN + 4.5, W - 2 * IN - 9, H - 2 * IN - 9, stroke=0, fill=1)


def framed_figure(c, rect, view, cols, rows, painter):
    """Draw a tiling into rect with the dotted grid and a slate frame."""
    painter(c, view, rect)
    c.saveState()
    clip = c.beginPath()
    clip.rect(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])
    c.clipPath(clip, stroke=0, fill=0)
    draw_grid(c, view, cols, rows)
    c.restoreState()
    c.setStrokeColor(SLATE)
    c.setLineWidth(0.6)
    c.rect(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])


def column_numbers(c, view, y, ncols, marked, big=7.2, small_=6.4):
    for i in range(ncols):
        px, _ = view((i, 0))
        m = marked(i)
        c.setFont('Serif-Bold' if m else 'Serif', big if m else small_)
        c.setFillColor(ACCENT if m else GREY_T)
        c.drawCentredString(px, y + 3, str(i + 1))


def page_one(c, gap=0.0):
    """Wang tiles, tiles that add, and Fibonacci.  `gap` is extra space above
    each section heading.  Returns the y of the bottom of the footnotes."""
    framed_page(c, draw_fib)
    title_block(c, 'COMPUTING WITH TILES',
                'Wang tiles that add, and a wall that counts in Fibonacci numbers',
                accent=ACCENT, ornament=fib_ornament)

    # I. Wang tiles -------------------------------------------------------
    y = 650 - gap
    heading(c, 'I', 'Wang tiles', X0, y, CW, accent=ACCENT)
    jr_col = 140                          # right-hand column: the tiles, then a patch
    jr_size, jr_gap = 14, 3
    jr_w = 6 * jr_size + 5 * jr_gap
    tw = CW - jr_col - 16
    yb = para(c, 'A <i>Wang tiling</i> is a tiling of square tiles with labels on each edge, such that the labels on touching edges match. '
                 'Tiles may not be rotated or '
                 'reflected. '
                 'We represent labels as a combination of color and etched lines, which must form a continuous line on a uniform background where edges meet. '
                 'Hao Wang (<font name="CJK">王浩</font>)<super>†</super> conjectured in 1961 that any set of such tiles that can '
                 'cover the plane can also cover it periodically. Robert Berger (1966) showed '
                 'otherwise: tiles can mimic any computer program (they are <i>Turing complete</i>), so '
                 'whether a set tiles the plane is undecidable. Along the way he found the '
                 'first <i>aperiodic</i> set, 20,426 tiles that tile the plane but never '
                 'repeat. At right is the smallest aperiodic set possible: 11 tiles with 4 unique edge '
                 'labels (Jeandel &amp; Rao, 2015).', X0, y - 12, tw, small)
    draw_jeandel_rao(c, X1 - jr_col + (jr_col - jr_w) / 2, y - 14, jr_size, jr_gap)
    py = y - 14 - 2 * jr_size - jr_gap - 6
    pb = draw_jr_patch(c, X1 - jr_col, py, jr_col)
    c.setFont('Serif-Italic', 7.4)
    c.setFillColor(GREY_T)
    c.drawCentredString(X1 - jr_col / 2, pb - 10, 'a minimal aperiodic set, and a patch of its tiling')
    jr_bottom = pb - 14
    # second paragraph, full width, below the text and the tile column
    yb = para(c, 'Our goal is to achieve an aperiodic tiling for the home using tiles in '
                 'easily obtainable practical shapes. Wang tiles are attractive because the '
                 'aperiodicity is from edge matching rather than shape. The Jeandel &amp; Rao '
                 'tile set thus achieves our goal, but let\'s go further.'
                 '', X0, min(yb, jr_bottom) - 6, CW, small)

    # II. Computing a sum -------------------------------------------------
    y = yb - 15 - gap
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
    n_sum = len(wt.SUM_TILES)
    st_gap = 3.0
    st = (X1 - tx - (n_sum - 1) * st_gap) / n_sum
    sy = y - 12
    for k, t in enumerate(wt.SUM_TILES):
        cx = tx + k * (st + st_gap) + st / 2
        draw_wang_tile(c, wt.sum_tile(t), View(cx, sy - st / 2, st), 0, 0)
        if t[4]:
            c.setFont('Serif-Bold', 7)
            c.setFillColor(SLATE)
            c.drawCentredString(cx, sy - st - 8, '★' if t[4] == '*' else t[4])
    yb = para(c, 'This set of 16 tiles with 6 labels demonstrates arithmetic with Wang tiles. '
                 'We will work on a quarter plane whose top and left edges '
                 'are constrained to be black. Place the <b>A</b> tiles on the top row at your input values, A₁ and A₂. The <b>★</b> tile can only be placed in the corner. '
                 'The tile edge constraints cause an etched line to descend from '
                 'each <b>A</b>. A charcoal diagonal leaves <b>★</b>; where it meets the first line it turns and starts a horizontal line at a depth corresponding to A₁. When that meets the second line '
                 'a red diagonal climbs up. This forces the <b>S</b> tile, representing the sum, to be placed at '
                 'column A₁&nbsp;+&nbsp;A₂.'
                 , tx, sy - st - 14, X1 - tx, small)

    # III. Fibonacci ------------------------------------------------------
    y = min(yb, fy - len(rows) * sz - 14) - 15 - gap
    heading(c, 'III', 'Fibonacci numbers', X0, y, CW, accent=ACCENT)
    # the 18 tiles, full width, and what they are
    n = len(ft.TILES)
    ts = 20.0
    tg = (CW - n * ts) / (n - 1)
    ty = y - 12
    for k, t in enumerate(ft.TILES):
        cx = X0 + k * (ts + tg) + ts / 2
        draw_wang_tile(c, t, View(cx, ty - ts / 2, ts), 0, 0)
        if t.name:
            c.setFont('Serif-Bold', 7)
            c.setFillColor(SLATE)
            c.drawCentredString(cx, ty - ts - 8, t.name.replace("''", '″').replace("'", '′'))
    yb = ty - ts - 10                    # just below the tile labels
    # the tiling, with two paragraphs beside it
    cols, nrows = 22, 14
    fs = 11.2
    fy = yb - 22
    view = View(X0 + fs / 2, fy - fs / 2, fs)
    rect = (X0, fy - nrows * fs, X0 + cols * fs, fy)
    framed_figure(c, rect, view, cols, nrows, draw_fib)
    column_numbers(c, view, fy, cols, lambda i: FIB_ROWS[0][i].name.startswith('F'))
    c.setFont('Serif-Italic', 7.4)
    c.setFillColor(GREY_T)
    c.drawCentredString((rect[0] + rect[2]) / 2, rect[1] - 10,
                        'as it could be laid in 2″ × 8″ subway tile')
    tx = rect[2] + 14
    tb = para(c, ''
              'By extending the previous tiles we can generate the Fibonacci numbers, each the sum of the two before. '
              'This set of 18 Wang tiles have 9 distinct edge labels; top and left borders are constrained to be black as before. '
              'The <b>F′</b> and <b>F″</b> tiles in the corner mark the first two numbers, 1 '
                 'and 2.<super>‡</super> Every <b>F</b> sends an etched line down. A long charcoal '
                 'diagonal leaves the corner, and where it meets the line of the '
                 '<b>F</b> at column <i>n</i>, at depth <i>n</i>, the line turns and runs right '
                 'to the descending line of the next <b>F</b>, at column <i>m</i>. There a charcoal '
                 'staircase climbs back up, rising <i>n</i> rows '
                 'as it moves <i>n</i> columns right, and reaches the top at column '
                 '<i>m</i>&nbsp;+&nbsp;<i>n</i>: the next <b>F</b>, which then sends its own ray down.'
              '', tx, fy + 10, X1 - tx, small)
    tb = para(c, ''
              'The tiling is aperiodic because the Fibonacci numbers spread out, so this is another tiling which would achieve our goal. '
              'Using subway tiles oriented differently above and below the '
              'long charcoal diagonal adds visual interest.'
              '', tx, tb - 5, X1 - tx, small)
    yb = min(rect[1] - 14, tb)

    fb = para(c, '<super>†</super> In Cantonese, Wang’s surname <font name="CJK">王</font> '
                 'is a homophone of <font name="CJK">黃</font>, Wong: a name held by several '
                 'members of this home.', X0, yb - 6, CW, foot)
    fb = para(c, '<super>‡</super> <b>F′</b> and <b>F″</b> fix the start: with two more tiles '
                 'that let <b>F″</b> stand at column 3 instead, the same machinery produces the '
                 'Lucas numbers 1, 3, 4, 7, 11, 18, 29.', X0, fb - 2, CW, foot)
    # (Dropped from the poster: Grünbaum & Shephard's Fig. 11.4.2 has three
    # misprints.  Its list of tiles leaves out the one that continues the
    # diagonal, its example drops two of the "6" edge labels in column 3, and
    # its caption counts 11 among the Fibonacci numbers.  See fibtiles.py.)
    if fb < 80:
        print('warning: page 1 footnotes run into the footer by %.1f pt' % (80 - fb))
    footer(c, 'Addition and Fibonacci tiles after Grünbaum & Shephard, Tilings and Patterns, §11.4.',
           accent=ACCENT, signature=SIGNATURE_FIB)
    c.showPage()
    return fb


def page_two(c, gap=0.0, ws=None):
    """The prime wall and its 43 tiles."""
    framed_page(c)
    title_block(c, 'A WALL THAT FINDS PRIMES',
                'Wang tiles that sieve for primes, in ordinary 2″ × 8″ subway tile',
                accent=ACCENT, ornament=ornament)

    # IV. The sieve -------------------------------------------------------
    y = 650 - gap
    heading(c, 'IV', 'A prime number sieve', X0, y, CW, accent=ACCENT)
    # the 43 tiles and what they are, then the wall
    per_row = 22
    ts = 17.0
    tg = (CW - per_row * ts) / (per_row - 1)
    ty = y - 12
    BOLD = {'*', 'p', 'c', 'B*'}          # the tiles the text talks about
    for k, t in enumerate(wt.TILES):
        r, q = divmod(k, per_row)
        cx = X0 + q * (ts + tg) + ts / 2
        cy = ty - r * (ts + 11) - ts / 2
        draw_wang_tile(c, t, View(cx, cy, ts), 0, 0)
        if t.name in BOLD:
            c.setFont('Serif-Bold', 6.6)
            c.setFillColor(SLATE)
        else:
            c.setFont('Serif', 5.4)
            c.setFillColor(GREY_T)
        c.drawCentredString(cx, cy - ts / 2 - 6, '★' if t.name == '*' else t.name)
    yb = ty - 2 * (ts + 11) - 1
    yb = para(c, 'The wall in this room is an aperiodic tiling using a set of 43 Wang tiles with 15 distinct edge labels. '
                 'Each edge label is shown by a tile color plus a pattern of etched lines, and '
                 'a run of matching colors is laid as a single subway tile set on the diagonal. '
                 'Tiles can not be rotated or reflected, edges must match, and the top and left borders must be black. '
                 'Given these constraints, the tiles fill '
                 'the infinite quarter plane in exactly one way, and that tiling is aperiodic due to the nature of primes.', X0, yb, CW, small)
    yb = para(c, ''
                 'Column <i>n</i> stands for the number <i>n</i>. '
                 'Each odd column sends down a thin or thick etched line. '
                 'These interact with the thick double etched lines to start '
                 'an vertical sequence of boxes of increasing odd sizes (3, 5, 7, 9, …) '
                 'which then interact with the charcoal diagonals to repeat '
                 'in rows. The line from the odd column is constrained to '
                 'be thick only if it never crosses the vertical edge of '
                 'another box, marking a prime (tile <b>Ap</b>); otherwise the line becomes '
                 'thin marking an odd composite (tile <b>Ac</b>). '
                 '(Even numbers get no ray; 2 has a tile of its own, <b>B*</b>.) The thick '
                 'rays reach the red top row at 2, 3, 5, 7, 11, 13, 17 and 19, marked by tile <b>p</b>. Composite numbers use tile <b>c</b>.',
              X0, yb - 6, CW, small)
    u0, v0, u1, v1 = FIG_UNITS
    ws = ws or WALL_SCALE
    wy = yb - 20 - gap
    ww = (u1 - u0) * ws
    wx = X0 + (CW - ww) / 2
    view = View(wx, wy, ws, u0, v0)
    rect = (wx, wy - (v1 - v0) * ws, wx + ww, wy)
    # the designed tiling is 21 x 27; solve a larger one if the figure needs it
    # (its first 21 columns are identical to the designed tiling)
    fig_grid = wt.bathroom_grid(max(GRID.w, FIG_COLS), max(GRID.h, FIG_ROWS))
    framed_figure(c, rect, view, FIG_COLS, FIG_ROWS,
                  lambda c, v, r: draw_wall(c, v, r, built=False, grid=fig_grid))
    # the part actually on the wall, dashed
    wu0, wv0, wu1, wv1 = WALL['wall_units']
    (ax, ay), (bx, by) = view((wu0, wv0)), view((wu1, wv1))
    c.saveState()
    c.setStrokeColor(Color(0.25, 0.33, 0.43, alpha=0.35))
    c.setLineWidth(0.6)
    c.setDash(1.6, 2.2)
    c.rect(ax, by, bx - ax, ay - by, stroke=1, fill=0)
    c.restoreState()
    column_numbers(c, view, wy, FIG_COLS, lambda i: wt.is_prime(i + 1), big=8.4, small_=7.2)
    c.setFont('Serif-Italic', 7.4)
    c.setFillColor(GREY_T)
    c.drawCentredString(X0 + CW / 2, rect[1] - 10,
                        f'the Wang tiling, columns 1–{FIG_COLS} and the top {FIG_ROWS} rows; the wall in this '
                        'room is the first 20 columns and 15 rows (dashed)')
    fb = rect[1] - 14
    if fb < 80:
        print('warning: page 2 text runs into the footer by %.1f pt' % (80 - fb))
    footer(c, 'Tile set PRIME2b from github.com/cscott/tile-hack (wangprime.js).',
           accent=ACCENT, signature=SIGNATURE)
    c.showPage()
    return fb


WALL_SCALE = 21.0       # points per Wang tile in the page-2 figure; main() fits it to the page
FIG_COLS, FIG_ROWS = 25, 18       # page-2 figure: through column 25 = 5 x 5, down to the bottom of the 7-box
FIG_UNITS = (-0.5, -0.5, FIG_COLS - 0.5, FIG_ROWS - 0.5)


def build(path='wang-tiling.pdf', gaps=(0.0, 0.0), ws=None):
    c = canvas.Canvas(path, pagesize=letter)
    c.setTitle('Computing with Tiles')
    c.setAuthor('C. Scott Ananian')
    c.setSubject('Walls of Wang tiles that add up Fibonacci numbers and sieve for primes')
    fbs = (page_one(c, gaps[0]), page_two(c, gaps[1], ws))
    c.save()
    return fbs


if __name__ == '__main__':
    # page 2: fit the figure to the free space (up to the full text width);
    # then, on both pages, spread what is left evenly above the
    # headings (and the page-2 figure)
    FOOTER_TOP, SLACK = 76, 8
    u0, v0, u1, v1 = FIG_UNITS
    fbs = build()
    ws = min(CW / (u1 - u0), WALL_SCALE + (fbs[1] - FOOTER_TOP - SLACK - 6) / (v1 - v0))
    fbs = build(ws=ws)
    print('wall figure at %.1f pt per tile; free space:' % ws,
          [round(fb - FOOTER_TOP - SLACK, 1) for fb in fbs])
    gaps = tuple(max(0.0, (fb - FOOTER_TOP - SLACK) / n) for fb, n in zip(fbs, (3, 2)))
    build(gaps=gaps, ws=ws)
