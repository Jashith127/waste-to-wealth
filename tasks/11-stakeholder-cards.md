# 11 · Stakeholder cards

**Phase:** UI · **Depends on:** 02, 03, 05, 07 · **Read first:** spec "Stakeholder cameos"; deck personas pp. 11 and 16

## Goal

Tapping a character opens a small card saying what that person wants. There are five characters:
- Anthony at the Basilica flower stall (s02);
- Arif at the saree shop (s02);
- the attendant (s03);
- the collector's driver (s05);
- a farm worker (s07).

## Content (use exactly)

New `src/data/stakeholders.json` (with a schema):

```json
{
  "anthony": { "name": "Anthony D.", "role": "Flower seller, St Mary's Basilica", "station": "s02",
    "wants": ["Buy only as many flowers as will sell within two days", "Keep his spot outside the Basilica", "Manage the daily market trip and long hours"],
    "evidence": ["D-p16", "D-p14"] },
  "arif": { "name": "Arif K.", "role": "Saree wholesaler, Shivajinagar", "station": "s02",
    "wants": ["Keep wedding and festival buyers coming to Shivajinagar instead of Chickpet", "Restock in time for the season without holding money in slow weeks"],
    "evidence": ["D-p11", "D-p12"] },
  "attendant": { "name": "The attendant", "role": "Hub front counter", "station": "s03", "proposed": true,
    "wants": [], "check": "needs the stakeholder table: not in the repo" },
  "driver": { "name": "The collector's driver", "role": "Authorised collector", "station": "s05", "proposed": true,
    "wants": [], "check": "needs the stakeholder table: not in the repo" },
  "farm_worker": { "name": "A farm worker", "role": "Poultry farm", "station": "s07", "proposed": true,
    "wants": [], "check": "needs the stakeholder table: not in the repo" }
}
```

**Don't write the `wants` for the attendant, driver or farm worker.** The spec says these come from "our stakeholder table", which isn't in the repo. Their cards show the name and role and the line `What they want: to come from the stakeholder table`, in muted text with a Proposed chip.

## Files to touch

- `src/data/stakeholders.json` and its schema.
- `src/game/ui/StakeholderCard.ts` (new): a deck-style card (art bible §8) with the name in Baloo 2 at 30 px, the role, and the wants as bullets in Hind at 24 px. It opens next to the character's head anchor without covering the kilo, and closes on a click elsewhere or Esc.
- In each station scene that has the character (s02, s03, s05, s07): a hotspot over the character's sprite and a small "?" marker above its `<name>_head` anchor while the card is closed. Add the figure and anchor to that station's build script if it's missing (s05 and s07 need the driver and farm worker figures: grey costumes, at true size).

## Acceptance criteria

- [ ] All five characters can be tapped, and their cards match the JSON exactly.
- [ ] The three cards without evidence say so and carry Proposed. No invented wants anywhere.
- [ ] A card never covers the kilo, its tag or the prompt.
- [ ] Opening a card pauses that station's auto-advance (s06/s07-style auto steps).

## Screenshots

`review/stakeholders/{1920x1080,1280x720}-anthony.png`, `-arif.png`, `-attendant.png`, `-driver.png`, `-farm-worker.png`.

## Questions

## Notes

## Blocked
