# 07 · s07 Farm and back to the stall: How it could close (Run 2)

**Phase:** grey box · **Depends on:** 06 · **Read first:** spec row 7 and the truth rule "Farm loop"

## Goal

The meal goes to a poultry farm as feed. The loop closes back at a chicken-and-mutton stall like Riyaz's. **No supply chain back to the stall was found**, so this whole station is labelled **"How it could close"**. Its only cited precedent is Kannur.

## Content (use exactly)

`src/data/stations/s07.json`:

- `number` 7 · `title`: `Farm → back to the stall` · `label`: `How it could close` · `place`: `A poultry farm, then Cockburn Road` · `greybox`: true · `set.lighting`: `midday`
- `evidence`: `["SPEC-journey", "C-kannur", "D-p22"]`
- `runs["2"]`:
  - `summary`: `Meal as poultry feed, and chicken back at the stall: how the loop could close.`
  - `proposed`: true
  - `prompts`: `watch`: `How it could close` · `leave`: `See the day's ledger`
- `params`:
  ```json
  {
    "beats": [
      { "caption": "Meal becomes poultry feed", "anchor": "feed" },
      { "caption": "Chickens raised on the farm", "anchor": "flock" },
      { "caption": "Back on the counter at the stall", "anchor": "stall" }
    ],
    "precedent": "Precedent: Kannur, Kerala",
    "caveat": "No supply chain back to the stall was found"
  }
  ```
- `blueprint["2"]` (all `proposed: true` except evidence):
  - backstage: `Meal sold as feed to a poultry farm.` [SPEC-journey, C-kannur]
  - frontstage: `Chicken back at a stall like Riyaz's.` [SPEC-journey, D-p22]
  - evidence: `Kannur precedent; no supply chain back to the stall was found.` [C-kannur, SPEC-journey]

## Files to touch

- `src/data/stations/s07.json`.
- `art/scripts/s07_build.py` (new), grey box in two parts on one plinth:
  - the left half is a farm shed (open-sided, a feeder trough, anchor `feed`), with a few chickens as simple grey shapes (anchor `flock`);
  - the right half is the S1 stall frontage as a grey block (anchor `stall`).
  - The camera pans left to right, as in s02.
- `src/game/scenes/stations/Station07.ts` (new):
  - **watch:** auto-pan through the three `params.beats`, about 1.5 s each, with a caption card at each anchor. Show `label` in the prompt line throughout, and `precedent` and `caveat` together as a small card, with the caveat in the muted colour.
  - Then **leave**, which goes to the `end` beat. The end card comes in task 10; until then the placeholder shows.

## Acceptance criteria

- [ ] "How it could close" is visible for the entire station, not only in the card.
- [ ] The caveat sentence is on screen with the precedent. It's never hidden behind a click.
- [ ] No farm brand, place name (other than "Kannur, Kerala" in the precedent line), or numbers of birds or feed.
- [ ] Everything except the evidence lane is Proposed.
- [ ] `check_palette.py s07` passes.

## Screenshots

`review/s07/{1920x1080,1280x720}-run2-01-feed.png`, `-02-flock.png`, `-03-stall.png`, `-04-blueprint.png`.

## Questions

## Notes

## Blocked
