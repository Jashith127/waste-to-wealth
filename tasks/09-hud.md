# 09 · HUD: the time-of-day clock and the phone corner

**Phase:** UI · **Depends on:** 08 · **Read first:** spec "The HUD shows only three things"; art bible §6.3 (HUD band), §8 (type, motion)

## Goal

The HUD shows exactly three things:
- the **time-of-day clock** (top-left, left of the prompt pill);
- **the kilo's tag** (already done: hanging, or docked top-right);
- the **phone corner** (bottom-right), which lights up for the UPI ping.

Nothing else is ever added to the HUD.

## Content (use exactly)

New `src/data/hud.json` (add a schema `src/data/schema/hud.schema.json`, following the existing ones):

```json
{
  "clock": {
    "phases": { "morning": "Morning", "midday": "Midday", "night": "Night" },
    "note": "Shows the part of the day, never a clock time: no times are evidenced except vendor hours."
  },
  "phone": { "ping_label": "Paid", "proposed": true }
}
```

The clock's phase for each beat is the station's `set.lighting` (the night variant uses `night`).

## Files to touch

- `src/data/hud.json`, `src/data/schema/hud.schema.json`.
- `src/game/ui/Clock.ts` (new): a small card (about 150 × 60) holding a sun or moon arc dial and the phase word, in Baloo 2 at 26 px. Draw it with Phaser graphics.
- `src/game/ui/PhoneCorner.ts` (new): a phone outline at bottom-right, sitting at x ≥ 1760, y ≥ 960, which is *inside* the blueprint area. When the blueprint is open, it moves up above the panel. `ping()` shows a saffron (`pay`) ring that expands twice with the word `Paid`, and emits nothing itself.
- `src/game/scenes/StationScene.ts`: **you may edit this one shared file, only to mount the clock and phone corner.** Create them in `create()`, and listen for the scene's `sfx` event `upi_ping` to call `phone.ping()`.
- Move the prompt pill right so it starts after the clock card. Change `layout.prompt.x` in `theme.ts`; that's the only theme change allowed.

## Acceptance criteria

- [ ] Every beat shows the right phase word, including Night on s01 night.
- [ ] No digits on the clock.
- [ ] The UPI ping in s03 lights the phone corner, which reads `Paid` with a Proposed chip, and the ring is saffron. It works with the blueprint open (the corner sits above the panel).
- [ ] Reduced motion: the ring doesn't expand; it shows for 1.5 s and hides.
- [ ] The HUD band holds only the clock, the prompt, the docked tag and the "i". Check every station's screenshots.

## Screenshots

`review/hud/{1920x1080,1280x720}-01-s01.png`, `-02-s03-ping.png`, `-03-s03-ping-blueprint.png`, `-04-s01-night.png`.

## Questions

## Notes

## Blocked
