# 17 · Art: s06 Renderer (example)

**Phase:** final art · **Depends on:** 06, 16 · **Read first:** spec truth rules (Renderer, Rendering steps); art bible §0 gap ("generic process, labelled typical; simplified machines with no named brand"), §6 ("Avoid: heavy particles, neon gradients, sci-fi panels")

## Goal

Final art for the fictional rendering plant: five simplified machines in a row on a shed floor, generic and unbranded. It should read as a working industrial shed, not a factory advert. Keep every name and anchor from task 06.

## References

- **Tier A:** F03 (the kitchen's steel, hood, drum and haze: the art bible allows "a faint charcoal-smoke haze in kitchens"; one light haze here is fine).
- **Gap:** rendering machinery. Commons form references only, labelled as typical (`"rendering plant"`, `"industrial cooker"`, `"screw press"`, `"hammer mill"`), with licence and credit. Simplify each machine to three or four readable shapes.

## What to build

1. **Shed:** a corrugated roof edge cropped at the top of the frame, a concrete floor with stains, and steel columns.
2. **Machines** (left to right, one per `step_N` anchor):
   - a hopper with a shredder;
   - a long horizontal cooker drum with insulation bands;
   - a screw press with an oil tray;
   - a dryer drum;
   - a mill with a dust hood.
   Connect them with simple conveyors.
3. **Outputs:** stacked woven sacks (meal) and a steel drum (oil). No labels on them.
4. **Material** (`PROP_material`): a matte brownish heap that changes in Phaser (tint per step). No gore.
5. **Lighting:** the midday preset and high windows. No coloured lights.

## Acceptance criteria

- [ ] Two critique passes in `review/s06/critique.md`.
- [ ] No text, brand, logo or place in the renders.
- [ ] Each machine reads distinctly at 1280×720 with its step label shown.
- [ ] `check_palette.py s06` passes.

## Screenshots

As task 06, re-shot, plus `critique.md` and `references.md`.

## Questions

## Notes

## Blocked
