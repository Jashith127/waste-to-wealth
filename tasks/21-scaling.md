# 21 · Scaling: laptop to projector

**Phase:** polish · **Depends on:** 13–18 · **Read first:** spec "Open decisions: Review setup"; art bible §1 (2× master renders), §8 (minimum sizes)

## Goal

The game should look sharp and stay readable on a 1280×720 laptop, a 1920×1080 screen and a 4K projector, and work with touch. The review setup is still undecided (spec, "Open decisions"), so support all three.

## Files to touch

- `art/scripts/lib/rig.py`: **you may change only `RES_DRAFT` usage.** Add `--master` to `render_station.py`, which renders at `RES_MASTER` (3840×2160).
- `tools/pack_layers.py`: write `@2x` variants when master renders exist, and convert shipped PNGs to **WebP (lossless for alpha layers, quality 92 for `bg`)**. Add `"scale": 2` entries to `layers.json` so positions stay in 1920-space.
- `StationScene.loadLayers()`: load `@2x` when `window.devicePixelRatio * innerWidth > 2400`, and place layers using 1920-space positions divided by the texture scale. **Only `loadLayers` and `layer()` may change.**
- Touch: check that every hotspot is at least 64 × 64 px at 1280×720 (art bible §8 minimums), and that drags work with touch in s03 and s04.

## Acceptance criteria

- [ ] Screenshots at 1280×720, 1920×1080 and 3840×2160 (Playwright `deviceScaleFactor: 2` at 1920×1080) of s01 and one more station show sharp sets. At 4K, there is no visible upscaling blur on the sign text.
- [ ] Total shipped asset size per station is under 3 MB at 1×. Report sizes in `review/scaling/sizes.md`.
- [ ] Touch-only play (Playwright `hasTouch`) completes s01, s03 and s04.
- [ ] Smallest text at 1280×720 is ≥ 16 px rendered (art bible §8: body 19 px). List any exceptions.

## Screenshots

`review/scaling/s01-1280.png`, `-1920.png`, `-4k.png`; the same for s03; and `review/scaling/sizes.md`.

## Questions

## Notes

## Blocked
