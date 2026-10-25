# 05 · s05 Bulk pickup, grey box (Run 2)

**Phase:** grey box · **Depends on:** 04 · **Read first:** patterns §3, §4 (the docked tag); spec row 5 and "From station 5 the camera follows the crate"

## Goal

The authorised collector's truck backs up to the hub, and one pickup takes many crates. The player taps to load. From here on, **the camera follows the crate**, not Riyaz: Riyaz isn't in this scene. The tag stays `+₹[__]` and is docked in the HUD.

## Content (use exactly)

`src/data/stations/s05.json`:

- `number` 5 · `title`: `Bulk pickup` · `place`: `The hub's loading bay` · `greybox`: true · `set.lighting`: `midday`
- `evidence`: `["SPEC-journey", "C-fee-southfirst", "C-fee-tnm", "D-p35"]`
- `runs["2"]`:
  - `summary`: `One pickup replaces many; an authorised collector takes the sealed crates.`
  - `proposed`: true
  - `prompts`: `load`: `Tap to load the crates` · `leave`: `Follow the crate`
- `params`:
  ```json
  {
    "crates_to_load": 6,
    "truck_label": "Authorised collector",
    "one_for_many": "One pickup replaces many"
  }
  ```
  `crates_to_load` is staging (how many crates sit in the bay), not a claim. Don't show it as a statistic.
- `blueprint["2"]` (all `proposed: true` except evidence):
  - vendor: `—`. Leave the vendor lane out: Riyaz has gone back to his stall.
  - frontstage: `One pickup from the hub replaces many from single stalls.` [SPEC-journey]
  - backstage: `An authorised collector under the collector agreement.` [SPEC-journey]
  - support: `The association schedules pickups.` [SPEC-journey]
  - evidence: `Hub concept note; outside services shape the vendor's day.` [SPEC-journey, D-p35]

## Files to touch

- `src/data/stations/s05.json`.
- `art/scripts/s05_build.py` (new), grey box:
  - the hub's side wall and a loading bay at kerb height;
  - a small generic truck (a cab box and a cargo box, no branding, `TRUCK_*`, anchor `truck_bay`);
  - six crates in two stacks (`PROP_crate_0` … `PROP_crate_5`, each with a `_centre` anchor). Crate 0 is *our* kilo's crate; add anchor `crate_0_knot`.
- `src/game/scenes/stations/Station05.ts` (new):
  - Each tap (or Space) moves the next crate into the truck (a 300 ms arc). Our crate (0) goes last, and its docked tag gives a small bounce when it's loaded.
  - After the last crate, show `params.one_for_many` as a caption card with a Proposed chip. Then **leave**: the truck slides off right, and the transition follows.
  - The truck label comes from `params.truck_label`, drawn as a Phaser card over `truck_bay`, never baked into the render.

## Acceptance criteria

- [ ] Riyaz is not in the scene, and the tag stays docked top-right showing `+₹[__]`.
- [ ] The truck carries no brand, name or number plate text.
- [ ] Space alone completes the station, and so does tapping.
- [ ] The caption and truck label carry a Proposed chip.
- [ ] `check_palette.py s05` passes.

## Screenshots

`review/s05/{1920x1080,1280x720}-run2-01-start.png`, `-02-loading.png`, `-03-loaded.png`, `-04-blueprint.png`.

## Questions

## Notes

## Blocked
