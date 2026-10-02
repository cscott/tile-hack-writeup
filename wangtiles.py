"""Wang tiles that sieve for primes: a Python port of tile-hack/wangprime.js
(tile set PRIME2b, VARIANT 3), the tiling in the downstairs bathroom.

A Wang tile is a unit square whose four edges carry colours; tiles are placed
edge to edge, matching colours must agree, and tiles may not be rotated or
reflected.  Here each edge colour also has a *look*: a base glaze (which
subway tile it is made of) plus a pattern of etched lines.

Physical construction (see wang3.svg / wang3-grout.svg): cut each Wang square
along both diagonals into four triangles, one per edge, coloured by that edge.
The two triangles on either side of an edge form a diamond of a single colour,
and runs of same-coloured diamonds are laid as diagonal 2"x8" subway tiles,
trimmed to 1, 2, 3 or 4 diamonds long.
"""
import sys

# --------------------------------------------------------------- the tile set
# (name, top, right, bottom, left)  -- verbatim from PRIME2b in wangprime.js
PRIME2B = [
    (' * ', 0, 2, 12, 0),
    (' A*', 12, 12, 1, 0),
    (' B*', 5, 1, 2, 12),
    (' E*', 4, 4, 1, 0),
    (' G*', 1, 1, 1, 0),

    (' p ', 0, 2, 5, 2),
    (' Ap', 5, 2, 6, 1),
    (' Ep', 7, 4, 6, 1),
    (' Fp', 6, 1, 7, 4),
    (' Gp', 6, 1, 6, 1),

    (' c ', 0, 2, 8, 2),
    (' Ac', 8, 2, 9, 1),
    (' Ec', 10, 4, 9, 1),
    (' Fc', 9, 1, 10, 4),
    (' Gc', 9, 1, 9, 1),

    (' B ', 8, 1, 1, 2),
    (' E ', 4, 4, 1, 1),
    (' F ', 1, 1, 4, 4),
    (' G ', 1, 1, 1, 1),

    ('D1*', 1, 13, 4, 0),
    ('D2*', 1, 13, 1, 13),
    ('D4*', 6, 11, 3, 13),

    ('D1p', 6, 3, 7, 11),
    ('D2p', 6, 3, 6, 3),

    ('D1c', 9, 3, 10, 11),
    ('D2c', 9, 3, 9, 3),
    ('D4c', 9, 11, 14, 3),

    ('D1 ', 1, 3, 4, 11),
    ('D2 ', 1, 3, 1, 3),
    ('D4 ', 1, 11, 3, 3),
    ('D5 ', 3, 1, 3, 1),
    ('D6 ', 3, 1, 2, 4),

    ('D6c', 14, 1, 13, 4),
    ('d1 ', 2, 3, 4, 11),
    ('d2', 2, 3, 1, 3),
    ('d2*', 2, 13, 1, 13),
    ('d4 ', 2, 11, 3, 3),
    ('d1p', 13, 3, 7, 11),
    ('d2p', 13, 3, 6, 3),
    ('d1c', 13, 3, 10, 11),
    ('d2c', 13, 3, 9, 3),
    ('d4c', 13, 11, 14, 3),
    ('D5c', 14, 1, 14, 1),
]

# Edge colour looks: (horizontal, vertical) = how the colour appears on the
# left/right edges and on the top/bottom edges.  Each look is
# (base, [lines...]) with lines 'thin' or 'thick', etched across the edge.
# Base names from wangprime.js; the tiles used for them are in BASE_TILE.
_RAW = [
    ['black'],                                                       # 0 black bar
    ['tan'],                                                         # 1 grass
    [['brown'], ['grey', 'white', 'white']],                         # 2 forest
    ['tan', 'white', 'white'],                                       # 3 grass with fence
    ['grey'],                                                        # 4 mountains
    ['brown', 'thick white'],                                        # 5 forest with road (prime)
    ['tan', 'thick white'],                                          # 6 grass with road
    ['grey', 'thick white'],                                         # 7 mountains with road
    [['brown', 'white'], ['brown']],                                 # 8 forest w/ road type 2 (composite)
    ['tan', 'white'],                                                # 9 grass w/ road type 2
    ['grey', 'white'],                                               # 10 mountain w/ road type 2
    [['grey', 'white', 'white'], ['grey', 'white', 'thick white', 'white']],  # 11
    ['brown', 'thick white', 'thick white'],                         # 12 forest w/ wall
    [['tan', 'thick white', 'thick white'], ['grey', 'white', 'white', 'white']],  # 13
    [['grey', 'thick white', 'thick white'], ['tan', 'white', 'white', 'white']],  # 14
    ['tan', 'white', 'thick white', 'white'],                        # 15 (unused in PRIME2b)
]
NOTES = ['black bar', 'grass', 'forest', 'grass with fence', 'mountains',
         'forest with road (prime)', 'grass with road', 'mountains with road',
         'forest w/ road type 2 (composite)', 'grass w/ road type 2',
         'mountain w/ road type 2', 'mountains w/ fence and road', 'forest w/ wall',
         'mountains w/ wall', 'grass with wall', 'grass w/ fence and road']


def _look(arr):
    base, *lines = arr
    return (base, ['thick' if l.startswith('thick') else 'thin' for l in lines])


COLORS = []
for raw in _RAW:
    if isinstance(raw[0], list):
        COLORS.append((_look(raw[0]), _look(raw[1])))
    else:
        COLORS.append((_look(raw), _look(raw)))

# which glaze each base colour was laid in
BASE_TILE = {'tan': 'silk', 'grey': 'charcoal', 'brown': 'auburn', 'black': 'basalt'}

SIDES = ('top', 'right', 'bottom', 'left')
DELTA = {'top': (0, -1), 'right': (1, 0), 'bottom': (0, 1), 'left': (-1, 0)}
OPP = {'top': 'bottom', 'bottom': 'top', 'left': 'right', 'right': 'left'}


class Tile:
    def __init__(self, index, name, top, right, bottom, left):
        self.index, self.name = index, name.strip()
        self.top, self.right, self.bottom, self.left = top, right, bottom, left

    def edge(self, side):
        return getattr(self, side)

    def look(self, side):
        """(base, lines) for this edge; vertical look on top/bottom."""
        h, v = COLORS[self.edge(side)]
        return v if side in ('top', 'bottom') else h

    def __repr__(self):
        return self.name


TILES = [Tile(i, *t) for i, t in enumerate(PRIME2B)]


# --------------------------------------------------------------- the solver
class Grid:
    """Same search as wangprime.js: column-major backtracking, tiles tried in
    order; cells beyond the top/left border read as colour 0, cells beyond the
    right/bottom border are unconstrained."""

    def __init__(self, width=21, height=27):
        self.w, self.h = width, height
        self.g = [[None] * height for _ in range(width)]

    def color(self, x, y, side):
        if x < 0 or y < 0:
            return 0
        if x >= self.w or y >= self.h:
            return None
        t = self.g[x][y]
        return None if t is None else t.edge(side)

    def ok(self, x, y, t):
        for s in SIDES:
            dx, dy = DELTA[s]
            c2 = self.color(x + dx, y + dy, OPP[s])
            if c2 is not None and c2 != t.edge(s):
                return False
        return True

    def fill(self, tiles=TILES):
        sys.setrecursionlimit(max(10000, 4 * self.w * self.h))
        order = [(x, y) for x in range(self.w) for y in range(self.h)]

        # in column-major order only the top and left neighbours are ever
        # filled, so candidates depend only on those two colours
        cand = {}
        for t in tiles:
            cand.setdefault((t.top, t.left), []).append(t)

        def rec(k):
            if k == len(order):
                return True
            x, y = order[k]
            for t in cand.get((self.color(x, y - 1, 'bottom'), self.color(x - 1, y, 'right')), ()):
                if self.ok(x, y, t):
                    self.g[x][y] = t
                    if rec(k + 1):
                        return True
                    self.g[x][y] = None
            return False
        return rec(0)

    def names(self):
        return [[self.g[x][y].name for x in range(self.w)] for y in range(self.h)]


_SOLVED = {}


def bathroom_grid(width=21, height=27):
    key = (width, height)
    if key not in _SOLVED:
        g = Grid(width, height)
        assert g.fill(), 'no tiling found'
        _SOLVED[key] = g
    return _SOLVED[key]


def is_prime(n):
    return n > 1 and all(n % d for d in range(2, int(n ** .5) + 1))


if __name__ == '__main__':
    g = bathroom_grid()
    for row in g.names():
        print('|'.join(f'{n:^3}' for n in row))
    ps = sorted({x + 1 for x in range(g.w) if g.g[x][0].name == 'p'})
    print('p columns:', ps)
    print('primes   :', [n for n in range(2, g.w + 1) if is_prime(n)])


# --------------------------------------------------------------- small examples
def solve(tiles, width, height, pins=None):
    """Generic version of the same search for tiles given as tuples
    (top, right, bottom, left, label).  `pins` fixes some cells.
    Returns rows of tiles, or None."""
    pins = pins or {}
    g = {}

    def color(x, y, i):
        if x < 0 or y < 0:
            return 0
        t = g.get((x, y))
        return None if t is None else t[i]

    def ok(x, y, t):
        for dx, dy, mine, theirs in ((0, -1, 0, 2), (1, 0, 1, 3), (0, 1, 2, 0), (-1, 0, 3, 1)):
            c2 = color(x + dx, y + dy, theirs)
            if c2 is not None and c2 != t[mine]:
                return False
        return True
    order = [(x, y) for x in range(width) for y in range(height)]
    sys.setrecursionlimit(max(10000, 4 * width * height))

    def rec(k):
        if k == len(order):
            return True
        x, y = order[k]
        for t in ([pins[(x, y)]] if (x, y) in pins else tiles):
            if ok(x, y, t):
                g[(x, y)] = t
                if rec(k + 1):
                    return True
                del g[(x, y)]
        return False
    if not rec(0):
        return None
    return [[g[(x, y)] for x in range(width)] for y in range(height)]


# Addition, after Grunbaum & Shephard, Tilings and Patterns, Fig. 11.4.1.
# (top, right, bottom, left, label).  Edge 0 is the border; 2 runs down from
# each A; 6/3/4 is the diagonal from the star; 5 runs along the bottom; 7/8 is
# the diagonal back up to S.  Numbering columns from 1 at the star, S lands
# at column A1 + A2.
SUM_TILES = [
    (0, 1, 6, 0, '*'), (6, 1, 3, 0, ''), (3, 4, 1, 0, ''), (1, 1, 3, 4, ''), (3, 4, 1, 1, ''),
    (0, 1, 2, 1, 'A'), (2, 1, 2, 1, ''), (2, 5, 1, 4, ''), (1, 5, 1, 5, ''), (2, 7, 1, 5, ''),
    (0, 1, 8, 1, 'S'), (1, 7, 8, 1, ''), (8, 1, 1, 7, ''), (1, 1, 1, 0, ''), (0, 1, 1, 1, ''),
    (1, 1, 1, 1, ''),
]


def sum_example(a1, a2):
    """Tiling showing A at columns a1, a2 (1-based); returns (rows, s_column)."""
    star, A, blank_top = SUM_TILES[0], SUM_TILES[5], SUM_TILES[14]
    # try blank tiles first, so nothing spurious grows in from the open
    # right and bottom edges of this finite patch
    plain = lambda t: sum(e == 1 for e in t[:4]) >= 3 and not t[4]
    no_A = sorted((t for t in SUM_TILES if t[4] != 'A'), key=lambda t: not plain(t))
    width, height = a1 + a2 + 1, a1 + 2
    pins = {(0, 0): star, (a1 - 1, 0): A, (a2 - 1, 0): A}
    for x in range(1, width):
        if (x, 0) not in pins and x != a1 + a2 - 1:
            pins[(x, 0)] = blank_top
    rows = solve(no_A, width, height, pins)
    s_cols = [x + 1 for x, t in enumerate(rows[0]) if t[4] == 'S']
    return rows, s_cols


# An aperiodic set of 11 Wang tiles in 4 colours (Jeandel & Rao, 2015), as
# drawn on Wikipedia and in the talk.  (top, right, bottom, left)
JEANDEL_RAO = [('R', 'R', 'R', 'G'), ('B', 'R', 'B', 'G'), ('R', 'G', 'G', 'G'),
               ('W', 'B', 'R', 'B'), ('B', 'B', 'W', 'B'), ('W', 'W', 'R', 'W'),
               ('R', 'G', 'B', 'W'), ('B', 'W', 'B', 'R'), ('B', 'R', 'W', 'R'),
               ('G', 'G', 'B', 'R'), ('R', 'W', 'R', 'G')]
