"""Flatten the visible tile layer of an SVG made by tile-hack/mksvg.js into
polygons (wall inches) + colour index.  Used to check the Python port.

mksvg.js's flipDart() emits the malformed transform "rotate({$ALPHA_DEG}) ...";
Inkscape (and every SVG renderer) discards an unparseable transform, i.e.
treats it as the identity, so we do the same here."""
import re, json, sys
import xml.etree.ElementTree as ET
from svgelements import SVG, Path, Shape, Group

def extract(src):
    text = open(src).read()
    text = re.sub(r'transform="rotate\(\{\$ALPHA_DEG\}\)[^"]*"', '', text)
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    root = ET.fromstring(text)
    INK = '{http://www.inkscape.org/namespaces/inkscape}'
    for g in list(root):
        if g.get(INK + 'groupmode') == 'layer':
            if 'none' in g.get('style', '') or g.get(INK + 'label') in ('Grout', 'Swatches'):
                root.remove(g)
    tmp = src + '.visible.svg'
    ET.ElementTree(root).write(tmp)
    raw = open(tmp).read()
    out = []
    svg = SVG.parse(tmp, reify=True)
    for el in svg.elements():
        if isinstance(el, Shape) and not isinstance(el, Group):
            if el.id and el.id.startswith('linearGradient'):
                continue
            blob = ' '.join(str(v) for v in el.values.values())
            m = re.search(r'linearGradient(\d+)', blob)
            pts = [(float(s.end.x), float(s.end.y)) for s in Path(el).segments() if s.end is not None]
            if len(pts) >= 3 and m:
                out.append({'c': int(m.group(1)), 'pts': pts})
    return out

if __name__ == '__main__':
    polys = extract(sys.argv[1])
    json.dump(polys, open(sys.argv[2], 'w'))
    from collections import Counter
    print(len(polys), 'polygons', Counter(p['c'] for p in polys))
