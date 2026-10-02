"""Fibonacci Wang tiles, after Grünbaum & Shephard, Tilings and Patterns,
Fig. 11.4.2, corrected.

The book's panel (b) lists 17 tiles; the forced tiling also needs the interior
diagonal step (7, 8, 1, 1) (the panel has only its border variant
(7, 8, 1, 0)), and its example grid (a) is missing two 6 labels at (2,2) and
(2,3).  With these 18 tiles and black (0) on the top and left edges, the
quarter-plane tiling is forced and its top row marks 1, 2, 3, 5, 8, 13, 21, ...

Edge types (h = on left/right edges, v = on top/bottom edges):
  0 border            1 blank
  2 F' | F''  (h)     3 between top-row tiles (h)
  4 under F'  (v)     5 F' line across to F'' (h)
  6 result ray down from each F (v)
  7, 8  diagonal running down-right (v, h)
  9, 10 staircase running up-right (h, v)
  11 under F (v)      12 carries a distance across to the next F (h)
"""
import wangtiles as wt

TILES_RAW = [
    (0, 2, 4, 0, "F'"), (0, 3, 6, 2, "F''"), (0, 3, 11, 3, 'F'), (0, 3, 1, 3, ''),
    (1, 1, 1, 0, ''),
    (4, 5, 7, 0, ''), (6, 9, 6, 12, ''), (11, 1, 6, 9, ''), (10, 1, 1, 9, ''),
    (1, 9, 10, 1, ''), (6, 1, 6, 1, ''),
    (7, 8, 1, 0, ''), (1, 1, 7, 8, ''), (6, 12, 7, 8, ''), (1, 12, 1, 12, ''),
    (6, 9, 6, 5, ''), (1, 1, 1, 1, ''),
    (7, 8, 1, 1, ''),                     # missing from the book's panel
]


def L(base, *lines):
    return (base, list(lines))


# Looks, in the prime set's vocabulary: tan = silk, grey = charcoal,
# brown = auburn, black = basalt.  (horizontal look, vertical look)
LOOKS = {
    0: (L('black'), L('black')),
    1: (L('tan'), L('tan')),
    2: (L('brown'), None),                       # as * -> p in the prime set
    3: (L('brown'), None),                       # top row
    4: (None, L('brown', 'thick', 'thick')),     # under F', like under *
    5: (L('tan', 'thick', 'thick'), None),       # F' double line turns to F''
    6: (None, L('tan', 'thick')),                # the result ray
    7: (None, L('grey')),                        # diagonal down-right
    8: (L('grey'), None),
    9: (L('grey', 'thin'), None),                # staircase up-right
    10: (None, L('grey', 'thin')),
    11: (None, L('brown', 'thick')),             # under F, like under p
    12: (L('tan', 'thick'), None),               # the distance carried across
}
NOTES = {0: 'border', 1: 'blank', 2: "F′ to F″", 3: 'top row', 4: "under F′",
         5: "F′ across to F″", 6: 'result ray', 7: 'diagonal ↘', 8: 'diagonal ↘',
         9: 'staircase ↗', 10: 'staircase ↗', 11: 'under F', 12: 'distance across'}


class FibTile(wt.Tile):
    def look(self, side):
        h, v = LOOKS[self.edge(side)]
        return v if side in ('top', 'bottom') else h


TILES = [FibTile(i, n or '', t, r, b, l) for i, (t, r, b, l, n) in enumerate(TILES_RAW)]


def visual_set():
    """The tiles as they would be seen: edges that look alike are merged."""
    ids = {}

    def k(t, s):
        base, lines = t.look(s)
        key = (s in ('top', 'bottom'), base, tuple(lines))
        return 0 if base == 'black' else ids.setdefault(key, len(ids) + 1)
    out = []
    for t in TILES:
        v = (k(t, 'top'), k(t, 'right'), k(t, 'bottom'), k(t, 'left'), t.name)
        if v[:4] not in [o[:4] for o in out]:
            out.append(v)
    return out


def forced(width=22, height=14):
    """The tiling (rows of FibTile) using tiles in order, as for the sum."""
    raw = [(t.top, t.right, t.bottom, t.left, t) for t in TILES]
    plain = lambda t: sum(e == 1 for e in t[:4]) >= 3 and not t[4].name
    rows = wt.solve(sorted(raw, key=lambda t: not plain(t)), width, height)
    return [[t[4] for t in row] for row in rows]


# --------------------------------------------------------------- laying it in subway tile
import math

PITCH = math.sqrt(0.5)               # diamond diagonal, in Wang-tile units
SIDE_JOINT = PITCH * 1.6 / 51.6      # 1/16" along the long sides
END_JOINT = PITCH * 6.4 / 51.6       # 1/4" at the ends
MAX_RUN = 4                          # a 2" x 8" tile covers 4 diamonds


def _cell_centre(a, b):
    return ((a - b + 1) / 2, (a + b) / 2)


def cells(rows):
    """Diamonds of the tiling: {(a, b): base}.  A diamond straddles one edge;
    a = x + y - 1/2 and b = y - x + 1/2 of its centre, so a step down-right
    is a + 1 and a step up-right is b - 1."""
    out = {}
    for j, row in enumerate(rows):
        for i, t in enumerate(row):
            out[(i + j, j - i + 1)] = t.look('bottom')[0]
            out[(i + j, j - i)] = t.look('right')[0]
    return out


def lay_tiles(rows, diagonal_b=2):
    """Group diamonds into 2" x 8" subway tiles.

    On the main diagonal (b == diagonal_b) and below it, tiles run down-right;
    above it they run up-right.  Each straight run of one colour gets as many
    whole tiles as fit, laid from its upper end, and at most one tile cut short.
    Returns [(base, [cells])]."""
    cs = cells(rows)
    pieces = []
    down = {k: v for k, v in cs.items() if k[1] >= diagonal_b}
    up = {k: v for k, v in cs.items() if k[1] < diagonal_b}

    def runs(region, line_of, pos_of, step):
        seen = set()
        for k in sorted(region, key=lambda k: (line_of(k), pos_of(k))):
            if k in seen:
                continue
            run = [k]
            while True:
                n = step(run[-1])
                if n in region and region[n] == region[k]:
                    run.append(n)
                else:
                    break
            seen.update(run)
            for s in range(0, len(run), MAX_RUN):
                pieces.append((region[k], run[s:s + MAX_RUN]))
    runs(down, lambda k: k[1], lambda k: k[0], lambda k: (k[0] + 1, k[1]))
    runs(up, lambda k: k[0], lambda k: k[1], lambda k: (k[0], k[1] + 1))
    return pieces


def piece_polygon(cells_):
    """The tile covering a straight run of diamonds, with grout around it."""
    p0 = _cell_centre(*cells_[0])
    p1 = _cell_centre(*cells_[-1])
    if len(cells_) > 1:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
    else:                                  # a single diamond: orientation is moot
        ux, uy = math.sqrt(0.5), math.sqrt(0.5)
    vx, vy = -uy, ux
    h = PITCH / 2 - END_JOINT / 2
    w = PITCH / 2 - SIDE_JOINT / 2
    a = (p0[0] - ux * h, p0[1] - uy * h)
    b = (p1[0] + ux * h, p1[1] + uy * h)
    return [(a[0] + vx * w, a[1] + vy * w), (b[0] + vx * w, b[1] + vy * w),
            (b[0] - vx * w, b[1] - vy * w), (a[0] - vx * w, a[1] - vy * w)]


def tile_stats(pieces):
    from collections import Counter
    return Counter(len(c) for _, c in pieces)
