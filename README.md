# Bathroom tiling posters

Two framed US Letter prints about the tiled walls:

- `pinwheel-tiling.pdf` (upstairs), two pages: why the pinwheel tiling never
  repeats; the kite/domino form used on the wall and a gallery of colorings.
- `wang-tiling.pdf` (downstairs), two pages. Page 1: Wang tiles, tiles that
  add, and an unbuilt wall that generates the Fibonacci numbers, with its 18
  tiles (border: the Fibonacci tiling). Page 2: the prime sieve on the wall,
  large, and its 43 tiles (border: the prime wall as laid).

```
pip install reportlab numpy
python3 make_poster.py      # -> pinwheel-tiling.pdf
python3 make_wang.py        # -> wang-tiling.pdf
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
| `make_wang.py` | The Wang pages: layout and text (`page_one()`, `page_two()`). It reuses the fonts and helpers from `make_poster.py`. Tile colors are `GLAZE` (silk is glazed ceramic, basalt dark stone, charcoal and auburn colored glass) and the etched-line tones are `ETCH`. The page text says "edge type" for a Wang edge label and keeps "color" for the tiles. |
| `wangtiles.py` | A Python port of `wangprime.js`: the PRIME2b tile set and edge colors, the same backtracking solver, the sum tiles (after Grünbaum & Shephard) and the 11-tile Jeandel–Rao set. `python3 wangtiles.py` prints the 21 × 27 tiling. |
| `wang_wall.json` | The as-built layout of the downstairs wall, in Wang-grid units: every silk, charcoal and auburn tile and basalt triangle, taken from `wang3-grout.svg`. |
| `tools/extract_wang_guide.py` | Regenerates `wang_wall.json` from `wang3-grout.svg` (needs `svgelements`). It checks that every diamond's glaze matches the Wang tiling: all 1133 do. |
| `fonts/NotoSerifTC-subset.ttf` | Just 王, 浩 and 黃 from Noto Serif CJK TC (SIL Open Font License), converted to TrueType so ReportLab can embed them. `tools/make_cjk_subset.py` rebuilds it; add characters to `CHARS` there. |
| `fibtiles.py` | The Fibonacci tiles (Grünbaum & Shephard Fig. 11.4.2, corrected: 18 tiles), their edge-type looks, the forced tiling, and `lay_tiles()`, the greedy layout in 2″ × 8″ tile (down-right on and below the long diagonal, up-right above it; whole tiles from the upper end of each run, at most one cut per run). |
| `tools/verify_fib.py` | Checks that the 18 tiles, and the tiles as drawn (look-alike edges merged), force 1, 2, 3, 5, 8, 13, 21, 34 in a 34 × 24 patch, and the Lucas-number variant mentioned in section III. |
| `tools/fib_preview.py` | The edge-type key, the 18 tiles and the laid tiling on one sheet (`fib_preview.pdf`). |
| `hattiles.py` | The hat ("einstein") tiling by substitution, ported from Craig S. Kaplan's hatviz (BSD 3-Clause), plus the hat's 8 kites / 16 right triangles (legs 1 : √3). Label `H1` is the reflected hat. |
| `tools/hat_preview.py` | Exploratory sketch of an unbuilt hat wall in the upstairs colors. |
| `hat_preview.pdf`, `HAT_NOTES.md` | That sketch, and the findings: why 2 : 1 tiles can't make any hat-family tile, how to cut hats from 1 : √3 tiles, and why uniform grout works (with a tolerance table for near-√3 tiles); and the better design, laid in 60° rhombus tile with the fewest cuts (`hattiles.optimal_layout()`, page 2 of the sketch; needs `ortools`, result cached in `hat_layout.json`). |
| `tools/jr_patch.py` | A patch of the Jeandel–Rao tiling in the poster's colors (`jr_patch.pdf`; needs `ortools`). It solves a 44 × 34 patch and shows the middle 34 × 24. |
| `tools/verify_sum.py` | Checks that the addition tiles force S to column A₁ + A₂, both with the book's edge types and with edges merged wherever they look alike as drawn (`wangtiles.SUM_LOOKS`). Edge 6, under ★, carries a heavy double line (as under F′ and ★ in the other two sets) partly for this reason: drawn like edge 3, it would let S stand anywhere from column 10 to 17. |
| `tools/verify_wang.py` | Checks that the Python solver reproduces `wang3.svg` and `wang3-grout.svg` tile for tile, and that the top row marks exactly the primes. |

## Common edits

- **Text:** edit the `para(...)` calls in `page_one()` / `page_two()`.
- **Gallery:** edit `GALLERY_PICKS` in `make_poster.py`. Names come from `kitedomino.GALLERY`; add entries there for new masks. `kitedomino.on(0, 5, 6, ...)` builds a mask from child numbers.
- **Tilt shading (page 1, section II):** `TILT_SHADE` in `make_poster.py` gives one shade per tile direction *k*θ (modulo a quarter-turn), the same in every panel; the captions draw the matching swatches. The long leg (the side of length 2) of each of the smallest triangles is drawn bold (`long_legs()`), since that is the edge whose direction is measured. In the first panel all five children are tilted θ, and the dashed line marks the uncut subway tile.
- **Colors:** the tile colors are `kitedomino.BATH_COLORS`, taken from `mksvg.js`. The page palette is at the top of `make_poster.py`.
- **Border scale:** `WALL_RATIO` (currently 1:24). The border is the level-3 supertile that contains the wall as its child 7, so it is the wall's own tiling extended outward; it fills the page at 1:24 or larger. The gallery cells are about 1:77.

## Notes on the Wang page

- The tiling is PRIME2b from `wangprime.js` (VARIANT 3) on a 21 × 27 grid. The wall shows columns 1–20 and the top 15 rows, which cover the bands of 3 and 5 and most of 7. The page-2 border is the whole 21 × 27 design as laid, grout and all (`BORDER_GROUT`, kept light so joints read apart from the etching); the section IV figure draws the bare Wang tiling without grout (`draw_wall(..., built=False)`). The cutting guide stops just short of its bottom and right edges, so those few triangles are drawn from the Wang grid instead.
- Each Wang tile is 73 mm, so a diamond is 51.6 mm: a 50 mm tile plus a 1.6 mm (1/16″) joint. Four diamonds make 206.4 mm, a 200 mm tile plus a 6.4 mm (1/4″) end joint.
- The etched lines follow `Color.toSvg` in `wangprime.js`: each edge's lines run from the tile center to the edge, 0.1 tile wide, or 0.2 for "thick". Their actual widths on the wall may differ. Unlike `wangprime.js`, `tile_lines()` joins them neatly. Lines that stop at a double line passing straight through (D4*, D4c, D4, d1, d2, d2*, d1p, d2p, d1c, d2c) end at its near line, like a T, with no stub past it. In A* and B* the double lines turn the corner nested, like box-drawing ╚ and ╗. In *, p and D1*, lines that would end in mid-tile opposite the black border are carried into the black triangle and clipped by it, so they seem to come out of the border. Overlaps are filled once, so translucent etching never doubles up.
- Layout: `make_wang.py` builds the pages a few times. On page 2 the wall figure first grows into the free space (`WALL_SCALE` is its starting size, capped at the full text width). Then whatever space is left under each page's last text is shared out evenly above its section headings (and the page-2 figure) (`build(gaps=...)`), so edits to the text re-balance the pages by themselves.
- Tile colors were matched by eye to photographs. Adjust `GLAZE` and `ETCH` to taste. The signatures (`SIGNATURE_FIB`, October 2026, for page 1, which carries the new Fibonacci design; `SIGNATURE`, February 2019, for page 2, the wall as built; both in `make_wang.py`) are separate from the pinwheel page's.
- Aperiodicity: with color 0 (black) on the top and left boundary, only `*` fits in the corner, and no tile has 0 on its bottom or right edge. Every band of boxes is then forced, and so is every road. A prime column *p* must carry a "prime" road above band *p*, because `D4*` needs one. So the quarter-plane tiling is unique, and its top row marks exactly the primes. A *finite* patch with an open bottom edge is weaker. Enumerating every 21 × 17 tiling shows 11–19 can come out "composite" when their own bands lie below the patch, but a composite can never come out "prime". On the wall, the proof that 11 is prime lies below the floor.

## Notes on the Fibonacci section

- The book's figure has three misprints: panel (b) omits the tile (7, 8, 1, 1) that continues the diagonal, the example grid (a) lacks two "6" labels at cells (2,2) and (2,3), and the caption lists 11. With the 18 tiles the quarter-plane tiling is forced.
- Look-alike edges: 2 and 3 may share a look (plain red), but 7 vs 10, 8 vs 9 and 6 vs 11 must differ, or the tiling stops being forced; that is why the climbing staircase (9/10) has a thin etched line. If F′ were also made to look like an ordinary F, the tiles would admit other starting pairs, such as the Lucas numbers.
- The tiling is solved 32 columns wide and cropped, so the up-right runs at the right edge of the section III figure and the page-1 border keep their upper ends and the stagger stays regular.

## Notes on the port

- Geometry and colors match `mksvg.js` exactly. Run `python3 tools/verify_port.py /path/to/tile-hack` to check; it needs node, `npm install` in tile-hack, `svgelements` and `scipy`.
- `mksvg.js`'s `flipDart()` emits the malformed transform `rotate({$ALPHA_DEG}) ...` (a `{$` / `${` typo). Renderers, Inkscape included, discard it, so "flipped" darts were drawn unflipped, and the port does the same (`FLIPDART_IS_IDENTITY = True`). The typo is harmless and possibly lucky: the transform as written, `rotate(α) scale(-1,1) rotate(-α)`, mirrors across the line perpendicular to the kite's axis and breaks the tiling (`FLIPDART_IS_IDENTITY = False` reproduces that). The geometrically sensible flip, a mirror across the kite's axis, gives the same shapes as identity and the same colors for every gallery style except "worms 3". `tools/flipdart_compare.py` draws all of this.
- The wall placement is the layer matrix in `pinwheel-grout.svg`, plus the small `translate(0.0273, -0.0029)` nudge applied there. That's `WALL_NUDGE` in `make_poster.py`.
