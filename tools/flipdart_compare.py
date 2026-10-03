"""Compare dart-flip variants of mksvg.js / kitedomino.py.  Writes flipdart.png."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly
import kitedomino as kd

A = kd.ALPHA_DEG
FLIPS = {
    'identity': kd.I3,                                        # as built (typo discarded)
    'literal': kd.R(A) @ kd.S(-1, 1) @ kd.R(-A),              # what the template meant
    'axis': kd.R(A) @ kd.S(1, -1) @ kd.R(-A),                 # mirror across the kite's axis
                                                              # (kitedomino with FLIPDART_IS_IDENTITY = False)
}
COL = ['#cfcecc', '#9eaebe']


def pieces(flip, perm):
    kd.FLIP_DART = FLIPS[flip]
    kd._rect_def.cache_clear()
    kd._dart_def.cache_clear()
    out = list(kd.tiles(perm, 2, level=2, matrix=np.eye(3), grout=False))
    kd.FLIP_DART = kd.I3
    kd._rect_def.cache_clear()
    kd._dart_def.cache_clear()
    return out


def key(k, c, ps):
    m = np.mean(ps[0], 0)
    return (round(float(m[0]), 5), round(float(m[1]), 5), k)


def draw(ax, items, title, alpha=1.0, highlight=()):
    for k, c, ps in items:
        hl = key(k, c, ps) in highlight
        for p in ps:
            ax.add_patch(MPoly(p, closed=True, fc=COL[c], ec='#d0342c' if hl else '#555555',
                               lw=1.6 if hl else 0.3, alpha=alpha, zorder=3 if hl else 2))
    ax.add_patch(MPoly([(0, 0), (2, 0), (2, 1), (0, 1)], closed=True, fill=False,
                       ec='#3F536E', lw=1.4, zorder=4))
    ax.set_xlim(-0.35, 2.35)
    ax.set_ylim(1.35, -0.35)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=10, family='serif', color='#3F536E')


fig, axs = plt.subplots(2, 2, figsize=(12, 7.2))
draw(axs[0, 0], pieces('identity', 2560),
     '(a) as built: flipDart transform discarded\nkites {9, 11}, the wall')
draw(axs[0, 1], pieces('literal', 2560),
     '(b) template fixed literally: rotate(α) scale(−1,1) rotate(−α)\n'
     'mirrors across the line perpendicular to the kite axis: darts leave their slots',
     alpha=0.55)
w_id = pieces('identity', kd.on(0, 6, 12, 34, 35, 17, 4, 5))
w_ax = pieces('axis', kd.on(0, 6, 12, 34, 35, 17, 4, 5))
k_id = {key(*x): x[1] for x in w_id}
changed = {key(*x) for x in w_ax if k_id.get(key(*x)) != x[1]}
draw(axs[1, 0], w_id, '(c) worms 3, as built')
draw(axs[1, 1], w_ax, f'(d) worms 3 with the intended flip, rotate(α) scale(1,−1) rotate(−α)\n'
     f'same shapes; {len(changed)} pieces change colour (red)', highlight=changed)
fig.tight_layout()
fig.savefig('flipdart.png', dpi=140)
print('changed', len(changed))
