# 13 · Art: s02 The walk

**Phase:** final art · **Depends on:** 02, 11 · **Read first:** art bible (all of it, again), especially §0 sources, §2 scale, §3.3 colour rules, §4 materials, §6 composition, §7 signs and people; `review/s01/critique.md` (the mistakes already made once)

## Goal

Turn the s02 grey box into final art at Station 1's quality. It's the market street from the stall to the back of Russell Market. Keep **every object name, collection and anchor** from the grey box, so `Station02.ts` doesn't change.

## References (in order of preference)

- **Tier A:** F01 (the square: steel cart, blue tarp, minaret, hoardings, auto-rickshaws), F02 (stained façades, trilingual signs, wires), F04 (shopfronts). Crops R18–R22.
- **Tier B:** X03 (Russell Market façade, 2020) and X04 (entrance, 2023, white with the jali arch). The façade is **white with a pink ghost** (art bible §0, decided).
- **Gap:** the back lane of Russell Market. Look at Street View for proportions only (art bible §0, Tier D: never save or trace it), and record each link you use in `review/s02/references.md`. Search Commons for Tier B: `python tools/fetch_commons.py "Category:<name>"`. Every file you use must be added to `evidence-map.json` as an `X##` with its licence and credit.

## What to build (in `art/scripts/s02_build.py`)

1. **Shopfronts**, x −5…11: four or five fronts mixing open and closed shops, using `kit.shutter_bay`, `kit.pier`, `kit.shop_opening` and `kit.awning`. No two neighbours alike. At least two signs, each a new entry in `s02.json` `signs[]`:
   - styles from `tools/render_signs.mjs`;
   - text only from trades in our deck (saree, flowers, sweets and chaat, meat), with Kannada from the deck pages;
   - no real shop names.
2. **Anthony's flower stall** (x ≈ 3), after the deck's description (p. 14: flowers kept in the stall overnight; jasmine and marigold at the Basilica gate, p. 34). It's a small wooden stall with marigold and jasmine heaps. **No church façade:** we have no photo of the Basilica, so the stall sits at a street corner.
3. **Russell Market corner** (x 11…15): white masonry with arched bays and a pink ghost (X03, X04), and the back-lane pile in Run 1 (`PROP_litter`: grey-white sacks and loose waste, matte, **no gore**).
4. **Street life** from F01: an auto-rickshaw parked at the kerb, built from kit-style bevelled boxes and unbranded; a hoarding frame **with no faces** (art bible §7); overhead wires.
5. **Run 2's cleaner pavement:** the same set without `PROP_litter`. The scene already hides it.

People: Riyaz walking (reuse `people.figure`, with an arm-swing pose pair if you want: `CHAR_riyaz_walk_a` and `_b`), and Anthony and Arif with costumes from photo *types* (art bible §7), not likenesses. Anthony: a flower seller in a vest and lungi or a shirt. Arif: a shopkeeper in a kurta. Keep their head anchors.

## Acceptance criteria

- [ ] Station 1's standard: compare your screenshots next to `review/s01/1920x1080-01-start.png` and write a short `review/s02/critique.md` against the art bible, as `review/s01/critique.md` does. At least two critique passes, with the fixes made.
- [ ] Every new prop and material traces to a reference id listed in the build script's comments.
- [ ] `check_palette.py s02` passes.
- [ ] Readable signs use only deck-sourced trades and Kannada. Each Urdu line has a `check` note. No real names or numbers.
- [ ] No faces on hoardings, no brand on the auto-rickshaw, no gore in the pile.
- [ ] The overhang rule holds: Riyaz is never hidden by an awning, and nothing needed sits below y 660.
- [ ] The grey-box screenshots' states all still work (same names and anchors).

## Screenshots

The same list as task 02, re-shot, plus `review/s02/critique.md` and `review/s02/references.md`.

## Questions

## Notes

## Blocked
