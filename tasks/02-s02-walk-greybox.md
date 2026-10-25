# 02 · s02 The walk, grey box, both runs

**Phase:** grey box · **Depends on:** 01 · **Read first:** patterns §6 (the recipe), §3; spec "The journey", row 2

## Goal

Riyaz carries the kilo along the market street from the stall towards Russell Market. **Run 1:** he dumps it behind Russell Market, and the −₹5 stays on the tag. **Run 2:** he takes it to the hub inside the fixed drop window, along a cleaner pavement. The set is a longer street slice: the camera slides along it while the player walks.

## Content (use exactly)

Replace `src/data/stations/s02.json` content (keep `$schema`, `id`, `number`, `title`, `set`):

- `place`: `Market street to Russell Market`
- `set.street`: `{ "x0": -5, "x1": 15 }`. That's 20 m of frontage; the camera pans from x = 0 to x = 10.
- `evidence`: `["SPEC-journey", "M01", "D-p34", "C-fee-southfirst", "C-fee-tnm", "X03", "X04"]`
- `runs["1"]`:
  - `summary`: `The kilo is dumped behind Russell Market.`
  - `prompts`: `walk`: `Walk to the back of Russell Market` · `dump`: `Leave it on the pile` · `leave`: `Back to the stall`
- `runs["2"]`:
  - `summary`: `The kilo goes to the hub inside the fixed drop window.`
  - `proposed`: true
  - `prompts`: `walk`: `Walk to the hub` · `leave`: `Into the hub`
- `blueprint["1"]`:
  - vendor: `Carries the kilo to the back of the market and leaves it there.` [SPEC-journey]
  - frontstage: `No one receives it.` [SPEC-journey]
  - backstage: `City collection, charged at ₹5/kg animal waste.` [C-fee-southfirst, C-fee-tnm]
  - support: `—`. Leave the support lane out.
  - evidence: `Hub concept note; September 2026 fee reports.` [SPEC-journey, C-fee-southfirst, C-fee-tnm]
- `blueprint["2"]`:
  - vendor: `Carries the kilo to the hub inside the drop window.` [SPEC-journey], proposed
  - frontstage: `The hub's drop window is open.` [SPEC-journey], proposed
  - backstage: `The association sets the drop window.` [SPEC-journey], proposed
  - support: `A cleaner pavement: waste no longer left on the street.` [SPEC-journey], proposed
  - evidence: `Hub concept note.` [SPEC-journey]
- `params`: `{ "walk_seconds": 6, "pan_m": 10 }`. `walk_seconds` is the time to hold → for the whole walk, and it's a game-feel number, not a claim. **Don't show any distance or minutes on screen** (art bible §0: the walk is "a few hundred metres", with no number).

## Files to touch

- `src/data/stations/s02.json`: the content above.
- `art/scripts/s02_build.py` (new): a **grey box**, made with `st.m["grey"]` and `st.m["grey_dark"]`:
  - `kit.plinth`, then a row of shop fronts with `kit.pier` and `kit.shutter_bay` (grey boards), and `kit.upper_storey` across x −5…15.
  - At x 11…15, a grey block for the Russell Market corner. Mark it with a `kit.pier` of `m["masonry"]` (white with the pink ghost, art bible §0) so the art task knows where it goes.
  - `PROP_litter`: three or four grey sacks (`kit.kilo_bag` shapes scaled 1.6×, `m["grey_dark"]`) on the pavement at x 12–14. This is the Run 1 pile and dump spot. Add `st.anchor("dump", ...)` at its centre and `st.anchor("litter_centre", ...)`.
  - `CHAR_riyaz_walk`: Riyaz carrying the bag. Use `people.figure` with the right hand holding `kit.kilo_bag` at hip height and the costume from `s01_build.py`. Add `st.anchor("riyaz_hand", ...)` at the bag's knot.
  - Two placeholder figures for task 11: `CHAR_anthony_idle` at x ≈ 3, in front of a grey stall, and `CHAR_arif_idle` at x ≈ 7, in a shop doorway. Use plain grey costumes (`people.costume_materials(..., shirt="#9A958E", cap=None)`). Add anchors `anthony_head` and `arif_head`.
  - `st.finish(TARGET)` with `TARGET = (0, 3, 1.0)`. The scene pans by moving `world.x`. Don't add cameras.
- `src/game/scenes/stations/Station02.ts` (new):
  - Phase `walk`: holding → (or holding the pointer on the right half of the screen) moves `world.x` left over `walk_seconds` while Riyaz stays near the centre. Release to stop.
  - Run 1: at the end, phase `dump`. Space or a click on the pile moves the bag onto the pile, and the tag stays −₹5. Then `leave`.
  - Run 2: hide `litter` and `litter_shadow`, so the pavement is cleaner. At the end, `leave` goes straight on.
  - The tag hangs from `riyaz_hand` while walking, and is created from `state.kilo.tag`.

## Acceptance criteria

- [ ] Both runs can be walked through. Releasing → stops the pan, with no drift, and the walk takes about `walk_seconds` held.
- [ ] Run 1 shows the pile; Run 2 doesn't. The Run 2 blueprint rows carry Proposed chips.
- [ ] No distance, minute or time-of-day number appears anywhere on screen.
- [ ] The tag never covers Riyaz or the bag. Nothing the player needs sits below y 660 at any point in the pan.
- [ ] `check_palette.py s02` passes. The placeholder figures exist with their anchors, ready for task 11.

## Screenshots

`review/s02/{1920x1080,1280x720}[-run2]-01-start.png`, `-02-mid-walk.png`, `-03-end.png`, `-04-blueprint.png`, plus Run 1 only: `-05-dumped.png`.

## Out of scope

Final art (task 13), stakeholder cards (11), the clock (09).

## Questions

## Notes

## Blocked
