# 10 · End card: the ledger and four beliefs

**Phase:** UI · **Depends on:** 08 · **Read first:** spec "The journey" (the end card), art bible §8 (end card frame), deck p. 1 (the arch-shaped signboard)

## Goal

After Run 2, one card shows the kilo's **ledger for both runs** side by side, then the **four before → after beliefs**, one at a time. Its frame is the deck's arch-shaped municipal signboard: a saffron board with red edging and ink text, drawn in Phaser.

## Content (use exactly)

New `src/data/endcard.json` (with a schema in `src/data/schema/endcard.schema.json`):

```json
{
  "title": "The same kilo",
  "ledger": {
    "1": { "heading": "Run 1 · Today", "lines": [
      { "text": "Waste collection fee", "value": "−₹5", "meaning": "cost", "evidence": ["C-fee-southfirst", "C-fee-tnm"] },
      { "text": "Leftover meat in the power cut", "value": "Lost", "meaning": "cost", "evidence": ["D-p22"] }
    ] },
    "2": { "heading": "Run 2 · With the hub", "proposed": true, "lines": [
      { "text": "Sorted waste at the hub", "value": "+₹[__]", "meaning": "income", "evidence": ["SPEC-journey"] },
      { "text": "Leftover meat in Chamber A", "value": "Kept", "meaning": "income", "evidence": ["SPEC-journey"] }
    ] }
  },
  "payout_note": "₹[__]/kg: the payout is not set. No source shows a renderer paying vendors; in the Kerala precedent, shops pay.",
  "beliefs": [
    { "before": "Waste is my problem to dump cheaply", "after": "My waste is worth money if I keep it clean" },
    { "before": "Anything official will cost me money", "after": "The hub is the market's own" },
    { "before": "A fridge isn't worth it with these power cuts", "after": "I can keep stock cold without buying one" },
    { "before": "Leftover meat is a loss I just take", "after": "Leftovers wait overnight in Chamber A, free" }
  ],
  "beliefs_evidence": ["SPEC-journey", "D-p22", "D-p19"],
  "replay": "Play again",
  "blueprint": "Open the full blueprint"
}
```

The belief rows are the spec's re-paired rows. Its "Open decisions" asks for them to be approved, so add a `"check": "pending approval (spec Open decisions)"` key to the file. The card shows nothing about that.

## Files to touch

- `src/data/endcard.json`, `src/data/schema/endcard.schema.json`.
- `src/data/evidence-map.json`: no new ids.
- `src/game/scenes/EndCard.ts` (new; the scene key `EndCard` is what `flow.ts` already looks for). Register it in `main.ts` next to `Placeholder`. **That one line in main.ts is the only shared-file change allowed.**
  - Draw the arch frame in Phaser graphics after deck p. 1: a saffron (`pay`) board, red (`cost`) edging and ink text. The arch is decoration and carries no meaning, so this is the one place the meaning colours are used as decoration, as on the deck's title slide.
  - Show the two ledger columns, then the beliefs one at a time (Space or click advances), then the `payout_note` in small muted text, then two buttons: `replay` (restarts Run 1 from beat 0 with a fresh state) and `blueprint` (opens a full-screen list of all stations' blueprint rows for Run 2).

## Acceptance criteria

- [ ] All text matches the JSON exactly, and every value carries its word ("Lost", "Kept", "−₹5", "+₹[__]").
- [ ] `payout_note` is visible on the card without any click.
- [ ] The Run 2 column has a Proposed chip.
- [ ] Replay starts a clean Run 1 (tag cleared, blueprint closed).
- [ ] At 1280×720, every line is ≥ 19 px (art bible §8 minimums) and nothing is clipped.

## Screenshots

`review/end/{1920x1080,1280x720}-01-ledger.png`, `-02-belief-1.png`, `-03-belief-4.png`, `-04-buttons.png`.

## Questions

## Notes

## Blocked
