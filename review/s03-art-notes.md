# Station 3 final art: notes and critique

Set script: `art/scripts/s03_art_build.py` → `art/blender/s03_weighin.blend` → `render_station.py` → `pack_layers.py s03` → `public/assets/stations/s03/`.
Review composites: `review/s03-art-pass1.png` (draft, before fixes) and `review/s03-art.png` (final). Both come from `node tools/preview_s03_art.mjs`. The text on them (rates, "1.0 kg", the chamber words) is an overlay showing what `Station03.ts` will draw. It is not baked into the render.

## References (art bible §0)

| Element | Traced from | Use |
|---|---|---|
| Russell Market wall: pointed arches, pilasters, base moulding, lintel over the entrance, jali in the arch, bracketed cornice | X04 / R24 (2023, Thejeshgn, CC BY-SA 4.0); X03 / R23 (2020, Ahmed Nisar, CC BY-SA 4.0) | Form. Colour is white with a faint pink ghost (§0 decision) |
| Posters on the pilasters | X04 / R24 | Density only: colour blocks, no text |
| Counter: steel top | F04 / R10 (Tier A) | Material |
| Counter front: blue-and-white checker tiles | X05 / R25 (2008, fraboof, CC BY-SA 2.0) | Material: ties the hub to the market's meat section |
| Crate: ribbed, stackable, handholds | F03 / R13 (Tier A) | Form only. Colour is Chamber B's meaning blue (§3.2) |
| Rate board frame | F04 fascia (Tier A) | Flex-banner look; board left blank |
| Wet paving, drain, puddles | R07 paving, R11 wet floor (F03); deck p. 34, *Five senses: Touch* | Material |
| Riyaz: cap, checked shirt, apron, wet hands | Deck p. 22 (persona), p. 23 (wet hands, empathy map); s01 costume | Costume. Apron clean, no blood (§4 "meat") |
| Platform scale, cold-room front, cooling unit, solar panel, attendant | None (§0 gaps; our proposal) | Generic forms, no brands, no digits. "Clean but not shiny" (§4) |

The Commons form searches that task 14 asks for ("platform scale", "plastic crate") were **not done** under the deadline. The scale is drawn generic, and no external file was traced for it.

## Decisions from the lead (2026-10-25)

- Crate in meaning blue (art bible §3.2), not red.
- Door bands baked into the set: green for A, blue for B. **No words baked in**: Phaser draws "Chamber A" / "Chamber B" at the `door_a` / `door_b` anchors (§3.3 rule 3).
- Masonry is white with the pink ghost, matching X04 and s02.
- Rate board blank in the render; Phaser draws the rates. Every rate stays `₹[__]/kg`.

`tools/check_palette.py` gains an allow-list with one entry, `s03/crate.png` (offsite), as task 14 says. The door bands cover 0.15% (income) and 0.14% (offsite) of `bg.png`, under the checker's 0.2% limit, so they need no entry. `check_palette.py s03` passes.

## Pass 1: draft render (`review/s03-art-pass1.png`)

| Rule | Finding | Fix |
|---|---|---|
| §0 façade | The pink ghost covers about a third of the wall in large salmon blotches, so it reads as the 2020 pink building, not "a faint ghost" | Own masonry material for this set: smaller worn patches at ~55% mix, a little soot washing down from the cornice. The kit's shared material is untouched (s02 uses it) |
| §5 interiors | No mass behind the wall, so the entrance showed bright plinth paving and no room | `kit.building_mass` with the hub room as a void, so the room behind the attendant drops to shadow |
| §4 wet paving | Six round, mirror-like puddles read as holes in the floor (they reflected the black void) | Two long, flat puddles by the drain, lighter and slightly rough; the wet sheen comes from the paving material's wet patch |
| R24 jali | The screen read as a brick wall | Thicker white bars, larger dark holes |
| §6.3 density | The masonry was bare, with no signage texture above the action | Three faded, illegible posters on the pilasters, as in R24 |
| Brief: wet hands | Riyaz's arms reached forward like a grab; the drips were invisible against the floor; his back was to the camera | Hands held out to the sides, clear of the apron; brighter, larger drops; turned three-quarters to the camera |
| §3.2 crate | The crate rendered a pale lavender (plastic fade toward white, then AgX lifted it), not the meaning blue | Its own plastic with a 12% fade, base one step under `#1F5BA8` |
| §8 type | A 1.3 m board is ~160 px wide on screen: no room for three rate lines | Board widened to 1.8 × 1.25 m, filling the right blind arch |

## Pass 2: final render (`review/s03-art.png`)

Full samples (128 for bg, 96 for sprites). All of pass 1 is fixed: the room behind the attendant is dark, so the attendant and the scale head read against it; the crate is the strongest colour in the action zone (kilo first, §6.3); the drops and the wet hands read; the puddles read as wet stone.

| Rule | Finding | Status |
|---|---|---|
| §0 façade | The pink ghost is now almost invisible: a few faint patches near the cornice | Left as is. "Faint" was the brief, and erring towards white keeps it continuous with s02. Raise the mix in `masonry_faint` if the field visit shows more pink |
| §6.3 one focal point | Riyaz stands between the crate's start (602, 587) and the scale pan (929, 600). A straight drag passes over his legs | Not re-rendered. `Station03.ts` should draw the dragged crate above `riyaz_idle` (see the builder notes) |
| §6.3 blueprint line | Scale pan at y 601 and crate centre at y 587, both above 660. The foreground below 660 holds only paving, the drain and one puddle | OK |
| §8 type | Even at 1.8 m the board is ~220 px wide on screen. The rates fit at ~19 px, which is under the 28 px base | The rates should be drawn as a card anchored at `rate_board`, not written onto the wall (builder notes) |
| §4 hub fittings | Cold room, scale, counter, crate and rate board read as new against the worn wall, without chrome or glow | OK |
| §3.3 | The meaning colours in the set are the crate (blue) and the two door bands (green, blue). Each gets its word from Phaser | OK, per the lead's decisions above |

## For `Station03.ts` (task 03)

- **Layers:** `bg`, `crate` + `crate_shadow`, `riyaz_idle`, `attendant_idle`, `attendant_type`. There is no FX layer.
- **Anchors (task 03's names):** `scale_pan`, `rate_board`, `crate_centre`, `crate_knot`.
- **Extra anchors:**
  - `scale_display`: where to draw "1.0 kg";
  - `attendant_phone`: for the masked number card;
  - `attendant_head`, `riyaz_head`, `riyaz_hand`;
  - `door_a`, `door_b`: for the "Chamber A" / "Chamber B" words, which are now needed in s03 too, because the bands are in the set;
  - `solar`, `exit`.
- **Riyaz has no `_type` or phone pose**, by design. The attendant's `type` pose holds the phone up.
- **Draw order:** draw the dragged crate above `riyaz_idle`.
- **Rate board:** draw it as a card at `rate_board`. The wall board is too small to carry 28 px text.
- **Merge:** `public/assets/stations/s03/` from this branch replaces the grey-box renders. Task 03's `s03_build.py` and `s03_weigh.blend` stay as they are; this set builds from its own script and `.blend`.

## Still open

- The Commons form references for the platform scale and the crate (task 14) are not done.
- 1280×720 is not checked; this pass looked at 1920×1080 only.
- The task 14 screenshots "as task 03, re-shot" need `Station03.ts`, so they come after the merge.
