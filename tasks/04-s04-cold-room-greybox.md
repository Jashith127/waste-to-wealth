# 04 · s04 Cold room, grey box (Run 2)

**Phase:** grey box · **Depends on:** 03 · **Read first:** patterns §3; spec row 4; art bible §3.2 (Chamber A green, Chamber B blue)

## Goal

Inside the hub there are two chambers behind two doors that are never shared. Riyaz puts the sorted waste crate into **Chamber B** (blue, it leaves the market) and his unsold meat into **Chamber A** (green, it waits overnight, free). Then the power cuts out, and solar keeps both chambers cold. Everything here is our proposal.

## Content (use exactly)

`src/data/stations/s04.json`:

- `number` 4 · `title`: `Cold room` · `place`: `The hub, inside` · `greybox`: true · `set.lighting`: `midday`
- `evidence`: `["SPEC-journey", "D-p22", "D-p19", "D-p20"]`
- `runs["2"]`:
  - `summary`: `Waste goes to Chamber B, unsold meat to Chamber A; solar carries through the power cut.`
  - `proposed`: true
  - `prompts`:
    - `waste`: `Put the crate in Chamber B`
    - `meat`: `Put the unsold meat in Chamber A`
    - `cut`: `The power goes out`
    - `solar`: `Solar keeps both chambers cold`
    - `leave`: `To the pickup bay`
- `params`:
  ```json
  {
    "chambers": {
      "A": { "label": "Chamber A", "sub": "Unsold meat · waits overnight, free", "meaning": "income" },
      "B": { "label": "Chamber B", "sub": "Sorted waste · sealed crates", "meaning": "offsite" }
    },
    "rule": "Two doors, never shared",
    "solar_label": "Solar"
  }
  ```
- `blueprint["2"]` (all `proposed: true` except evidence):
  - vendor: `Sorts waste into sealed crates in Chamber B; puts unsold meat in Chamber A.` [SPEC-journey]
  - frontstage: `Two doors, never shared.` [SPEC-journey]
  - backstage: `Chamber B crates wait for the bulk pickup.` [SPEC-journey]
  - support: `Solar unit keeps both chambers cold through power cuts.` [SPEC-journey, D-p22]
  - evidence: `Persona: power cuts put stock at risk; interview 03: "a good fridge".` [D-p22, D-p19, D-p20]

## Files to touch

- `src/data/stations/s04.json`.
- `art/scripts/s04_build.py` (new), grey box:
  - a room interior with two insulated doors side by side, each about 0.9 × 2.0 m, 1 m apart, on the back wall (`DOOR_A`, `DOOR_B`; anchors `door_a` and `door_b`);
  - a small solar indicator box near the doors (anchor `solar`);
  - `PROP_crate` (the same dimensions as s03, `crate_centre`);
  - `PROP_meat_tray` (steel tray with three cut pieces, `meat_tray_centre`);
  - `FX_chamber_light`: a cool light inside each chamber, visible through a door window;
  - `CHAR_riyaz_idle`;
  - render with and without `--power-cut`, with the room lights tagged `practical` and the chamber lights in `FX_` (not practical: they run on solar).
- `src/game/scenes/stations/Station04.ts` (new):
  - Draw a thin colour strip and a label on each door from `params.chambers`: green for A and blue for B, **always with the word**, never colour alone.
  - Show `params.rule` as a small card between the doors.
  - Flow: **waste** (drag the crate to door B) → **meat** (drag the tray to door A) → **cut** (swap to the power-cut background; the chamber glow stays on) → **solar** (pulse the solar box) → **leave**.
  - Dragging to the wrong door springs the item back and shows `params.rule` once.

## Acceptance criteria

- [ ] Each door shows its word label as well as its colour. Chamber A is green and Chamber B is blue, matching `theme.ts`.
- [ ] Wrong-door drops are refused with the rule. The two doors are never shown open at once.
- [ ] In the power cut, the room goes dark but the chambers stay lit, and the solar label is visible.
- [ ] The tag stays `+₹[__]`, docked in the HUD (the kilo is in the crate now).
- [ ] `check_palette.py s04` passes. The door strips are UI drawn by Phaser, not baked into the render.

## Screenshots

`review/s04/{1920x1080,1280x720}-run2-01-start.png`, `-02-chamber-b.png`, `-03-chamber-a.png`, `-04-power-cut.png`, `-05-blueprint.png`.

## Questions

## Notes

## Blocked
