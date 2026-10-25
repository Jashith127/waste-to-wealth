# 15 · Art: s04 Cold room

**Phase:** final art · **Depends on:** 04, 14 · **Read first:** art bible §0 gaps ("Cold room with two chambers: no precedent. It is our proposal, so draw it generic and label it Proposed"), §4, §5 (power cut: what goes off)

## Goal

Final art for the two-chamber cold room inside the hub. With no precedent, it stays **generic and plain**: insulated panel walls, two sturdy cold-room doors with heavy latches, a small solar controller box with a cable running up and out. Keep every name and anchor from task 04.

## References

- **Tier A:** F03 (steel racks R16: use them inside the chambers), F04 (the cooler's form and glass from the s01 build script, `cooler()`).
- **Gap:** cold-room doors and panels. Commons form references only (`"cold room door"`, `"insulated panel"`), with licence and credit.

## What to build

1. **Room:** white insulated sandwich-panel walls with vertical seams every 1 m, a floor drain and a wet floor (`m["floor"]`), and a rubber kick strip at the base of each door. The room light is `practical` (off in the power cut).
2. **Doors A and B:** heavy latch handles and door windows showing the cold interior. Inside A, steel racks with trays; inside B, sealed blue crates stacked. The chamber lights are `FX_chamber_light` (solar, so *not* practical).
3. **Solar controller:** a small grey box with a status lamp and a conduit running up the wall. Its lamp is emissive, in `FX_` too.
4. The **door colour strips are drawn by Phaser** (task 04). Don't paint the doors green or blue in Blender.

## Acceptance criteria

- [ ] Two critique passes in `review/s04/critique.md`.
- [ ] In the power-cut render, the room is dark but the chamber windows and the solar lamp stay lit.
- [ ] Nothing reads as sci-fi: no glowing panels, no neon edges (spec "Avoid").
- [ ] `check_palette.py s04` passes, with blue crates inside B allowed as in task 14.

## Screenshots

As task 04, re-shot, plus `critique.md` and `references.md`.

## Questions

## Notes

## Blocked
