# 01 · s01 night variant: the end of Run 1

**Phase:** grey box · **Depends on:** nothing · **Read first:** patterns §3 "Variants", §1 commands; art bible §5 (night column)

## Goal

Run 1 ends back at the stall that night. The power goes out and the leftover meat spoils, because the stall's cooler is on mains power. `runs.json` already lists the beat as `"s01:night"`, after `s02`. It reuses the Station 1 set, re-lit, with a tray of leftovers on the counter.

## Content (use exactly)

Add to `src/data/stations/s01.json` → `runs["1"].prompts`:

| key | text |
|---|---|
| `night` | `That night, the power goes out` |
| `night_leave` | `Start the day again, with the hub` |

Add `params.leftovers`:

```json
"leftovers": {
  "tag": { "value": "Lost", "meaning": "cost", "note": "Leftovers spoil without power" },
  "evidence": ["D-p22", "D-p23", "SPEC-journey"]
}
```

Add to `blueprint["1"]` nothing: the night beat shows the same Run 1 rows.

## Files to touch

- `art/scripts/s01_build.py`: add a `PROP_leftovers` collection holding a steel tray (about 0.45 × 0.3 m, `m["steel"]`) with three cut pieces (`m["meat"]`). Put it on the counter top at x ≈ 0.05, y ≈ 2.5, between the kilo spot and the block, without overlapping either. Add `st.anchor("leftovers_centre", ...)` and a shadow catcher, as for the kilo.
- `src/game/scenes/stations/Station01.ts`: when `this.variant === 'night'`:
  - Use `bg_night`, `riyaz_idle_night` and `leftovers_night`. No kilo, no chopping.
  - Show the `night` prompt. After 1.2 s, fade the leftovers layer to 85% brightness with a tint of `0xB8A89A` (the spoiling cue; no gore) and hang a `KiloTag` from `leftovers_centre` with the `params.leftovers.tag` content.
  - Then show the `night_leave` prompt with `→`. `→` (or the button) calls `this.leave()`, which starts Run 2.
- `src/data/stations/s01.json`: the content above.
- `tools/shoot.mjs`: add a `s01-night` script (see Screenshots).

## Render

```bash
blender -b --python art/scripts/s01_build.py
blender -b art/blender/s01_stall.blend --python art/scripts/render_station.py -- --preset night --power-cut
blender -b art/blender/s01_stall.blend --python art/scripts/render_station.py -- --only leftovers,leftovers_shadow
python tools/pack_layers.py s01
```

The day render must not show the leftovers. Hide `PROP_leftovers` in day beats from the scene code (don't place the layer), not by deleting it.

## Acceptance criteria

- [x] `?run=1&beat=2` opens the night beat directly. Walking Run 1 from the start reaches it after s02.
- [x] Night frame: the tube light, bulb and cooler glow are all off (`--power-cut`), and the sky is the night preset. The cooler does not flicker.
- [x] The leftovers tray reads as a steel tray of meat at 1280×720, and its "Lost" tag hangs beside it, never over it.
- [x] `→` goes to the "Run 2 · With the hub" card, then s01 in its day state with the kilo tag cleared.
- [x] Day beats of s01 look exactly as before (compare with `review/s01/1920x1080-01-start.png`).
- [x] `python tools/check_palette.py s01` passes.

## Screenshots

`review/s01/{1920x1080,1280x720}-night-01-dark.png`, `-night-02-lost.png` and `-night-03-run2-card.png`.

## Out of scope

Sound (task 19), and any change to the HUD clock (task 09).

## Questions

## Notes

- Changed: added the s01 night variant (power-cut set, night Riyaz, leftover tray, Lost tag, Run 2 exit), its Blender prop, and the night/day layer renders.
- Check: at 1280×720 the tray is dim but readable beside the Lost card; `→` shows the Run 2 card and s01 returns with the kilo tag cleared.
- Uncertain: the tray sits at x −0.04 rather than +0.05 so it clears the kilo and block; the night frame is deliberately very dark.

## Blocked
