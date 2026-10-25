# 14 · Art: s03 Weigh-in and payment

**Phase:** final art · **Depends on:** 03, 13 · **Read first:** art bible §0 gaps (platform scale, crates), §3.2 (hub crates use meaning colours), §4 ("things the hub proposes look clean but not shiny"); `review/s01/critique.md`

## Goal

Final art for the hub's front counter. The hub is **our proposal**, so per art bible §4 its fittings (counter, scale, crates, rate board) look **new and clean, but not shiny**. They sit inside the worn market fabric of Russell Market's white masonry, which makes the hub visibly a new thing. Keep every name and anchor from task 03.

## References

- **Tier A:** F04 (steel counter tops, the photo-menu board as a model for the rate board's density), F03 (red crates: form only).
- **Tier B:** X05 (Russell Market's meat-section counters: blue-and-white checker tiles, R25). Use those tiles on the counter front; they tie the hub to the market.
- **Gaps:** a platform scale and stackable crates. Search Commons for form references (`"platform scale"`, `"plastic crate"`), and record licence and credit. Form only: no brand marks.

## What to build

1. **The counter**: steel top, front in `m["tiles_checker"]` (R25), with a gap where the scale sits.
2. **The platform scale**: low steel platform, a column and a small digital head. The display stays blank in the render; Phaser draws `1.0 kg`.
3. **The crate** (`PROP_crate`): ribbed, stackable, with handholds, 0.55 × 0.36 × 0.30 m. Colour: **blue (`offsite`, Chamber B)**, because the waste leaves the market (art bible §3.2). Use the exact meaning blue on the *crate* (it is meaning), but give it a plastic material with a subtle fade (`M.plastic`).
4. **The rate board**: a clean flex board on the back wall, blank in the render. Phaser draws its lines from `params.rate_board`. Give it the flex-banner frame look from the Station 1 fascia.
5. **The attendant**: a hub uniform. This is our proposal, so keep it simple: a plain shirt in a muted colour that isn't a meaning colour, and a lanyard. Two poses: idle and type.
6. **Riyaz**, as in s01 (same costume materials, wet hands), without the cleaver.

## Acceptance criteria

- [ ] Two critique passes in `review/s03/critique.md`.
- [ ] The crate is the only meaning-coloured object in the set, and only the meaning blue. `check_palette.py s03` passes. If the checker flags the crate, add it to an allow-list *inside the checker* as `s03/crate.png`, with a comment pointing here.
- [ ] Scale and crate have no brand marks or digits in the render.
- [ ] The hub fittings read as new against the worn masonry, without looking like a sci-fi panel (spec "Avoid").

## Screenshots

As task 03, re-shot, plus `review/s03/critique.md` and `references.md`.

## Questions

## Notes

## Blocked
