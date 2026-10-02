"""The hat (aperiodic 'einstein' monotile) tiling, by substitution.

A Python port of the metatile construction in Craig S. Kaplan's hatviz
(https://github.com/isohedral/hatviz, BSD 3-Clause, (c) 2023 Craig S. Kaplan),
after Smith, Myers, Kaplan & Goodman-Strauss, "An aperiodic monotile" (2023).
Each hat is returned as an affine transform of the base hat outline plus a
label; label 'H1' (and only it) is the reflected hat.
"""
import math

R3 = math.sqrt(3)
HR3 = R3 / 2
IDENT = (1, 0, 0, 0, 1, 0)


def pt(x, y):
    return (x, y)


def hexpt(x, y):
    return (x + 0.5 * y, HR3 * y)


def inv(T):
    det = T[0] * T[4] - T[1] * T[3]
    return (T[4] / det, -T[1] / det, (T[1] * T[5] - T[2] * T[4]) / det,
            -T[3] / det, T[0] / det, (T[2] * T[3] - T[0] * T[5]) / det)


def mul(A, B):
    return (A[0] * B[0] + A[1] * B[3], A[0] * B[1] + A[1] * B[4], A[0] * B[2] + A[1] * B[5] + A[2],
            A[3] * B[0] + A[4] * B[3], A[3] * B[1] + A[4] * B[4], A[3] * B[2] + A[4] * B[5] + A[5])


def padd(p, q):
    return (p[0] + q[0], p[1] + q[1])


def psub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def trot(a):
    c, s = math.cos(a), math.sin(a)
    return (c, -s, 0, s, c, 0)


def ttrans(x, y):
    return (1, 0, x, 0, 1, y)


def rot_about(p, a):
    return mul(ttrans(*p), mul(trot(a), ttrans(-p[0], -p[1])))


def tpt(M, P):
    return (M[0] * P[0] + M[1] * P[1] + M[2], M[3] * P[0] + M[4] * P[1] + M[5])


def match_seg(p, q):
    return (q[0] - p[0], p[1] - q[1], p[0], q[1] - p[1], q[0] - p[0], p[1])


def match_two(p1, q1, p2, q2):
    return mul(match_seg(p2, q2), inv(match_seg(p1, q1)))


def intersect(p1, q1, p2, q2):
    d = (q2[1] - p2[1]) * (q1[0] - p1[0]) - (q2[0] - p2[0]) * (q1[1] - p1[1])
    uA = ((q2[0] - p2[0]) * (p1[1] - p2[1]) - (q2[1] - p2[1]) * (p1[0] - p2[0])) / d
    return (p1[0] + uA * (q1[0] - p1[0]), p1[1] + uA * (q1[1] - p1[1]))


HAT = [hexpt(0, 0), hexpt(-1, -1), hexpt(0, -2), hexpt(2, -2), hexpt(2, -1), hexpt(4, -2),
       hexpt(5, -1), hexpt(4, 0), hexpt(3, 0), hexpt(2, 2), hexpt(0, 3), hexpt(0, 2), hexpt(-1, 2)]


class Hat:
    def __init__(self, label):
        self.label = label

    def hats(self, T):
        yield T, self.label


class Meta:
    def __init__(self, shape, width):
        self.shape = list(shape)
        self.width = width
        self.children = []

    def add(self, T, geom):
        self.children.append([T, geom])

    def eval_child(self, n, i):
        T, g = self.children[n]
        return tpt(T, g.shape[i])

    def recentre(self):
        cx = sum(p[0] for p in self.shape) / len(self.shape)
        cy = sum(p[1] for p in self.shape) / len(self.shape)
        self.shape = [(p[0] - cx, p[1] - cy) for p in self.shape]
        M = ttrans(-cx, -cy)
        for ch in self.children:
            ch[0] = mul(M, ch[0])

    def hats(self, T):
        for S, g in self.children:
            yield from g.hats(mul(T, S))


H1_HAT, H_HAT, T_HAT, P_HAT, F_HAT = Hat('H1'), Hat('H'), Hat('T'), Hat('P'), Hat('F')


def _H_init():
    o = [pt(0, 0), pt(4, 0), pt(4.5, HR3), pt(2.5, 5 * HR3), pt(1.5, 5 * HR3), pt(-0.5, HR3)]
    m = Meta(o, 2)
    m.add(match_two(HAT[5], HAT[7], o[5], o[0]), H_HAT)
    m.add(match_two(HAT[9], HAT[11], o[1], o[2]), H_HAT)
    m.add(match_two(HAT[5], HAT[7], o[3], o[4]), H_HAT)
    m.add(mul(ttrans(2.5, HR3), mul((-0.5, -HR3, 0, HR3, -0.5, 0), (0.5, 0, 0, 0, -0.5, 0))), H1_HAT)
    return m


def _T_init():
    m = Meta([pt(0, 0), pt(3, 0), pt(1.5, 3 * HR3)], 2)
    m.add((0.5, 0, 0.5, 0, 0.5, HR3), T_HAT)
    return m


def _P_init():
    m = Meta([pt(0, 0), pt(4, 0), pt(3, 2 * HR3), pt(-1, 2 * HR3)], 2)
    m.add((0.5, 0, 1.5, 0, 0.5, HR3), P_HAT)
    m.add(mul(ttrans(0, 2 * HR3), mul((0.5, HR3, 0, -HR3, 0.5, 0), (0.5, 0, 0, 0, 0.5, 0))), P_HAT)
    return m


def _F_init():
    m = Meta([pt(0, 0), pt(3, 0), pt(3.5, HR3), pt(3, 2 * HR3), pt(-1, 2 * HR3)], 2)
    m.add((0.5, 0, 1.5, 0, 0.5, HR3), F_HAT)
    m.add(mul(ttrans(0, 2 * HR3), mul((0.5, HR3, 0, -HR3, 0.5, 0), (0.5, 0, 0, 0, 0.5, 0))), F_HAT)
    return m


RULES = [['H'], [0, 0, 'P', 2], [1, 0, 'H', 2], [2, 0, 'P', 2], [3, 0, 'H', 2], [4, 4, 'P', 2],
         [0, 4, 'F', 3], [2, 4, 'F', 3], [4, 1, 3, 2, 'F', 0], [8, 3, 'H', 0], [9, 2, 'P', 0],
         [10, 2, 'H', 0], [11, 4, 'P', 2], [12, 0, 'H', 2], [13, 0, 'F', 3], [14, 2, 'F', 1],
         [15, 3, 'H', 4], [8, 2, 'F', 1], [17, 3, 'H', 0], [18, 2, 'P', 0], [19, 2, 'H', 2],
         [20, 4, 'F', 3], [20, 0, 'P', 2], [22, 0, 'H', 2], [23, 4, 'F', 3], [23, 0, 'F', 3],
         [16, 0, 'P', 2], [9, 4, 0, 2, 'T', 2], [4, 0, 'F', 3]]


def construct_patch(H, T, P, F):
    ret = Meta([], H.width)
    shapes = {'H': H, 'T': T, 'P': P, 'F': F}
    for r in RULES:
        if len(r) == 1:
            ret.add(IDENT, shapes[r[0]])
        elif len(r) == 4:
            Tc, g = ret.children[r[0]]
            poly = g.shape
            P_ = tpt(Tc, poly[(r[1] + 1) % len(poly)])
            Q_ = tpt(Tc, poly[r[1]])
            n = shapes[r[2]]
            ret.add(match_two(n.shape[r[3]], n.shape[(r[3] + 1) % len(n.shape)], P_, Q_), n)
        else:
            TP, gP = ret.children[r[0]]
            TQ, gQ = ret.children[r[2]]
            P_ = tpt(TQ, gQ.shape[r[3]])
            Q_ = tpt(TP, gP.shape[r[1]])
            n = shapes[r[4]]
            ret.add(match_two(n.shape[r[5]], n.shape[(r[5] + 1) % len(n.shape)], P_, Q_), n)
    return ret


def construct_metatiles(patch):
    bps1 = patch.eval_child(8, 2)
    bps2 = patch.eval_child(21, 2)
    rbps = tpt(rot_about(bps1, -2.0 * math.pi / 3.0), bps2)
    p72 = patch.eval_child(7, 2)
    p252 = patch.eval_child(25, 2)
    llc = intersect(bps1, rbps, patch.eval_child(6, 2), p72)
    w = psub(patch.eval_child(6, 2), llc)
    nH = [llc, bps1]
    w = tpt(trot(-math.pi / 3), w)
    nH.append(padd(nH[1], w))
    nH.append(patch.eval_child(14, 2))
    w = tpt(trot(-math.pi / 3), w)
    nH.append(psub(nH[3], w))
    nH.append(patch.eval_child(6, 2))
    new_H = Meta(nH, patch.width * 2)
    for ch in [0, 9, 16, 27, 26, 6, 1, 8, 10, 15]:
        new_H.add(*patch.children[ch])
    new_P = Meta([p72, padd(p72, psub(bps1, llc)), bps1, llc], patch.width * 2)
    for ch in [7, 2, 3, 4, 28]:
        new_P.add(*patch.children[ch])
    new_F = Meta([bps2, patch.eval_child(24, 2), patch.eval_child(25, 0), p252,
                  padd(p252, psub(llc, bps1))], patch.width * 2)
    for ch in [21, 20, 22, 23, 24, 25]:
        new_F.add(*patch.children[ch])
    AAA = nH[2]
    BBB = padd(nH[1], psub(nH[4], nH[5]))
    CCC = tpt(rot_about(BBB, -math.pi / 3), AAA)
    new_T = Meta([BBB, CCC, AAA], patch.width * 2)
    new_T.add(*patch.children[11])
    for m in (new_H, new_P, new_F, new_T):
        m.recentre()
    return [new_H, new_T, new_P, new_F]


def hat_tiling(levels=4):
    """All hats of a patch: [(transform, label)], transforms applied to HAT."""
    tiles = [_H_init(), _T_init(), _P_init(), _F_init()]
    for _ in range(levels - 1):
        tiles = construct_metatiles(construct_patch(*tiles))
    return list(construct_patch(*tiles).hats(IDENT))


def is_reflected(T):
    return T[0] * T[4] - T[1] * T[3] < 0


# --------------------------------------------------------------- kites and triangles
# The hat is 8 kites of the deltoidal trihexagonal tiling.  In these
# coordinates hexagon centres lie on hexpt(0,0) + Z*hexpt(2,2) + Z*hexpt(-2,4);
# a kite is (hex centre H, edge midpoint M1, triangle centre T, midpoint M2)
# with |HM| = sqrt3 (long), |MT| = 1 (short) and right angles at M1, M2.
def _e(deg, r):
    return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))


def _hat_kites():
    A, B = hexpt(2, 2), hexpt(-2, 4)
    hat = HAT
    out = []

    def inside(p):                      # point in polygon (ray casting)
        x, y = p
        c = False
        for k in range(len(hat)):
            (x1, y1), (x2, y2) = hat[k], hat[(k + 1) % len(hat)]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                c = not c
        return c
    for i in range(-4, 5):
        for j in range(-4, 5):
            H = (i * A[0] + j * B[0], i * A[1] + j * B[1])
            for k in range(6):
                M1, T, M2 = (padd(H, _e(60 * k + d, r)) for d, r in ((-30, R3), (0, 2), (30, R3)))
                cen = ((H[0] + M1[0] + T[0] + M2[0]) / 4, (H[1] + M1[1] + T[1] + M2[1]) / 4)
                if inside(cen):
                    out.append((H, M1, T, M2))
    assert len(out) == 8
    return out


HAT_KITES = _hat_kites()
# each kite as its two right triangles (H, M, T), right angle at M; the two
# are mirror images, so one comes from a tile cut on each diagonal
HAT_TRIANGLES = [tri for (H, M1, T, M2) in HAT_KITES for tri in ((H, M1, T), (H, M2, T))]


def inset_triangle(tri, d):
    """Shrink a triangle uniformly by d on every side (about its incentre);
    the result is similar, so the tile's proportions don't change."""
    (ax, ay), (bx, by), (cx, cy) = tri
    a = math.dist(tri[1], tri[2])
    b = math.dist(tri[0], tri[2])
    c = math.dist(tri[0], tri[1])
    s = a + b + c
    ix, iy = (a * ax + b * bx + c * cx) / s, (a * ay + b * by + c * cy) / s
    area = abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay)) / 2
    r = 2 * area / s
    f = (r - d) / r
    return [(ix + f * (x - ix), iy + f * (y - iy)) for x, y in tri]


# --------------------------------------------------------------- laying hats in 60-degree rhombus tile
# Splitting every kite in half gives right triangles (legs 1 : sqrt3).  The four
# whose right angles meet at an edge midpoint M of the kite grid form a 60-degree
# rhombus of side 2 (diagonals 2 and 2*sqrt3): the rhombille, or "tumbling
# blocks", tiling.  So the whole hat tiling can be laid in rhombus tile, cutting
# only where colours meet:
#   rhombus      4 triangles, uncut
#   equilateral  2 triangles sharing a long leg  (rhombus cut on its short diagonal)
#   obtuse       2 triangles sharing a short leg (rhombus cut on its long diagonal)
#   right        1 triangle                      (rhombus cut on both diagonals)

def _key(p):
    return (round(p[0], 6), round(p[1], 6))


def world_triangles(hats):
    """[(colour, (H, M, T))] for every half-kite, in world coordinates;
    colour is 'blue' for reflected hats and 'light' otherwise."""
    out = []
    for T, label in hats:
        col = 'blue' if is_reflected(T) else 'light'
        for tri in HAT_TRIANGLES:
            out.append((col, tuple(tpt(T, p) for p in tri)))
    return out


def rhombus_layout(hats, prefer='equilateral'):
    """Group half-kites into rhombus-tile pieces, never mixing colours.
    Returns [(colour, kind, polygon, handedness)]; handedness is +1/-1 for a
    single right triangle, else 0."""
    slots = {}
    for col, (H, M, T) in world_triangles(hats):
        slots.setdefault(_key(M), []).append((col, H, M, T))
    pieces = []

    def single(t):
        col, H, M, T = t
        hand = 1 if ((H[0] - M[0]) * (T[1] - M[1]) - (H[1] - M[1]) * (T[0] - M[0])) > 0 else -1
        pieces.append((col, 'right', [H, M, T], hand))

    def pair(a, b):
        # two triangles sharing a leg from M: union is a triangle without M
        pts = {}
        for _, H, M, T in (a, b):
            for p in (H, T):
                pts[_key(p)] = p
        shared_long = _key(a[1]) == _key(b[1])          # same H: shared leg M-H
        kind = 'equilateral' if shared_long else 'obtuse'
        far = [a[1], a[3], b[1] if shared_long else b[3]]
        poly = list(pts.values())
        pieces.append((a[0], kind, poly, 0))

    for m, ts in slots.items():
        if len(ts) != 4:
            for t in ts:
                single(t)
            continue
        Mx, My = ts[0][2]
        ts.sort(key=lambda t: math.atan2((t[1][1] + t[3][1]) / 2 - My, (t[1][0] + t[3][0]) / 2 - Mx))
        cols = [t[0] for t in ts]
        if len(set(cols)) == 1:
            rh = []
            for t in ts:                                 # outer vertices in angular order
                for p in (t[1], t[3]):
                    if all(_key(p) != _key(q) for q in rh):
                        rh.append(p)
            rh.sort(key=lambda p: math.atan2(p[1] - My, p[0] - Mx))
            pieces.append((cols[0], 'rhombus', rh, 0))
            continue
        used = [False] * 4
        # 2+2 splits first, then a pair inside a 3+1 split
        pairs = [(i, (i + 1) % 4) for i in range(4)]
        splits = [((0, 1), (2, 3)), ((1, 2), (3, 0))]
        done = False
        for (a, b), (c, d) in splits:
            if cols[a] == cols[b] and cols[c] == cols[d]:
                pair(ts[a], ts[b]); pair(ts[c], ts[d]); done = True
                break
        if done:
            continue
        cand = [(i, j) for i, j in pairs if cols[i] == cols[j]]
        if cand:
            def kind_of(i, j):
                return 'equilateral' if _key(ts[i][1]) == _key(ts[j][1]) else 'obtuse'
            cand.sort(key=lambda ij: kind_of(*ij) != prefer)
            i, j = cand[0]
            pair(ts[i], ts[j]); used[i] = used[j] = True
        for k in range(4):
            if not used[k]:
                single(ts[k])
    return pieces


def inset_polygon(poly, d):
    """Shrink a convex polygon by d on every side (mitred corners)."""
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    poly = sorted(poly, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))   # CCW
    lines = []
    for k in range(n):
        (x1, y1), (x2, y2) = poly[k], poly[(k + 1) % n]
        L = math.hypot(x2 - x1, y2 - y1)
        nx, ny = -(y2 - y1) / L, (x2 - x1) / L                         # inward for CCW
        lines.append(((x1 + nx * d, y1 + ny * d), (x2 + nx * d, y2 + ny * d)))
    out = []
    for k in range(n):
        out.append(intersect(*lines[k - 1], *lines[k]))
    return out


def layout_stats(pieces):
    """Tiles and cuts per colour, buying whole rhombi.  Halves come two to a
    rhombus (one cut); right triangles four to a rhombus (two cuts), two of
    each hand."""
    from collections import Counter
    out = {}
    for col in sorted({p[0] for p in pieces}):
        c = Counter(p[1] for p in pieces if p[0] == col)
        hands = Counter(p[3] for p in pieces if p[0] == col and p[1] == 'right')
        right_tiles = math.ceil(max(hands[1], hands[-1]) / 2) if c['right'] else 0
        tiles = c['rhombus'] + math.ceil(c['equilateral'] / 2) + math.ceil(c['obtuse'] / 2) + right_tiles
        cuts = math.ceil(c['equilateral'] / 2) + math.ceil(c['obtuse'] / 2) + 2 * right_tiles
        out[col] = dict(pieces=dict(c), tiles=tiles, cuts=cuts)
    return out


# ------------------------------------------------------------------ fewest cuts
# rhombus_layout() above only ever groups the four triangles around one M.  A
# rhombus tile can also sit *across* a kite axis H-T: the two equilateral
# halves on either side of the axis (around the kite's two midpoints M, M')
# make a rhombus whose short diagonal is the axis.  With point-to-point cuts
# those are all the pieces there are, since every two-triangle piece is an
# equilateral half (H, T1, T2) or an obtuse half (H1, T, H2), and
#   equilateral + equilateral across T1-T2  = rhombus around M
#   equilateral + equilateral across H-T    = rhombus across the axis H-T
#   obtuse + obtuse across H1-H2            = rhombus around M
#   anything else                           = not convex, or not a rhombus.
# Cuts are counted per piece: a half costs 1/2 (two halves per cut), a right
# triangle 3/4 (four per three cuts).  In quarter-cuts:
CUT_COST = {'rhombus': 0, 'offset rhombus': 0, 'equilateral': 2, 'obtuse': 2, 'right': 3}


def candidate_pieces(hats):
    """Every single-colour piece that can be cut from a 60-degree rhombus by
    point-to-point cuts.  Returns (triangles, pieces): triangles is
    [(colour, (H, M, T))]; each piece is (kind, [triangle indices])."""
    tris = world_triangles(hats)
    k = lambda p: _key(p)
    by_m, by_hm, by_tm, by_ht = {}, {}, {}, {}
    for i, (col, (H, M, T)) in enumerate(tris):
        by_m.setdefault(k(M), []).append(i)
        by_hm.setdefault((k(H), k(M)), []).append(i)
        by_tm.setdefault((k(T), k(M)), []).append(i)
        by_ht.setdefault((k(H), k(T)), []).append(i)
    same = lambda ids: len({tris[i][0] for i in ids}) == 1
    pieces = [('right', [i]) for i in range(len(tris))]
    pieces += [('rhombus', ids) for ids in by_m.values() if len(ids) == 4 and same(ids)]
    pieces += [('equilateral', ids) for ids in by_hm.values() if len(ids) == 2 and same(ids)]
    pieces += [('obtuse', ids) for ids in by_tm.values() if len(ids) == 2 and same(ids)]
    for (h, t), kite in by_ht.items():               # the kite's two halves, one per M
        if len(kite) != 2:
            continue
        ids = [j for i in kite for j in by_hm[(h, k(tris[i][1][1]))]]
        if len(ids) == 4 and same(ids):
            pieces.append(('offset rhombus', ids))
    return tris, pieces


def _piece_polygon(tris, ids):
    ms = {_key(tris[i][1][1]) for i in ids}
    pts = {}
    for i in ids:
        for p in tris[i][1]:
            if len(ids) == 1 or _key(p) not in ms:
                pts[_key(p)] = p
    pts = list(pts.values())
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def _hand(tri):
    H, M, T = tri
    return 1 if ((H[0] - M[0]) * (T[1] - M[1]) - (H[1] - M[1]) * (T[0] - M[0])) > 0 else -1


def optimal_layout(hats, time_limit=120, verbose=False):
    """Exact cover of the half-kites by rhombus-tile pieces, solved with
    OR-Tools CP-SAT in three rounds: fewest cuts (CUT_COST), then fewest
    obtuse halves (the long skinny cut is the one most likely to crack), then
    fewest offset rhombi (so the light field stays plain tumbling blocks).
    Returns [(colour, kind, polygon, handedness)] like rhombus_layout()."""
    from ortools.sat.python import cp_model
    tris, cands = candidate_pieces(hats)
    m = cp_model.CpModel()
    x = [m.NewBoolVar('') for _ in cands]
    cover = [[] for _ in tris]
    for v, (kind, ids) in zip(x, cands):
        for i in ids:
            cover[i].append(v)
    for vs in cover:
        m.AddExactlyOne(vs)
    goals = [
        sum(CUT_COST[kind] * v for v, (kind, _) in zip(x, cands) if CUT_COST[kind]),
        sum(v for v, (kind, _) in zip(x, cands) if kind == 'obtuse'),
        sum(v for v, (kind, _) in zip(x, cands) if kind == 'offset rhombus'),
    ]
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    for g in goals:
        m.Minimize(g)
        st = solver.Solve(m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError('no layout found')
        best = round(solver.ObjectiveValue())
        if verbose:
            print('optimal' if st == cp_model.OPTIMAL else 'feasible', best)
        m.ClearHints()
        for v in x:
            m.AddHint(v, solver.Value(v))
        m.Add(g <= best)
    out = []
    for v, (kind, ids) in zip(x, cands):
        if solver.Value(v):
            col = tris[ids[0]][0]
            out.append((col, kind, _piece_polygon(tris, ids),
                        _hand(tris[ids[0]][1]) if kind == 'right' else 0))
    return out


def cut_stats(pieces):
    """Pieces and cuts per colour by the CUT_COST metric (halves 1/2 cut,
    right triangles 3/4), and the right triangles' hand balance."""
    from collections import Counter
    out = {}
    for col in sorted({p[0] for p in pieces}):
        c = Counter(p[1] for p in pieces if p[0] == col)
        hands = Counter(p[3] for p in pieces if p[0] == col and p[1] == 'right')
        out[col] = dict(pieces=dict(c), cuts=sum(CUT_COST[k] * n for k, n in c.items()) / 4,
                        left=hands[-1], right=hands[1])
    return out
