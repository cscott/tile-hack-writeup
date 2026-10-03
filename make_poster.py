#!/usr/bin/env python3
"""Two-page framed print about the pinwheel tiling in the bathroom.

    python3 make_poster.py            -> pinwheel-tiling.pdf

Page 1: why the pinwheel tiling never repeats.
Page 2: dominoes, kites, and the colourings from github.com/cscott/tile-hack.

Requires: reportlab, numpy, and the FreeSerif fonts (GNU FreeFont).
Geometry lives in pinwheel.py (triangle substitution) and kitedomino.py
(the tile-level kite/domino substitution actually used on the wall).
"""
import math
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

from pinwheel import CH_AFF, subdivide, verts
import kitedomino as kd

# ------------------------------------------------------------------ fonts
FONT_DIR = '/usr/share/fonts/truetype/freefont/'
for name, f in [('Serif', 'FreeSerif.ttf'), ('Serif-Bold', 'FreeSerifBold.ttf'),
                ('Serif-Italic', 'FreeSerifItalic.ttf'),
                ('Serif-BoldItalic', 'FreeSerifBoldItalic.ttf')]:
    pdfmetrics.registerFont(TTFont(name, FONT_DIR + f))
registerFontFamily('Serif', normal='Serif', bold='Serif-Bold',
                   italic='Serif-Italic', boldItalic='Serif-BoldItalic')

# ------------------------------------------------------------------ palette
TILE_GRAY = HexColor(kd.BATH_COLORS[0])   # weather gray   #cfcecc
TILE_BLUE = HexColor(kd.BATH_COLORS[1])   # skylight blue  #9eaebe
TILES = [TILE_GRAY, TILE_BLUE]
GROUT = HexColor('#8E8A85')
PAPER = HexColor('#F5F3EF')
LIGHT = HexColor('#E4E3E0')     # paper-friendly tint of weather gray
BLUE_L = HexColor('#C6D0DB')    # tint of skylight blue
BLUE_D = HexColor('#7489A6')    # shade of skylight blue
SLATE = HexColor('#3F536E')
INK = HexColor('#363B42')
GREY_T = HexColor('#6B6F75')

W, H = letter
TH = math.atan(0.5)
X0, X1 = 72, W - 72
CW = X1 - X0
SIGNATURE = 'C. Scott Ananian · January 2019'


# ------------------------------------------------------------------ helpers
def poly(c, pts, fill=None, stroke=None, lw=0.6):
    p = c.beginPath()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    if fill is not None:
        c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
    c.drawPath(p, fill=fill is not None, stroke=stroke is not None)


body = ParagraphStyle('body', fontName='Serif', fontSize=9.6, leading=12.4,
                      textColor=INK, alignment=TA_JUSTIFY)
small = ParagraphStyle('small', parent=body, fontSize=8.6, leading=10.9)
foot = ParagraphStyle('foot', parent=body, fontSize=7.7, leading=9.5, textColor=GREY_T)


def para(c, text, x, ytop, w, style=body):
    """Draw a paragraph with its top at ytop; return the y of its bottom."""
    p = Paragraph(text, style)
    _, h = p.wrap(w, 1000)
    p.drawOn(c, x, ytop - h)
    return ytop - h


def heading(c, num, text, x, y, w, accent=None):
    c.setFillColor(SLATE)
    c.setFont('Serif-Bold', 10.5)
    label = f'{num}.  ' + ' '.join(text.upper())
    c.drawString(x, y, label)
    tw = c.stringWidth(label, 'Serif-Bold', 10.5)
    c.setStrokeColor(accent or TILE_BLUE)
    c.setLineWidth(0.6)
    c.line(x + tw + 8, y + 3.5, x + w, y + 3.5)


def spaced(c, s, x, y, font, size, track, color):
    c.setFillColor(color)
    c.setFont(font, size)
    widths = [c.stringWidth(ch, font, size) for ch in s]
    cx = x - (sum(widths) + track * (len(s) - 1)) / 2
    for ch, wd in zip(s, widths):
        c.drawString(cx, y, ch)
        cx += wd + track


def place(x, y, size):
    """affine placing the canonical pinwheel triangle (width 2) at width `size`."""
    s = size / 2.0
    return np.array([[s, 0], [0, s]]), np.array([x, y])


def title_block(c, title, subtitle, accent=None, ornament=None):
    """Title, subtitle and a rule with a small ornament in the middle.
    `ornament(c, cx, cy)` draws the ornament; default is a pinwheel triangle."""
    accent = accent or TILE_BLUE
    spaced(c, title, W / 2, 702, 'Serif', 25, 3.2, SLATE)
    c.setFont('Serif-Italic', 11.5)
    c.setFillColor(GREY_T)
    c.drawCentredString(W / 2, 683, subtitle)
    c.setStrokeColor(accent)
    c.setLineWidth(0.6)
    c.line(W / 2 - 110, 671, W / 2 - 12, 671)
    c.line(W / 2 + 12, 671, W / 2 + 110, 671)
    if ornament:
        ornament(c, W / 2, 671)
    else:
        L, t = place(W / 2 - 8, 667.5, 16)
        poly(c, verts(L, t), fill=accent, stroke=SLATE, lw=0.5)


def footer(c, left, accent=None, signature=None):
    fy = 64
    c.setStrokeColor(accent or TILE_BLUE)
    c.setLineWidth(0.5)
    c.line(X0, fy + 12, X1, fy + 12)
    size = 7.6
    while c.stringWidth(left, 'Serif', size) > CW - 140 and size > 6:
        size -= 0.1
    c.setFont('Serif', size)
    c.setFillColor(GREY_T)
    c.drawString(X0, fy, left)
    c.setFont('Serif-Italic', 9.5)
    c.setFillColor(SLATE)
    c.drawRightString(X1, fy - 1, signature or SIGNATURE)


# ------------------------------------------------------------------ frame
OUT, IN = 18, 50
WALL_RATIO = 24                        # border drawn at 1 : WALL_RATIO (<= 24 to fill the page)
WALL_SCALE = 72.0 / WALL_RATIO         # page points per wall inch
WALL_NUDGE = kd.T(0.02727758, -0.00289308)   # final alignment from pinwheel-grout.svg
# The wall is one level-2 domino.  To see more of the tiling around it, draw the
# level-3 domino that has the wall as its child 7 (a non-flipped domino whose
# colour bit is 0 in perm2560, so it is exactly the wall's supertile).  Of the
# candidate children, 7 sits most centrally, so the level-3 supertile covers
# the whole page down to 1:24.
_X7 = next(X for num, X, f in kd.RECT_HALF if num == 7)
BORDER_MATRIX = kd.WALL_MATRIX @ WALL_NUDGE @ np.linalg.inv(kd.S(0.2) @ _X7)
BORDER_LEVEL = 3


def wall_to_page(x, y):
    """wall inches (y down, origin top-left) -> page points, wall centred."""
    wx, wy = kd.WALL_SIZE
    return (W / 2 + WALL_SCALE * (x - wx / 2), H / 2 - WALL_SCALE * (y - wy / 2))


def draw_wall_frame(c):
    """The border is the bathroom wall's tiling (perm2560), extended outward."""
    c.saveState()
    p = c.beginPath()
    p.rect(OUT, OUT, W - 2 * OUT, H - 2 * OUT)
    c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(GROUT)
    c.rect(OUT, OUT, W - 2 * OUT, H - 2 * OUT, stroke=0, fill=1)
    for kind, col, polys in kd.tiles(kd.BATH_STYLE, 2, level=BORDER_LEVEL, matrix=BORDER_MATRIX):
        for pg in polys:
            pts = [wall_to_page(x, y) for x, y in pg]
            xs = [q[0] for q in pts]
            ys = [q[1] for q in pts]
            if max(xs) < OUT or min(xs) > W - OUT or max(ys) < OUT or min(ys) > H - OUT:
                continue
            if min(xs) > IN and max(xs) < W - IN and min(ys) > IN and max(ys) < H - IN:
                continue
            poly(c, pts, fill=TILES[col])
    c.restoreState()
    c.setFillColor(PAPER)
    c.rect(IN, IN, W - 2 * IN, H - 2 * IN, stroke=0, fill=1)
    c.setStrokeColor(SLATE)
    c.setLineWidth(1.2)
    c.rect(IN, IN, W - 2 * IN, H - 2 * IN, stroke=1, fill=0)
    c.setLineWidth(0.5)
    c.rect(IN + 4, IN + 4, W - 2 * IN - 8, H - 2 * IN - 8, stroke=1, fill=0)
    c.setStrokeColor(GROUT)
    c.setLineWidth(0.6)
    c.rect(OUT, OUT, W - 2 * OUT, H - 2 * OUT, stroke=1, fill=0)


def new_page(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    draw_wall_frame(c)


# ------------------------------------------------------------------ page 1 diagrams
def orient_k(Lk):
    """Direction of a tile's long leg as a multiple k of theta (mod 90 deg)."""
    v = Lk @ np.array([1.0, 0.0])
    a = math.atan2(v[1], v[0])
    q = math.pi / 2
    for k in range(-12, 13):
        if abs(((a - k * TH + q / 2) % q) - q / 2) < 1e-7:
            return k
    return 0


def draw_subway(c, x, y, w):
    h = w / 2
    a, b, cc, d = (x, y), (x + w, y), (x + w, y + h), (x, y + h)
    poly(c, [a, b, cc], fill=TILE_BLUE)
    poly(c, [a, cc, d], fill=LIGHT)
    c.setStrokeColor(GROUT)
    c.setLineWidth(0.6)
    c.setDash(2.5, 2.5)
    c.line(x, y + h, x + w, y)          # the other diagonal: the other hand
    c.setDash()
    c.setStrokeColor(SLATE)
    c.setLineWidth(1.2)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setLineWidth(1.0)
    c.line(x, y, x + w, y + h)
    r = 7
    poly(c, [(b[0] - r, b[1]), (b[0] - r, b[1] + r), (b[0], b[1] + r)], stroke=SLATE, lw=0.6)
    rad = 30
    c.setLineWidth(0.6)
    c.arc(x - rad, y - rad, x + rad, y + rad, 0, math.degrees(TH))
    c.setFillColor(INK)
    c.setFont('Serif-Italic', 11)
    c.drawString(x + rad + 3, y + 3.5, 'θ')
    c.setFont('Serif', 11)
    c.drawCentredString(x + w / 2, y - 13, '2')
    c.drawString(x + w + 5, y + h / 2 - 4, '1')
    c.saveState()
    c.translate(x + w / 2, y + h / 2)
    c.rotate(math.degrees(TH))
    c.drawCentredString(14, -12, '√5')
    c.restoreState()


# One shade per tilt k (tile direction k*theta, modulo a quarter-turn), the
# same in every panel; the panel captions carry the key.
TILT_SHADE = {-1: TILE_GRAY, 0: BLUE_L, 1: TILE_BLUE, 2: BLUE_D, 3: HexColor('#5A6F8E')}


def tilt_label(k):
    return {0: '0', 1: 'θ', -1: '−θ'}.get(k, f'{k}θ')


def long_legs(c, tris, lw):
    """Mark each triangle's long leg (its first two vertices) in bold."""
    c.saveState()
    c.setStrokeColor(SLATE)
    c.setLineWidth(lw)
    c.setLineCap(1)
    for pg in tris:
        c.line(*pg[0], *pg[1])
    c.restoreState()


def draw_level1(c, x, y, size):
    """One generation: all five children are tilted by theta.  The two
    unmirrored children form an uncut subway tile, so their shared
    hypotenuse is drawn dashed."""
    L, t = place(x, y, size)
    kids = [verts(L @ l2, L @ t2 + t) for l2, t2 in CH_AFF]
    for pg in kids:
        poly(c, pg, fill=TILT_SHADE[1])
    for pg in kids:
        poly(c, pg, stroke=SLATE, lw=0.7)
    long_legs(c, kids + [verts(L, t)], 2.2)
    a, b = L @ np.array([1.0, 0.0]) + t, L @ np.array([1.6, 0.8]) + t   # children 3 | 4
    c.setStrokeColor(TILT_SHADE[1])
    c.setLineWidth(1.2)
    c.line(*a, *b)
    c.setStrokeColor(SLATE)
    c.setLineWidth(0.6)
    c.setDash(2, 2)
    c.line(*a, *b)
    c.setDash()
    poly(c, verts(L, t), stroke=SLATE, lw=1.2)


def draw_level(c, x, y, size, n):
    """n generations, each tile shaded by its tilt (TILT_SHADE).  Returns
    the tilts present, in increasing order."""
    L, t = place(x, y, size)
    tiles = list(subdivide(L, t, n))
    for Lk, tk, p in tiles:
        poly(c, verts(Lk, tk), fill=TILT_SHADE[orient_k(Lk)])
    for Lk, tk, p in tiles:
        poly(c, verts(Lk, tk), stroke=SLATE, lw=0.35 if n > 2 else 0.5)
    poly(c, verts(L, t), stroke=SLATE, lw=1.1)
    long_legs(c, [verts(Lk, tk) for Lk, tk, p in tiles] + [verts(L, t)], 1.5 if n == 2 else 1.0)
    return sorted({orient_k(Lk) for Lk, tk, p in tiles})


def swatch_caption(c, cx, y, parts, size=8):
    """Centred caption mixing text and shade swatches: parts are strings or
    ('swatch', colour)."""
    font = 'Serif-Italic'
    sw = size * 0.8
    widths = [c.stringWidth(p, font, size) if isinstance(p, str) else sw + 2.5 for p in parts]
    x = cx - sum(widths) / 2
    for p, w in zip(parts, widths):
        if isinstance(p, str):
            c.setFont(font, size)
            c.setFillColor(GREY_T)
            c.drawString(x, y, p)
        else:
            c.setFillColor(p[1])
            c.setStrokeColor(SLATE)
            c.setLineWidth(0.4)
            c.rect(x + 0.5, y - 0.5, sw, sw, stroke=1, fill=1)
        x += w


def tilt_parts(prefix, ks):
    parts = [prefix]
    for i, k in enumerate(ks):
        if i:
            parts.append(' or ' if i == len(ks) - 1 else ', ')
        parts += [('swatch', TILT_SHADE[k]), tilt_label(k)]
    return parts


def draw_dial(c, cx, cy, R, N=72):
    c.setStrokeColor(GROUT)
    c.setLineWidth(0.5)
    c.circle(cx, cy, R, stroke=1, fill=0)
    c.circle(cx, cy, R * 0.32, stroke=1, fill=0)
    for n in range(N, -1, -1):
        a = n * TH
        r0 = R * (0.36 + 0.5 * n / N)
        col = SLATE if n < 6 else (BLUE_D if n < 24 else TILE_BLUE)
        c.setStrokeColor(col)
        c.setLineWidth(1.4 if n < 6 else 0.8)
        c.line(cx + r0 * math.cos(a), cy + r0 * math.sin(a),
               cx + R * math.cos(a), cy + R * math.sin(a))
    c.setFillColor(INK)
    c.setFont('Serif', 8.5)
    for n in range(0, 5):
        a = n * TH
        lab = '0' if n == 0 else ('θ' if n == 1 else f'{n}θ')
        c.drawCentredString(cx + (R + 11) * math.cos(a), cy + (R + 11) * math.sin(a) - 3, lab)
    c.setFont('Serif-Italic', 8)
    c.setFillColor(SLATE)
    c.drawCentredString(cx, cy + 2, 'nθ')
    c.setFont('Serif', 6.5)
    c.drawCentredString(cx, cy - 7, f'n ≤ {N}')


# ------------------------------------------------------------------ page 1
def page_one(c):
    new_page(c)
    title_block(c, 'THE PINWHEEL TILING',
                'a pattern that never repeats, made from ordinary 2 : 1 subway tile')

    # I. one tile
    y = 650
    heading(c, 'I', 'One tile, one cut', X0, y, CW)
    draw_subway(c, X0 + 4, y - 90, 148)
    c.setFont('Serif-Italic', 7.8)
    c.setFillColor(GREY_T)
    c.drawCentredString(X0 + 78, y - 117, 'cut along either diagonal')
    tb = para(c, 'Most aperiodic tilings are impractical to build. Penrose tiles need '
            'golden-ratio proportions and 36° and 72° angles, so they must be custom-made. '
            'The pinwheel tiling needs only a standard 3″ × 6″ subway tile, cut once along '
            'a diagonal; the triangle’s smallest angle is <i>θ</i> = arctan ½ ≈ 26.565°. '
            'There are two diagonals, and cutting along each yields different triangles: left-handed and right-handed. Two same-handed triangles meeting along their hypotenuse pair back up into full tiles; differently-handed triangles meeting along their hypotenuse become kites.<super>†</super>',
         X0 + 182, y - 12, CW - 182)

    # II. five from one
    y = 510
    heading(c, 'II', 'Five from one', X0, y, CW)
    dsz = 128
    gap = (CW - 3 * dsz) / 2
    base = y - 82
    draw_level1(c, X0, base, dsz)
    k2 = draw_level(c, X0 + dsz + gap, base, dsz, 2)
    k3 = draw_level(c, X0 + 2 * (dsz + gap), base, dsz, 3)
    captions = [tilt_parts('one generation: 5 tiles, all tilted ', [1]),
                tilt_parts('two: 25, tilted ', k2),
                tilt_parts('three: 125, tilted ', k3)]
    for i, parts in enumerate(captions):
        swatch_caption(c, X0 + i * (dsz + gap) + dsz / 2, base - 12, parts)
    pb = para(c, 'The 2:1 triangle divides exactly into five copies of itself, each scaled by '
            '1/√5: the altitude from the right angle splits off one, and the rest divides '
            'into four, two of which form an uncut subway tile.<super>‡</super> Enlarge by √5 and repeat: '
            '1 tile becomes 5, then 25, then 125, covering ever larger regions of the plane. This tiling was discovered by John Conway. '
            'Charles Radin (1994) showed that this tiling can be enforced with decorated '
            'copies of the tile and local matching rules.',
         X0, base - 22, CW)

    # III. irrational twist
    y = min(338, pb - 22)
    heading(c, 'III', 'The irrational twist', X0, y, CW)
    dial_w = 112
    steps = [
        '<b>1.</b> Each child’s long leg (marked in bold above) is tilted by exactly '
        '<i>θ</i> from its parent’s; perpendicular directions count as the same. '
        'Three children are mirror images of the parent; two are not.',
        '<b>2.</b> A mirrored tile’s children turn the opposite way from an unmirrored '
        'tile’s, so each generation adds ±<i>θ</i>. After <i>n</i> generations tiles thus '
        'point in directions −(<i>n</i>−2)<i>θ</i>, −(<i>n</i>−4)<i>θ</i>, …, '
        '(<i>n</i>−2)<i>θ</i>, <i>nθ</i>.',
        '<b>3.</b> A periodic tiling is one finite patch repeated forever, so it can only '
        'have finitely many directions. As long as the directions <i>kθ</i> are all '
        'distinct, the tiling must be aperiodic. (If no child were mirrored, every tile '
        'would point in direction <i>nθ</i>, and the directions would be finite!)',
        '<b>4.</b> arctan ½ is not a rational multiple of π,<super>§</super> so no two '
        'directions <i>kθ</i> coincide, even up to a multiple of 90°. A pinwheel tiling '
        'contains supertiles of every generation, so it has infinitely many directions '
        '(uniformly distributed, as Radin showed). '
        '<b>Therefore no pinwheel tiling is periodic.</b>',
    ]
    yy = y - 12
    for s in steps:
        yy = para(c, s, X0, yy, CW - dial_w - 14, small) - 4.5
    dcx = X1 - dial_w / 2 + 6
    draw_dial(c, dcx, y - 70, 47)
    c.setFont('Serif-Italic', 7.6)
    c.setFillColor(GREY_T)
    c.drawCentredString(dcx, y - 131, 'directions nθ never repeat')

    # the one-line moral
    my = min(yy, y - 136) - 15
    c.setStrokeColor(TILE_BLUE)
    c.setLineWidth(0.5)
    c.line(X0 + 40, my + 15, X1 - 40, my + 15)
    c.line(X0 + 40, my - 8, X1 - 40, my - 8)
    c.setFont('Serif-Italic', 12)
    c.setFillColor(SLATE)
    c.drawCentredString(W / 2, my, 'It never repeats because arctan ½ is not a rational multiple of π.')

    # footnotes
    fy = my - 17
    fy = para(c, '<super>†</super> <i>For the attentive viewer:</i> the tiles are exactly '
                 '2 : 1, but the grout joints are not uniform. For tile plus grout to stay '
                 'on a 2 : 1 grid, 6″ + <i>g</i><sub>end</sub> = 2(3″ + '
                 '<i>g</i><sub>side</sub>), so <i>g</i><sub>end</sub> = '
                 '2<i>g</i><sub>side</sub>: ⅛″ joints along the long sides, but ¼″ at the '
                 'short ends. Can you see the difference?', X0, fy, CW, foot) - 3
    fy = para(c, '<super>‡</super> The same works for any <i>N</i> : 1 tile. The altitude cuts off one '
                 'copy; the rest is the triangle enlarged <i>N</i> times, which divides into '
                 '<i>N</i>² copies (<i>N</i> along the hypotenuse and <i>N</i>(<i>N</i>−1)/2 whole '
                 'tiles), so the triangle divides into <i>N</i>² + 1 copies scaled by '
                 '1/√(<i>N</i>² + 1). For each, <i>θ</i> = arctan(1/<i>N</i>): a 4″ × 12″ tile '
                 'gives a 10-piece pinwheel, a 2″ × 8″ tile a 17-piece one. <i>N</i> = 1 is '
                 'degenerate and periodic, since arctan 1 = π/4 <i>is</i> a rational multiple '
                 'of π.', X0, fy, CW, foot) - 3
    para(c, '<super>§</super> Since tan <i>θ</i> = ½, 2 + <i>i</i> = √5 '
            '<i>e</i><super><i>iθ</i></super>. If <i>θ</i> = (<i>p</i>/<i>q</i>)π, then '
            '(2 + <i>i</i>)<super>2<i>q</i></super> = 5<super><i>q</i></super> = '
            '(2 + <i>i</i>)<super><i>q</i></super>(2 − <i>i</i>)<super><i>q</i></super>, so '
            '(2 + <i>i</i>)<super><i>q</i></super> = (2 − <i>i</i>)<super><i>q</i></super>, '
            'impossible since 2 ± <i>i</i> are distinct Gaussian primes. More generally, '
            'the only rational values of tan at rational multiples of π are 0 and ±1 '
            '(I. Niven, <i>Irrational Numbers</i>, 1956). The irrationality of π itself is '
            'beside the point: arctan 1 = π/4 is a rational multiple of π, and right '
            'isosceles triangles tile periodically.', X0, fy, CW, foot)

    footer(c, 'C. Radin, “The pinwheel tilings of the plane,” Ann. of Math. 139 (1994), 661–702.'
              f'   Border: this wall’s tiling, extended, 1 : {WALL_RATIO}.')
    c.showPage()


# ------------------------------------------------------------------ page 2
def draw_children(c, kind, x, y, scale):
    """Level-1 domino or kite with the child numbers used by the colour mask.
    (x, y) is the page position of the parent's local origin; local y is down."""
    def to(p):
        return (x + scale * p[0], y - scale * p[1])
    kids = kd.level1_children(kind)
    for n, kk, col, pg in kids:
        poly(c, [to(p) for p in pg], fill=TILE_BLUE if col else LIGHT, stroke=SLATE, lw=0.4)
    poly(c, [to(p) for p in kd.leaf_polygons(kind, False)[0]], stroke=SLATE, lw=1.1)
    c.setFillColor(INK)
    c.setFont('Serif', 5.6)
    for n, kk, col, pg in kids:
        cx, cy = to(np.array(pg).mean(0))
        c.drawCentredString(cx, cy - 2, str(n))


def draw_supertile(c, perm, x, y, w, ncolors=2):
    """A level-2 domino (625 pieces) with grout, lower-left corner at (x, y)."""
    h = w / 2
    c.setFillColor(GROUT)
    c.rect(x, y, w, h, stroke=0, fill=1)
    for kind, col, polys in kd.tiles(perm, ncolors, level=2, matrix=kd.S(w / 2)):
        for pg in polys:
            poly(c, [(x + px, y + h - py) for px, py in pg], fill=TILES[col])


def bits(perm):
    return [k for k in range(64) if (perm >> k) & 1]


# the bathroom first, then favourites from mksvg.js
GALLERY_PICKS = [2560, kd.on(0, 1, 2, 6, 7, 8, 9), kd.on(0, 1, 6, 8), 62, 253952,
                 kd.on(14, 15, 18, 22, 13, 26, 32), kd.on(0, 5, 6, 11, 12),
                 kd.on(0, 5, 6, 11, 12, 4), kd.on(0, 12, 8, 1),
                 kd.on(0, 6, 8, 12, 19, 23, 16, 31, 37), kd.on(0, 6, 12, 34, 35, 17, 4, 5),
                 kd.on(0, 6, 7, 9, 10, 3)]


def page_two(c):
    new_page(c)
    title_block(c, 'COLORING THE PINWHEEL', 'dominoes, kites, and a 38-bit mask')

    y = 650
    heading(c, 'IV', 'Dominoes and kites', X0, y, CW)
    sc = 62
    dy = y - 16
    draw_children(c, 'domino', X0, dy, sc)
    draw_children(c, 'dart', X0 + 2 * sc + 24, dy, sc)
    c.setFont('Serif-Italic', 7.8)
    c.setFillColor(GREY_T)
    c.drawCentredString(X0 + sc, dy - 1.6 * sc - 12, 'domino → 15 dominoes + 10 kites')
    c.drawCentredString(X0 + 3 * sc + 24, dy - 1.6 * sc - 12, 'kite → 12 dominoes + 13 kites')
    tx = X0 + 4 * sc + 40
    para(c, 'On the wall, triangles are paired across their hypotenuses: a <i>domino</i> is '
            'a whole 3″ × 6″ tile, a <i>kite</i> is two mirror-image half-tiles. Taking two '
            'pinwheel generations at once gives a substitution that inflates by 5, shown at '
            'left. Children of a domino are numbered 0–12 (pieces swapped by its half-turn '
            'symmetry share a number); children of a kite, 13–37.',
         tx, y - 14, X1 - tx, small)

    y2 = dy - 1.6 * sc - 26
    y3 = para(c, 'A coloring is a set <i>S</i> of these numbers. Each piece is one color step '
            'from its parent if its number is in <i>S</i>, and the same color otherwise, '
            'counting modulo the number of colors. With the two tiles on this wall, '
            '<i>S</i> = {9, 11}, the two shaded kites in every domino, gives the border '
            'around this page. Below are other sets explored while designing the wall, each on a '
            'level-2 domino of 625 pieces, with their original working names.',
         X0, y2, CW, small)

    # gallery
    cols, gx = 3, 14
    cw = (CW - (cols - 1) * gx) / cols
    ch = cw / 2
    top = y3 - 12
    names = {p: n for p, n, f in kd.GALLERY}
    names[2560] = 'kites (this wall)'
    for i, perm in enumerate(GALLERY_PICKS):
        r, k = divmod(i, cols)
        x = X0 + k * (cw + gx)
        yb = top - (r + 1) * ch - r * 19
        draw_supertile(c, perm, x, yb, cw)
        c.setStrokeColor(SLATE)
        c.setLineWidth(1.4 if perm == 2560 else 0.6)
        c.rect(x, yb, cw, ch, stroke=1, fill=0)
        name, mask = names[perm], '  {' + ', '.join(map(str, bits(perm))) + '}'
        wn = c.stringWidth(name, 'Serif-Italic', 8.2)
        wm = c.stringWidth(mask, 'Serif', 6.4)
        cx0 = x + cw / 2 - (wn + wm) / 2
        c.setFont('Serif-Italic', 8.2)
        c.setFillColor(SLATE)
        c.drawString(cx0, yb - 10, name)
        c.setFont('Serif', 6.4)
        c.setFillColor(GREY_T)
        c.drawString(cx0 + wn, yb - 10, mask)

    footer(c, 'Colorings from github.com/cscott/tile-hack, in this wall’s tiles: '
              'weather gray and skylight blue.')
    c.showPage()


def build(path='pinwheel-tiling.pdf'):
    c = canvas.Canvas(path, pagesize=letter)
    c.setTitle('The Pinwheel Tiling')
    c.setAuthor('C. Scott Ananian')
    c.setSubject('Why the pinwheel tiling is aperiodic, and how the wall is colored')
    page_one(c)
    page_two(c)
    c.save()


if __name__ == '__main__':
    build()
