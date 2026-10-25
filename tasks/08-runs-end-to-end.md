# 08 · Run 1 and Run 2 end to end

**Phase:** grey box · **Depends on:** 01–07 · **Read first:** patterns §4 (state, flow); spec "The journey" (Run 1 about 60 s, the whole game about 5 minutes)

## Goal

Play the whole game from Run 1 · s01 to Run 2's end beat without a hitch, timed, and leave a repeatable script that does it.

## Files to touch

- `tools/shoot.mjs`: add a script `full` that starts at `?run=1&beat=0` and plays every beat with the keys each station uses. It takes one screenshot per beat at 1280×720 into `review/full/NN-<beat>.png`, and prints the elapsed time per beat and per run.
- Fix **only** bugs inside station scenes (`src/game/scenes/stations/*`) and station data. If a bug lives in a shared file (`flow.ts`, `StationScene.ts`, `state.ts`, the UI components), don't fix it. Write it up as a new task file `tasks/08a-<bug>.md` with steps to reproduce.

## Acceptance criteria

- [ ] `node tools/shoot.mjs full` completes both runs with no console errors (collect `page.on('console')` errors and fail on any).
- [ ] Run 1 plays s01 → s02 (dump) → s01 night, then the "Run 2 · With the hub" card.
- [ ] Run 2 plays s01 → s07 → end (placeholder until task 10).
- [ ] Timing, with the script's minimum inputs: Run 1 ≤ 75 s and the whole game ≤ 5 min 30 s. Record the per-beat times in "Notes". If over, list which beats are slow; don't cut content.
- [ ] The tag is right at every beat:
  - Run 1: −₹5, then "Lost" on the leftovers at night.
  - Run 2: −₹5 until s03, `+₹[__]` from s03 on.
  - It's cleared at the start of Run 2.
- [ ] B (blueprint) and I (evidence) work on every beat, and B's state persists across beats.
- [ ] Deep links work: `?run=2&beat=4` starts at s05 with a sensible tag. If a deep link needs state from earlier beats, the scene must default it; note any that don't.

## Screenshots

`review/full/*.png` (one per beat), plus a `review/full/timing.md` with the times.

## Questions

## Notes

## Blocked
