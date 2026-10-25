# Tasks

One file per unit of work, in order. Each is sized for one session. Do them in number order; a task may depend on any earlier one.

## Before you start any task

1. Read [docs/patterns.md](../docs/patterns.md) once, end to end. Re-read the sections the task points to.
2. Read the task file to the end before touching anything.
3. Look at Station 1. It's the worked example: `src/data/stations/s01.json`, `art/scripts/s01_build.py` and `src/game/scenes/stations/Station01.ts`.

## While you work

- **Content.** Use the exact strings the task gives, with the evidence ids it gives. If you need a line, number or prop the task doesn't give, **don't make it up**. Stop and write the question under "Questions" at the bottom of the task file.
- **Truth rules** (spec, "Truth rules"):
  - Fees are ₹5/kg animal waste and ₹3/kg bone.
  - The payout is always `₹[__]/kg` (tag `+₹[__]`), never a number.
  - The renderer is always "Renderer (example)".
  - Station 7 is labelled "How it could close".
  - Every hub detail is marked Proposed.
  - Art comes from our photos (art bible §0).
  - No real shop names, people or phone numbers (art bible §7).
- **Shared files.** Don't edit `StationScene.ts`, `flow.ts`, `state.ts`, `content.ts`, `theme.ts`, `src/game/ui/*`, `art/scripts/lib/*` or `render_station.py` unless the task says to. If you can't finish without changing one, mark the task blocked (below).
- **Blender.** Changes go through scripts only; the scripts back up the `.blend`. Never run anything that writes outside `art/`.

## When you finish

- Every acceptance box is ticked. Tick them in this file as you go.
- The screenshots the task lists exist and you've looked at them. Note anything that looks wrong under "Notes".
- `npx tsc --noEmit` and `npm run build` pass.
- Commit: `NN-name: <summary>`, with the screenshot paths in the body.

## If you are blocked

Rename the file to `NN-name-blocked.md`, write what blocked you and what you tried under "Blocked", commit, and move to the next task that doesn't depend on it. The lead picks up blocked tasks.

## The list

| # | Task | Phase |
|---|---|---|
| 01 | [s01 night variant (Run 1 ending)](01-s01-night-variant-done.md) | Grey box |
| 02 | [s02 The walk, both runs](02-s02-walk-greybox.md) | Grey box |
| 03 | [s03 Weigh-in and payment](03-s03-weigh-in-greybox.md) | Grey box |
| 04 | [s04 Cold room](04-s04-cold-room-greybox.md) | Grey box |
| 05 | [s05 Bulk pickup](05-s05-pickup-greybox.md) | Grey box |
| 06 | [s06 Renderer (example)](06-s06-renderer-greybox.md) | Grey box |
| 07 | [s07 How it could close](07-s07-loop-greybox.md) | Grey box |
| 08 | [Run 1 and Run 2 end to end](08-runs-end-to-end.md) | Grey box |
| 09 | [HUD: clock and phone corner](09-hud.md) | UI |
| 10 | [End card](10-end-card.md) | UI |
| 11 | [Stakeholder cards](11-stakeholder-cards.md) | UI |
| 12 | [Skip menu](12-skip-menu.md) | UI |
| 13 | [Art: s02 The walk](13-art-s02-walk.md) | Final art |
| 14 | [Art: s03 Weigh-in](14-art-s03-weigh-in.md) | Final art |
| 15 | [Art: s04 Cold room](15-art-s04-cold-room.md) | Final art |
| 16 | [Art: s05 Bulk pickup](16-art-s05-pickup.md) | Final art |
| 17 | [Art: s06 Renderer](17-art-s06-renderer.md) | Final art |
| 18 | [Art: s07 Farm and the loop](18-art-s07-loop.md) | Final art |
| 19 | [Captions and sound hooks](19-captions-and-sound.md) | Polish |
| 20 | [Reduced motion](20-reduced-motion.md) | Polish |
| 21 | [Scaling: laptop to projector](21-scaling.md) | Polish |
| 22 | [The check script](22-check-script.md) | Polish |
| 23 | [README](23-readme.md) | Polish |
