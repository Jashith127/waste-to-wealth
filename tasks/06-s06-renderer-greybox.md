# 06 · s06 Renderer (example), grey box (Run 2)

**Phase:** grey box · **Depends on:** 05 · **Read first:** spec row 6 and the truth rules (Renderer and Rendering steps)

## Goal

Off-site at a rendering plant, the player watches the material move through a **typical** process: size reduction, cooking, pressing out oil, drying, milling, then meal and oil. The plant is fictional and labelled **"Renderer (example)"**, and the steps are labelled **"Typical process"**. No real company, logo or place appears. This is the first off-site station, so its labels use `offsite` blue.

## Content (use exactly)

`src/data/stations/s06.json`:

- `number` 6 · `title`: `Renderer` · `label`: `Renderer (example)` · `place`: `Off-site` · `greybox`: true · `set.lighting`: `midday`
- `evidence`: `["SPEC-journey"]`. The research checkpoint ids for rendering (E0xx) will be added when `research/evidence.csv` arrives. Add the note `"Rendering evidence ids pending research/evidence.csv"` under the station's `params.evidence_note`.
- `runs["2"]`:
  - `summary`: `The material moves through a typical rendering process into meal and oil.`
  - `proposed`: true
  - `prompts`: `watch`: `Watch the process` · `leave`: `Follow the meal`
- `params`:
  ```json
  {
    "process_label": "Typical process",
    "steps": ["Size reduction", "Cooking", "Pressing out oil", "Drying", "Milling"],
    "outputs": ["Meal", "Oil"],
    "evidence_note": "Rendering evidence ids pending research/evidence.csv"
  }
  ```
- `blueprint["2"]` (all `proposed: true` except evidence):
  - frontstage: `—`. Leave it out.
  - backstage: `Renderer (example) processes the crates in a typical sequence.` [SPEC-journey]
  - support: `The collector agreement links the hub and the renderer.` [SPEC-journey]
  - evidence: `Rendering steps are a typical process, not a specific plant.` [SPEC-journey]

## Files to touch

- `src/data/stations/s06.json`.
- `art/scripts/s06_build.py` (new), grey box: five simple machines in a row, left to right, on a plant floor (no street slice: use `kit.plinth` only, with a grey floor material):
  - a hopper with a shredder for size reduction;
  - a horizontal cooker drum for cooking;
  - a press for pressing out oil;
  - a dryer drum for drying;
  - a mill for milling;
  - and two output bins (meal sacks, an oil drum).
  - Add one anchor per machine (`step_0` … `step_4`, and `out_meal`, `out_oil`) and `PROP_material`, a small grey heap that travels.
- `src/game/scenes/stations/Station06.ts` (new):
  - **watch:** the material moves step by step, about 1.2 s per step, auto-advancing. Space skips to the next step. A blue (`offsite`) label card shows each step's name from `params.steps`. Show `process_label` and the station `label` together in the top-left prompt line.
  - At the end, show the two output labels, then **leave**.

## Acceptance criteria

- [ ] "Renderer (example)" and "Typical process" are on screen for the whole station.
- [ ] No brand, logo, company name or place name anywhere, including the renders.
- [ ] Step names match `params.steps` exactly and in order.
- [ ] Off-site labels use `offsite` blue with text. The tag stays docked.
- [ ] It auto-advances, Space skips, and the whole station takes 10 s or less untouched.

## Screenshots

`review/s06/{1920x1080,1280x720}-run2-01-start.png`, `-02-cooking.png`, `-03-outputs.png`, `-04-blueprint.png`.

## Questions

## Notes

## Blocked
