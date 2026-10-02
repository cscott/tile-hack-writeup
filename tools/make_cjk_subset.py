#!/usr/bin/env python3
"""Make fonts/NotoSerifTC-subset.ttf: the few Chinese characters the Wang page
uses, from Noto Serif CJK TC, converted to TrueType outlines so that
ReportLab can embed them.  (Noto fonts are under the SIL Open Font License.)

    python3 tools/make_cjk_subset.py [/path/to/NotoSerifCJK-Regular.ttc]
"""
import os, sys
from fontTools.ttLib import TTCollection, TTFont, newTable
from fontTools import subset
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

CHARS = '王浩黃'
SRC = sys.argv[1] if len(sys.argv) > 1 else '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
OUT = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'NotoSerifTC-subset.ttf')

coll = TTCollection(SRC)
font = next(f for f in coll.fonts if 'TC' in f['name'].getDebugName(4))
opts = subset.Options()
opts.name_IDs = ['*']
opts.notdef_outline = True
opts.layout_features = []
sub = subset.Subsetter(opts)
sub.populate(text=CHARS)
sub.subset(font)

# CFF (cubic) -> glyf (quadratic)
gs = font.getGlyphSet()
glyf = newTable('glyf')
glyf.glyphOrder = font.getGlyphOrder()
glyf.glyphs = {}
for name in font.getGlyphOrder():
    pen = TTGlyphPen(gs)
    gs[name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
    glyf.glyphs[name] = pen.glyph()
font['glyf'] = glyf
font['loca'] = newTable('loca')
del font['CFF ']
if 'VORG' in font:
    del font['VORG']
font['maxp'] = maxp = newTable('maxp')
maxp.tableVersion = 0x00010000
for k in ('maxZones', 'maxTwilightPoints', 'maxStorage', 'maxFunctionDefs',
          'maxInstructionDefs', 'maxStackElements', 'maxSizeOfInstructions',
          'maxComponentElements', 'maxPoints', 'maxContours', 'maxCompositePoints',
          'maxCompositeContours', 'maxComponentDepth'):
    setattr(maxp, k, 0)
maxp.maxZones = 1
maxp.numGlyphs = len(font.getGlyphOrder())
font['head'].indexToLocFormat = 0
font['head'].glyphDataFormat = 0
font['post'].formatType = 2.0
font['post'].extraNames = []
font['post'].mapping = {}
font.sfntVersion = '\x00\x01\x00\x00'
font.recalcBBoxes = True
font.save(OUT)
print('wrote', os.path.normpath(OUT))
