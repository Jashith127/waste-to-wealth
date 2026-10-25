# 23 · README

**Phase:** polish · **Depends on:** 22 · **Read first:** everything in `docs/`

## Goal

A `README.md` at the repo root that lets a new teammate or a reviewer run the game in five minutes and understand what's real, what's proposed and what's still a placeholder.

## Content (sections, in this order)

1. **What this is:** two sentences from the spec's summary, and a link to `docs/game-concept.md`.
2. **Play it:** `npm install`, `npm run dev`, then open `http://localhost:8080`. The keys:
   - Space or click: act;
   - →: walk on;
   - B: blueprint;
   - I: evidence;
   - C: captions;
   - M: skip menu;
   - Esc: close.
   Then the URL params `?run=2&beat=3`, `?station=s04` and `?reducedMotion`.
3. **Build:** `npm run build` (output in `dist/`), `npm run check`.
4. **How it's made:** link to `docs/patterns.md` and `docs/art-bible.md`, with the pipeline diagram from patterns §1.
5. **Truth rules:** the table from the spec, unchanged, plus a pointer to the evidence card (I) in the game.
6. **Credits:**
   - the team names from the deck title slide (p. 1), exactly as written there;
   - the CC BY-SA photo credits, generated from `field/external/commons/credits.json` (author, licence, link);
   - "© OpenStreetMap contributors, ODbL";
   - Phaser (MIT) and the template licence in `docs/licenses/`;
   - Google Fonts (OFL).
7. **Still placeholder:** the `"check"` warnings from `npm run check`, plus anything listed in `review/s01/critique.md` under "Still open".

## Files to touch

`README.md` (new) and `tools/credits.mjs` (new), which prints the credits section from `credits.json` and `evidence-map.json` so it never drifts.

## Acceptance criteria

- [ ] A clean clone, then `npm install && npm run dev`, works by following the README alone. Test it in a fresh folder.
- [ ] Every external photo used in the game is credited, and `tools/credits.mjs` output matches the README.
- [ ] No claim in the README goes beyond the spec. Copy its wording for the truth rules.

## Questions

## Notes

## Blocked
