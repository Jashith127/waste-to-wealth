# 20 · Reduced motion

**Phase:** polish · **Depends on:** 08–12, 19 · **Read first:** patterns §3 ("Reduced motion"); art bible §8 (motion)

## Goal

With `prefers-reduced-motion: reduce` (or `?reducedMotion`, or the skip-menu toggle), nothing slides, shakes, pans, flickers, swings or pulses. Every state still reads, through cross-fades and static frames.

## Files to touch

- Audit every station scene, every UI component and `flow.ts`, `StationCard.ts`, `EndCard.ts` and `SkipMenu.ts`. List each tween, shake, camera pan, timer-driven flicker and pulsing ring in `review/reduced-motion/audit.md`, with its file and line and the reduced alternative used.
- Fix the station scenes and UI components yourself. For shared files (`StationScene.ts`, `flow.ts`), **you may make only the reduced-motion changes the audit lists.**
- `tools/shoot.mjs`: the `--reduced` flag already exists. Run every station with it.

Rules:
- camera shake: off;
- pans (s02, s07): cut to each stop;
- the fridge flicker: steady;
- hint rings: static;
- tag swing and flip: an instant swap;
- the walk-out slide: a fade only;
- auto-advancing steps: still advance, without movement.

## Acceptance criteria

- [ ] `audit.md` lists every motion in the game with its reduced alternative.
- [ ] `node tools/shoot.mjs <sid> --reduced` works for every station, and its screenshots show the same states as the normal ones.
- [ ] No animation longer than 240 ms remains in reduced mode, except fades.

## Screenshots

`review/<sid>/*-reduced-*.png` for every station.

## Questions

## Notes

## Blocked
