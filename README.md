# Pinwheel tiling poster

Generates `pinwheel-tiling.pdf`, a two-page US Letter print about the
pinwheel tiling on the bathroom wall.

- **Page 1:** why the tiling never repeats.
- **Page 2:** the kite/domino form used on the wall, and a gallery of colorings.

```
pip install reportlab numpy
python3 make_poster.py
```

Fonts: GNU FreeFont (FreeSerif). Set `FONT_DIR` at the top of
`make_poster.py` if yours live somewhere other than
`/usr/share/fonts/truetype/freefont/`. On macOS that might be
`brew install --cask font-freefont`; any TTF family with the Greek and math
glyphs used here (θ π √ ℤ ½ ⅛ ¼) will do.

## Files

| file | what it is |
|---|---|
| `make_poster.py` | Layout and all the text. Page 1 is `page_one()`, page 2 is `page_two()`. Palette and signature are near the top. |
| `pinwheel.py` | The single-triangle pinwheel substitution, used for the page-1 diagrams. |
| `kitedomino.py` | A Python port of `mkRect()`/`mkDart()` from [tile-hack](https://github.com/cscott/tile-hack)'s `mksvg.js`. It uses the kite/domino substitution with grout and `permN` colorings. It draws the border (the real wall, `perm2560`) and the page-2 gallery. `GALLERY` holds the styles and notes from `mksvg.js`. |
| `tools/verify_port.py` | Checks the port against the original JavaScript, piece by piece. |
| `tools/extract_svg.py` | Flattens an SVG from `mksvg.js` into polygons. Used by `verify_port.py`. |
| `tools/flipdart_compare.py` | Draws `flipdart.png`, comparing the dart-flip variants (`PYTHONPATH=. python3 tools/flipdart_compare.py`). |

## Common edits

- **Text:** edit the `para(...)` calls in `page_one()` / `page_two()`.
- **Gallery:** edit `GALLERY_PICKS` in `make_poster.py`. Names come from `kitedomino.GALLERY`; add entries there for new masks. `kitedomino.on(0, 5, 6, ...)` builds a mask from child numbers.
- **Colors:** the tile colors are `kitedomino.BATH_COLORS`, taken from `mksvg.js`. The page palette is at the top of `make_poster.py`.
- **Border scale:** `WALL_RATIO` (currently 1:24). The border is the level-3 supertile that contains the wall as its child 7, so it is the wall's own tiling extended outward; it fills the page at 1:24 or larger. The gallery cells are about 1:77.

## Notes on the port

- Geometry and colors match `mksvg.js` exactly. Run `python3 tools/verify_port.py /path/to/tile-hack` to check; it needs node, `npm install` in tile-hack, `svgelements` and `scipy`.
- `mksvg.js`'s `flipDart()` emits the malformed transform `rotate({$ALPHA_DEG}) ...` (a `{$` / `${` typo). Renderers, Inkscape included, discard it, so "flipped" darts were drawn unflipped, and the port does the same (`FLIPDART_IS_IDENTITY = True`). The typo is harmless and possibly lucky: the transform as written, `rotate(α) scale(-1,1) rotate(-α)`, mirrors across the line perpendicular to the kite's axis and breaks the tiling (`FLIPDART_IS_IDENTITY = False` reproduces that). The geometrically sensible flip, a mirror across the kite's axis, gives the same shapes as identity and the same colors for every gallery style except "worms 3". `tools/flipdart_compare.py` draws all of this.
- The wall placement is the layer matrix in `pinwheel-grout.svg`, plus the small `translate(0.0273, -0.0029)` nudge applied there. That's `WALL_NUDGE` in `make_poster.py`.
