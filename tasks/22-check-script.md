# 22 · The check script

**Phase:** polish · **Depends on:** everything before · **Read first:** spec "Truth rules"; patterns §2 and §7; `src/data/schema/*`

## Goal

One command, `npm run check`, that fails loudly if the game breaks a truth rule, cites a missing source, ships a bad colour or doesn't build. The lead runs it before every review.

## Files to touch

- `package.json`: add `"check": "node tools/check.mjs"`, and add `ajv` as a pinned devDependency (`npm install --save-dev --save-exact ajv@8.17.1 ajv-formats@3.0.1`).
- `tools/check.mjs` (new), which runs, in order, printing ✓ or ✗ for each:
  1. **Schemas.** Every file in `src/data/` validates against its schema in `src/data/schema/`. Any data file without a schema fails.
  2. **Evidence.** Every `evidence` id anywhere in `src/data/**/*.json` exists in `evidence-map.json`. Every `X##` and `M##` source has `licence` and `credit`. Every `file` path exists in the repo.
  3. **Truth rules:**
     - every `₹` amount in `src/data/**` is one of `₹5`, `₹3`, `₹[__]` (with an optional `/kg`, and `−` or `+`);
     - the strings "₹5/kg" and "₹3/kg" appear only next to "animal waste" and "bone" respectively;
     - no `payout` or `rate` field holds a digit;
     - `s06.label` is exactly `Renderer (example)` and `s07.label` is exactly `How it could close`;
     - every `blueprint` row whose evidence is only `SPEC-*` has `"proposed": true`, and the same goes for run summaries whose station is s03–s07;
     - no string matches a real-name blacklist kept in `tools/check-blacklist.txt`: start it with the real shop and people names visible in F02 and F04, and the brand names in F01 and F02.
  4. **Pending checks.** List every `"check"` key (translations, approvals, missing tables) as a warning, not a failure. This list feeds `review/final.md`.
  5. **Assets.** Every station in `runs.json` that has a scene file has `public/assets/stations/<id>/pack.json`, and every key there resolves to a file. Then run `python tools/check_palette.py`.
  6. **Safety.** No `.blend` outside `art/`, no file larger than 15 MB in `public/`, and every `art/scripts/*.py` that saves a `.blend` imports `safety`.
  7. **Build.** `npx tsc --noEmit`, then `npm run build`.

## Acceptance criteria

- [ ] `npm run check` passes on the current repo, or every failure it finds is fixed in data or art (not by loosening the check), or reported to the lead in "Notes".
- [ ] Each truth-rule check has a failing fixture under `tools/check-fixtures/`, tested by `node tools/check.mjs --self-test`: for example, a station JSON with `"₹12/kg"`, or a hub blueprint row without `proposed`.
- [ ] Runs in under 60 s without the build step (`--fast` skips step 7).

## Screenshots

None. Paste the output of `npm run check` under "Notes".

## Questions

## Notes

## Blocked
