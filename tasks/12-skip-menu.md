# 12 · Skip menu

**Phase:** UI · **Depends on:** 08, 10 · **Read first:** patterns §4 (state and URL params)

## Goal

A reviewer can jump to any beat of either run, or restart. M opens the menu (as does a small "≡" button left of the "i"). Esc or M closes it.

## Content (use exactly)

Add to `src/data/hud.json`:

```json
"menu": {
  "title": "Jump to",
  "restart": "Restart from the beginning",
  "reduced_motion": "Reduced motion",
  "close": "Close"
}
```

Row labels come from `runs.json` (`title`) and each station's `number · title`, with " (night)" for variants.

## Files to touch

- `src/data/hud.json`.
- `src/game/scenes/SkipMenu.ts` (new). An overlay scene launched on top of the current one (`scene.launch`), which pauses the station underneath. It has two columns, Run 1 and Run 2, one row per beat, plus the end card.
  - Choosing a row sets `state` (`run`, `beat`, and a sensible kilo tag for that point: none before s01, −₹5 before s03, `+₹[__]` from s03 on in Run 2) and starts that beat through `StationCard`.
  - Add a reduced-motion toggle that writes `state.reducedMotion`.
- `src/game/main.ts`: register the scene, **one line**. `StationScene.ts`: mount the "≡" button and the M key, **these two things only**.

## Acceptance criteria

- [ ] Every beat in `runs.json` can be reached from the menu and plays correctly from there.
- [ ] The kilo tag is right after every jump (rules above).
- [ ] The station underneath is paused while the menu is open: no auto-advance and no flicker timers firing.
- [ ] Keyboard only: arrows move, Enter chooses, Esc closes.

## Screenshots

`review/menu/{1920x1080,1280x720}-01-open.png`, `-02-after-jump-s05.png`.

## Questions

## Notes

## Blocked
