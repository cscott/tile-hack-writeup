# An unbuilt "einstein" wall

Notes on building the hat, the aperiodic monotile of Smith, Myers, Kaplan
and Goodman-Strauss (2023), from cut subway tile. The coloring is the
upstairs pinwheel's: reflected hats in skylight blue `#9eaebe`, all others
in weather gray `#cfcecc`. The sketch is `hat_preview.pdf`. To regenerate it:

```
PYTHONPATH=. python3 tools/hat_preview.py
```

## The short version

- The hat is 8 kites, and each kite is two mirror-image right triangles with
  legs **1 : √3** (30° and 60° corners). So you need 1 : √3 tiles, cut once
  along the diagonal, in two colors.
- **No setting of the hat's parameter can be built from 2 : 1 subway tile
  cut on the diagonal.** This is impossible, not just awkward.
- With true 1 : √3 tiles, a **uniform grout joint works exactly**. A tile
  close to 1 : √3 also works: the small error just makes the joint along each
  diagonal cut taper slightly.

## Why 2 : 1 tiles can't work

Two 1 : 2 right triangles glued along their diagonal make a kite with corners
of 126.87°, 90°, 53.13° and 90°. A hat kite needs 120°, 90°, 60° and 90°.
The kites then fail to close up:

- around a hexagon center, six kites meet at 6 × 53.13° = 318.8°, leaving
  a 41.2° gap. This is drawn in the sketch.
- around a triangle center, three kites take 3 × 126.87° = 380.6°, so they
  overlap by 20.6°.

Changing the hat's parameter doesn't help. The hat family Tile(*a*, *b*)
changes only edge lengths, never angles, and every member has 120° corners.
A corner built from 1 : 2 triangles has angle *p*·α + *q*·(90° − α) + *r*·90°,
where α = arctan ½. This equals 120° only if α is a rational multiple of π.
It isn't: that is the same fact that makes the pinwheel tiling aperiodic.
So no hat-family tile can be cut from 1 : 2 triangles, however they are
arranged.

## Cutting a hat from 1 : √3 tiles

- **Pieces.** A hat is 8 kites, or 16 triangles: 8 of each handedness. A
  tile cut along one diagonal gives two triangles of the same hand, and
  glazed tiles can't be flipped. So each hat needs 8 tiles: 4 cut along one
  diagonal and 4 along the other, one cut each. Starting from 3″ × 6″ tile
  instead adds a second cut per tile, trimming it to 3″ × 5.2″.
- **No uncut tiles.** An uncut rectangle would be two triangles sharing their
  diagonal with one rotated 180°. In the hat's kite grid, triangles share a
  diagonal only as the two mirror-image halves of a kite. So every piece is
  a triangle, and there is nothing to merge, even within one hat.
- **Size.** If the short leg is 1 unit, a hat is 6 × 4.33 units, with an area
  of 8√3 ≈ 13.9 square units. With 3″ short legs, a hat is about
  18″ × 13″, before grout.

## Better: lay it in 60° rhombus tile

The 30° and 60° corners are those of a standard 60° rhombus tile. Cutting a
rhombus along both diagonals gives four 1 : √3 right triangles. This also
works the other way round, which leads to a much better design.

Split every kite of the hat tiling in half. Wherever four right angles meet,
at the midpoint between two hexagon centers of the kite grid, the four
triangles there form exactly one 60° rhombus, with side 2 and diagonals
2 and 2√3. Around each hexagon center, where twelve 30° points meet, six
of these rhombi fan out. The whole hat tiling is therefore a *rhombille*
("tumbling blocks") tiling with some rhombi cut apart.

A rhombus can also sit *across* a kite axis: the two equilateral halves on
either side of the axis make a rhombus whose short diagonal is the axis
(one whole kite plus a half-kite on each side). These "offset" rhombi have
the same three orientations as the grid ones; only the joint lines differ.
With point-to-point cuts, these are all the pieces there are:

| piece | triangles | from a rhombus | cuts |
|---|---|---|---|
| whole rhombus, on the grid | 4 around a right-angle point | uncut | 0 |
| offset rhombus | 2 equilateral halves meeting on a kite axis | uncut | 0 |
| equilateral half | 2, sharing a long leg | short diagonal; two halves per cut | ½ |
| obtuse half | 2, sharing a short leg | long diagonal; two halves per cut | ½ |
| right triangle | 1 | both diagonals; four per three cuts, two of each hand | ¾ |

Any two equilateral halves that meet edge to edge make a grid rhombus or an
offset rhombus, and two obtuse halves meeting on their long edge make a grid
rhombus. Every other pair is not convex, or not a rhombus. A rhombus is
mirror-symmetric, so there is no handedness to manage: every cut gives
pieces of both hands, and the wall needs left and right triangles in nearly
equal numbers (310 and 308 blue, 314 and 320 light, in the patch below).

`hattiles.optimal_layout()` chooses the pieces as an exact cover of the
half-kites, never mixing colors, with OR-Tools CP-SAT. It works in three
rounds: fewest cuts at the costs above; then fewest obtuse halves, since
the long skinny cut is the one most likely to crack a tile; then fewest
offset rhombi, so the light field stays plain tumbling blocks wherever it
can. The solve takes about four minutes. `tools/hat_preview.py` caches the
result in `hat_layout.json`; delete the file or pass `--resolve` to solve
again. The first round is proven optimal. The later two stop at a time
limit, so they are very good but not proven best. Page 2 of the sketch
shows the result.

- **Every blue hat is two whole rhombi (one on the grid, one offset), one
  equilateral half and six right triangles**: 4 + 4 + 2 + 6 = 16
  half-kites, ½ + 6 × ¾ = **5 cuts**. Solving a lone hat by enumeration
  confirms this is the minimum. The only other 5-cut layout swaps the
  equilateral half for an obtuse half.
- **The light tile** takes about six right triangles per blue hat. About
  two of these are forced locally: a light half-kite whose rhombus-mates on
  both legs are blue. The rest are forced by parity over the region.
  Chains of offset rhombi link the blue hats in pairs, so the light tile
  closes up around each hat without further cuts. They are shaded in the
  small panel of the sketch.
- **No obtuse halves** are needed anywhere inside the patch.
- **Within 30 units of the patch center (804 hats):** 992 cuts. Using only
  the grid rhombi would take 1,374, and cutting every half-kite from 1 : √3
  rectangles 6,432, all counted the same way. About 1 tile in 9 needs any
  cut.

Grout stays uniform too. Lay each whole rhombus with the usual joint. When
cutting one, take out a strip one joint wide along the cut, the saw kerf plus a
trim. Each piece is then exactly its slot shrunk by half a joint on every side,
just like the whole tiles.

Size: a rhombus side is 2 units, where a triangle's short leg is 1. A hat is
6 × 4.33 units, so it spans about 3 × 2.2 rhombus sides. With 3″ sides, that
is about 9″ × 6.5″ per hat. Rhombus tiles are usually sold by their overall
size or as mosaic sheets, so measure the side before planning.

## Grout

Shrinking a triangle by the same distance on every side, toward its
incenter, gives a smaller triangle of exactly the same shape. So 1 : √3
pieces set with a uniform joint fit the 1 : √3 layout exactly. Unlike the
pinwheel and Wang walls, no joint needs to be wider than the others.

A tile that is only close to 1 : √3 leaves each triangle's corner angle
slightly off from 30°. Set the right angle and both short sides with the
nominal joint, and the joint along the diagonal cut tapers. That cut is the
axis of each kite, between its two halves. With a 3″ short leg (or the size
given):

| tile | long : short | small angle | taper along the cut |
|---|---|---|---|
| 3 × 5.196″ (exact) | 1.732 | 30.00° | none |
| 15 × 26 cm | 1.733 | 29.98° | 0.1 mm |
| 7 × 12 cm | 1.714 | 30.26° | 0.6 mm |
| 3 × 5.25″ | 1.750 | 29.74° | 0.7 mm |
| 4 × 7″ | 1.750 | 29.74° | 0.9 mm |
| 3 × 5″ | 1.667 | 30.96° | 2.5 mm (~3/32″) |
| 3 × 5.5″ | 1.833 | 28.61° | 3.9 mm (~5/32″) |
| 3 × 6″ (subway) | 2.000 | 26.57° | 10.2 mm (~3/8″): no good |

These sizes are examples of ratios to look for, not known products.
Anything within about ±1% of √3 hides in a normal 1/8″ joint.

## Coloring

Every reflected hat is surrounded by unreflected ones, so two colors are
enough to pick out the reflected hats. In the generated patch they are
459 of 3603, about 1 in 8.

Uniform grout, though, makes the light hats merge into one field: nothing
marks where one light hat ends and the next begins. Compare the two panels
of the sketch. If the hat shapes themselves should be legible on the wall:

- use a third color, e.g. by the hat's orientation or by its role in the
  substitution, as in Kaplan's hatviz;
- make the joint between hats slightly wider or darker than the joint
  inside a hat;
- etch the hat outlines, as the Wang wall etches its edge types.

## Code

- `hattiles.py`:
  - generates hats by the H/T/P/F metatile substitution, ported from Craig
    S. Kaplan's [hatviz](https://github.com/isohedral/hatviz) (BSD 3-Clause,
    © 2023 Craig S. Kaplan);
  - `HAT_KITES` and `HAT_TRIANGLES` decompose the hat into 8 kites and 16
    triangles;
  - `inset_triangle()` gives the grout inset;
  - label `H1` marks the reflected hat, which `is_reflected()` also detects.
- `rhombus_layout()` is the simple grid-only grouping. `candidate_pieces()`,
  `optimal_layout()` and `cut_stats()` give the fewest-cuts layout (needs
  `pip install ortools`).
- `tools/hat_preview.py`: draws the sketch. Its grout width is `JOINT`, in
  units of the short leg. Its layout is cached in `hat_layout.json`.
