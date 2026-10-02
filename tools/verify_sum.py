#!/usr/bin/env python3
"""Check that the addition tiles force S to column A1 + A2, both with the
book's edge types and with edges merged wherever they look alike as drawn
(wangtiles.SUM_LOOKS).

    python3 tools/verify_sum.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import wangtiles as wt


def visual(looks):
    """SUM_TILES with edge types merged wherever they look alike."""
    ids = {}

    def k(e, vert):
        h, v = looks[e]
        base, lines = v if vert else h
        return 0 if base == 'black' else ids.setdefault((vert, base, tuple(lines)), len(ids) + 1)
    return [(k(t, 1), k(r, 0), k(b, 1), k(l, 0), n) for t, r, b, l, n in wt.SUM_TILES]


def s_positions(tiles, a1=4, a2=7, width=18, height=16):
    """Columns where S can stand, given A at a1 and a2."""
    star, A, S, blank = tiles[0], tiles[5], tiles[10], tiles[14]
    rest = [t for t in tiles if t[4] not in ('A', 'S', '*')]
    plain = lambda t: sum(e == tiles[15][0] for e in t[:4]) >= 3
    rest.sort(key=lambda t: not plain(t))
    ok = []
    for s in range(2, width):
        if s in (a1, a2):
            continue
        pins = {(0, 0): star, (a1 - 1, 0): A, (a2 - 1, 0): A, (s - 1, 0): S}
        for x in range(1, width):
            pins.setdefault((x, 0), blank)
        if wt.solve(rest, width, height, pins):
            ok.append(s)
    return ok


if __name__ == '__main__':
    good = True
    for name, tiles in (('edge types', wt.SUM_TILES), ('as drawn', visual(wt.SUM_LOOKS))):
        for a1, a2 in ((4, 7), (3, 5), (2, 6)):
            pos = s_positions(tiles, a1, a2)
            fine = pos == [a1 + a2]
            good &= fine
            print(f'{name}: A at {a1}, {a2} -> S at {pos}', 'OK' if fine else 'NOT FORCED')
    sys.exit(0 if good else 1)
