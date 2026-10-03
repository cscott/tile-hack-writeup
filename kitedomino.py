"""Kite/domino form of the pinwheel tiling, with the colourings from
github.com/cscott/tile-hack (mksvg.js, KITE_VARIANT with DRAW_GROUT).

A Python port of mkRect()/mkDart().  Every leaf is a real tile:
  * a "domino" = one uncut 2:1 subway tile
  * a "dart"   = a kite made of two half-tiles (each cut on the diagonal),
                 mirror images of each other, separated by a saw kerf.
One level of substitution inflates by 5 (two pinwheel generations).

Coordinates follow the SVG: x right, y DOWN, one unit = one tile+grout
width.  The domino occupies the box [0,2] x [0,1].

Colouring ("permN" styles): a child's colour is its parent's colour plus
bit `num` of N (mod the number of colours), where num is the child's index:
0-12 for the children of a domino, 13-37 for the children of a dart.

Fidelity note: mksvg.js's flipDart() writes the malformed transform
"rotate({$ALPHA_DEG}) ...", which renderers (Inkscape included) discard,
so a "flipped" dart is drawn unflipped.  The bathroom was laid from that
output, so this port reproduces it (FLIPDART_IS_IDENTITY = True).  Set it to
False for the intended flip, a mirror across the kite's axis (see FLIP_DART):
the shapes are the same either way, only some colourings change.
"""
import math
from functools import lru_cache
import numpy as np

TILE_EDGE = 3.0      # inches, short side of the subway tile
TILE_GROUT = 1 / 8   # long-side joint; the short-end joint is twice this
TILE_KERF = 1 / 8    # saw kerf between the two halves of a kite

ALPHA = math.atan(0.5)
ALPHA_DEG = math.degrees(ALPHA)
FLIPDART_IS_IDENTITY = False

# The tiles actually used (names from mksvg.js)
BATH_COLORS = ['#cfcecc',   # weather gray
               '#9eaebe',   # skylight blue
               '#aca8aa']   # darker weathered waltz
BATH_STYLE = 2560            # "perm2560", 3 colours: the "star destroyer"
# placement of the level-2 domino on the 71.5" x 89.5" wall (inches)
WALL_SIZE = (71.5, 89.5)
WALL_MATRIX = np.array([[0.0, -78.125, 74.8125],
                        [78.125, 0.0, -33.375],
                        [0.0, 0.0, 1.0]])


def T(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1.0]])


def R(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def S(sx, sy=None):
    sy = sx if sy is None else sy
    return np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1.0]])


I3 = np.eye(3)
FLIP_RECT = T(2, 0) @ S(-1, 1)
# A flipped dart is its mirror image across the kite's axis, the line from
# its origin vertex through (2, 1) at angle ALPHA.  mksvg.js wrote
# rotate(ALPHA) scale(-1,1) rotate(-ALPHA), which mirrors across the line
# *perpendicular* to the axis and moves the dart out of its slot; plain
# scale(-1,1) mirrors across the y axis, with the same problem.  The axis
# mirror needs scale(1,-1) between the rotations.
FLIP_DART = I3 if FLIPDART_IS_IDENTITY else R(ALPHA_DEG) @ S(1, -1) @ R(-ALPHA_DEG)

# children of a domino: (num, transform, flip-flag); 0-7 dominoes, 8-12 darts
RECT_CENTER = (0, T(4, 3) @ R(-2 * ALPHA_DEG), True)
RECT_HALF = [
    (1, T(1, 0), True),
    (2, T(0, 2) @ R(-90), False),
    (3, T(0, 4) @ R(-90), True),
    (4, T(0, 4), False),
    (5, T(2, 4), True),
    (6, T(4, 3) @ R(-2 * ALPHA_DEG) @ T(0, 1), False),
    (7, T(4, 3) @ R(-2 * ALPHA_DEG) @ T(1, 2), False),
    (8, T(5, 0) @ S(-1, 1), True),
    (9, T(3, 1) @ S(-1, 1), True),
    (10, T(1, 2) @ S(-1, 1) @ R(90), True),
    (11, T(2, 4) @ S(1, -1), True),
    (12, T(4, 3) @ S(-1, 1) @ R(90), True),
]
RECT_OTHER_HALF = T(10, 5) @ R(180)

# children of a dart: 0-12 darts, 13-24 dominoes (the second half reflected)
DART_TOP = [(0, I3, False), (1, T(2, 1), False), (2, T(6, 3) @ R(180), False),
            (3, T(8, 4) @ R(180), False), (4, T(8, 4), False)]


def dart_half(h):
    return [(5 + 4 * h, T(4, 2) @ R(-90), False), (6 + 4 * h, T(5, 0), False),
            (7 + 4 * h, T(7, 1), False), (8 + 4 * h, T(9, 2) @ R(90), False),
            (13 + 6 * h, T(2, 0), False), (14 + 6 * h, T(7, 0), False),
            (15 + 6 * h, T(9, 2) @ R(-90), True), (16 + 6 * h, T(9, 4) @ R(-90), False),
            (17 + 6 * h, T(4, 3), False), (18 + 6 * h, T(5, 4), False)]


DART_HALF1 = R(2 * ALPHA_DEG) @ S(1, -1)


class Style:
    def __init__(self, perm, ncolors):
        self.perm, self.n = perm, ncolors

    def bit(self, k):
        return (self.perm >> k) & 1


def _child(style, level, flip, base, num, f, is_rect, bitnum):
    c = base + style.bit(bitnum)
    if flip:
        f = not f
    sub = rect_node(style, level - 1, f, c) if is_rect else dart_node(style, level - 1, f, c)
    if flip:
        F = FLIP_RECT if is_rect else FLIP_DART
        sub = [(F @ M, k, cc) for M, k, cc in sub]
    return sub


def _place(M, items):
    return [(M @ m, k, c) for m, k, c in items]


@lru_cache(maxsize=None)
def _rect_def(style, level, flip, base):
    if level == 0:
        return [(I3, 'domino', base)]
    out = []
    num, X, f = RECT_CENTER
    out += _place(X, _child(style, level, flip, base, num, f, True, num))
    half = []
    for num, X, f in RECT_HALF:
        half += _place(X, _child(style, level, flip, base, num, f, num < 8, num))
    out += half + _place(RECT_OTHER_HALF, half)
    return _place(S(0.2), out)


@lru_cache(maxsize=None)
def _dart_def(style, level, flip, base):
    if level == 0:
        return [(I3, 'dart', base)]
    out = []
    for num, X, f in DART_TOP:
        out += _place(X, _child(style, level, flip, base, num, f, False, num + 13))
    for h in (0, 1):
        half = []
        for num, X, f in dart_half(h):
            half += _place(X, _child(style, level, flip, base, num, f, num > 12, num + 13))
        out += _place(DART_HALF1, half) if h else half
    return _place(S(0.2), out)


def rect_node(style, level, flip, base):
    items = _rect_def(style, level, flip, base)
    return _place(FLIP_RECT, items) if flip else items


def dart_node(style, level, flip, base):
    items = _dart_def(style, level, flip, base)
    return _place(FLIP_DART, items) if flip else items


# ---- leaf shapes, with grout (cell units) ----
_g = TILE_GROUT / (TILE_EDGE + TILE_GROUT)
_e = TILE_EDGE / (TILE_EDGE + TILE_GROUT)
_k = TILE_KERF / (TILE_EDGE + TILE_GROUT)
_kx = (_k / 2) * math.sqrt(5)
_ky = (_k / 2) * (math.sqrt(5) / 2)


def leaf_polygons(kind, grout=True):
    if not grout:
        if kind == 'domino':
            return [[(0, 0), (2, 0), (2, 1), (0, 1)]]
        x0, y0 = 2 * math.cos(2 * ALPHA), 2 * math.sin(2 * ALPHA)
        return [[(0, 0), (2, 0), (2, 1), (x0, y0)]]
    g, e = _g, _e
    if kind == 'domino':
        return [[(g, g / 2), (g + 2 * e, g / 2), (g + 2 * e, g / 2 + e), (g, g / 2 + e)]]
    t1 = [(g + _kx, g / 2), (g + 2 * e, g / 2), (g + 2 * e, g / 2 + e - _ky)]
    t2 = [(g + _kx, g / 2), (g + 2 * e, g / 2), (g + 2 * e, g / 2 - (e - _ky))]
    Rm = T(g, g / 2) @ R(2 * ALPHA_DEG) @ T(-g, -g / 2)
    t2 = [tuple((Rm @ np.array([x, y, 1]))[:2]) for x, y in t2]
    return [t1, t2]


def tiles(perm=BATH_STYLE, ncolors=3, level=2, matrix=None, grout=True, color_offset=0):
    """Yield (kind, colour_index, [polygon, ...]) for every physical piece."""
    style = Style(perm, ncolors)
    M0 = WALL_MATRIX if matrix is None else matrix
    for M, kind, c in rect_node(style, level, False, 0):
        Mt = M0 @ M
        polys = []
        for poly in leaf_polygons(kind, grout):
            P = np.array([[x, y, 1.0] for x, y in poly]).T
            Q = (Mt @ P)[:2].T
            polys.append([tuple(q) for q in Q])
        yield kind, (c + color_offset) % ncolors, polys


def on(*bits):
    return sum(1 << b for b in bits)


# Colourings explored in mksvg.js (STYLES), with Scott's notes; '*' = favourite
GALLERY = [
    (2560, 'kites', True),
    (on(0, 1, 2, 6, 7, 8, 9), 's hook', True),
    (on(0, 1, 6, 7, 8), 'massachusetts', False),
    (on(0, 1, 6, 8), 'whip', True),
    (on(0, 6, 7, 10, 3), 'spring', False),
    (on(0, 6, 7, 9, 10, 3), "samson's columns", False),
    (62, 'triple block outline', True),
    (127, 'triple block outline w/ center', False),
    (128, 'figure eight-ish', False),
    (on(9, 10), 'chomp chomp', False),
    (253952, 'tetris Z piece', True),
    (on(14, 15, 18, 22, 13, 26, 32), 'rocket ships', True),
    (on(0, 5, 6, 11, 12), 'simple worms', True),
    (on(0, 5, 6, 11, 12, 4), 'bracket worms', True),
    (on(16, 17, 21, 25), 'simple stars', False),
    (on(0, 12, 8, 1), 'z snake', True),
    (on(0, 6, 8, 12), 'worms 2', False),
    (on(0, 6, 8, 12, 19, 23, 16, 31, 37), 'worms 2e', True),
    (on(0, 6, 12, 34, 35, 17, 4, 5), 'worms 3', True),
]


def level1_children(kind, perm=BATH_STYLE, ncolors=2):
    """The 25 pieces of one inflated domino or kite, in the parent's local
    coordinates (no grout), with the child number used by the colouring
    bit-mask (0-12 inside a domino, 13-37 inside a kite) and the colour
    the given style assigns."""
    node = rect_node if kind == 'domino' else dart_node
    rng = range(0, 13) if kind == 'domino' else range(13, 38)
    base = node(Style(0, 2), 1, False, 0)
    nums = [None] * len(base)
    for k in rng:
        for i, (M, kk, c) in enumerate(node(Style(1 << k, 2), 1, False, 0)):
            if c == 1:
                nums[i] = k
    cols = node(Style(perm, ncolors), 1, False, 0)
    out = []
    for (M, kk, _), n, (_, _, c) in zip(base, nums, cols):
        poly = [tuple((M @ np.array([x, y, 1.0]))[:2]) for x, y in leaf_polygons(kk, False)[0]]
        out.append((n, kk, c % ncolors, poly))
    return out
