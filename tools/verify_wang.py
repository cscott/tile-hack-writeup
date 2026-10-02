#!/usr/bin/env python3
"""Check wangtiles.py against the tiling Scott actually used.

    python3 tools/verify_wang.py /path/to/tile-hack

Compares the Python solver's 21 x 27 tiling with the tile placements in
wang3.svg (etched pattern) and wang3-grout.svg (cutting guide), and checks
that the top row marks exactly the primes.
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import wangtiles as wt


def placements(path):
    s = open(path).read()
    i = s.find('inkscape:label="Tiles"')
    j = s.find('inkscape:label="Grid"')
    out = {}
    for u in re.findall(r'<use\b[^>]*>', s[i:j]):
        h = int(re.search(r'href="#tile(\d+)"', u).group(1))
        x = int(float(re.search(r'\bx="([^"]*)"', u).group(1)))
        y = int(float(re.search(r'\by="([^"]*)"', u).group(1)))
        out[(x, y)] = h
    return out


def main(tilehack):
    g = wt.bathroom_grid()
    ok = True
    for name in ('wang3.svg', 'wang3-grout.svg'):
        ref = placements(os.path.join(tilehack, name))
        same = len(ref) == g.w * g.h and all(g.g[x][y].index == t for (x, y), t in ref.items())
        print(f'{name}: {len(ref)} tiles, {"identical" if same else "DIFFERENT"}')
        ok &= same
    # a prime is marked by edge colour 5 (auburn, thick etched line) under the top row
    marked = [x + 1 for x in range(g.w) if g.g[x][0].bottom == 5]
    primes = [n for n in range(1, g.w + 1) if wt.is_prime(n)]
    print('marked prime:', marked, 'OK' if marked == primes else f'expected {primes}')
    return ok and marked == primes


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[1]) else 1)
