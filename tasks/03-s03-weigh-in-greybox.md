# 03 · s03 Weigh-in and payment, grey box (Run 2)

**Phase:** grey box · **Depends on:** 02 · **Read first:** patterns §3, §4 (the tag flip); spec "The journey" row 3 and "The service-design layer"

## Goal

At the hub's front counter, Riyaz drags the crate onto the platform scale. He *says* his phone number and the attendant types it, because wet hands make the phone uncomfortable. A slip is issued and the UPI payment confirms **by sound**. The tag flips from −₹5 to +₹[__]. The rate board says sorted waste earns more, **with no numbers**.

## Content (use exactly)

`src/data/stations/s03.json`:

- `number` 3 · `title`: `Weigh-in and payment` · `place`: `The hub's front counter` · `greybox`: true · `set.lighting`: `midday`
- `evidence`: `["SPEC-journey", "D-p23", "D-p20", "D-p26", "D-p22"]`
- `runs["2"]`:
  - `summary`: `The kilo is weighed, recorded by voice and paid by UPI.`
  - `proposed`: true
  - `prompts`:
    - `drag`: `Put the crate on the scale`
    - `number`: `Say your number`
    - `wait`: `The attendant types it in`
    - `paid`: `Paid`
    - `leave`: `Into the cold room`
- `params`:
  ```json
  {
    "weight_label": "1.0 kg",
    "rate_board": [
      { "line": "Bone, sorted", "rate": "₹[__]/kg" },
      { "line": "Offal, sorted", "rate": "₹[__]/kg" },
      { "line": "Mixed", "rate": "₹[__]/kg" }
    ],
    "rate_note": "Sorted earns more",
    "speech": "My number is…",
    "number_masked": "••••• •••••",
    "slip": { "title": "Hub slip", "lines": ["1.0 kg · sorted", "₹[__] by UPI"] },
    "tag_after": { "value": "+₹[__]", "meaning": "income", "note": "₹[__]/kg, payout to be set" }
  }
  ```
- `blueprint["2"]` (all `proposed: true` except the evidence lane):
  - vendor: `Puts the crate on the scale and says his number.` [SPEC-journey, D-p23]
  - frontstage: `Attendant, scale and rate board; the slip comes on WhatsApp.` [SPEC-journey, D-p20]
  - backstage: `The rate is set with the collector agreement.` [SPEC-journey]
  - support: `UPI payment, confirmed by sound.` [SPEC-journey, D-p26]
  - evidence: `Empathy map: wet hands make the phone uncomfortable; interview 04: typing slows them down.` [D-p23, D-p26]
- No `runs["1"]`: Run 1 never reaches the hub.

## Files to touch

- `src/data/stations/s03.json`, `src/data/evidence-map.json` (no new ids needed).
- `art/scripts/s03_build.py` (new), grey box at true sizes:
  - a counter 1.2 m high and 2 m wide, inside a grey hub front (the masonry pier from task 02 for continuity);
  - a platform scale about 0.6 × 0.6 m, 0.12 m high (`SCALE_platform`, anchor `scale_pan`);
  - a rate-board panel on the back wall (`RATEBOARD_panel`, anchor `rate_board`): **leave it blank** and draw its text in Phaser from `params.rate_board`;
  - `PROP_crate`, a crate 0.55 × 0.36 × 0.30 m in `m["grey"]`, with anchors `crate_centre` and `crate_knot` (the top centre);
  - `CHAR_attendant_idle` and `CHAR_attendant_type` behind the counter (grey costume) and `CHAR_riyaz_idle` in front, without the cleaver;
  - `TARGET` at the scale.
- `src/game/scenes/stations/Station03.ts` (new):
  1. **drag:** drag the crate onto the scale. A drop within 90 px of `scale_pan` snaps; anything else springs back. Space also works.
  2. Show `weight_label` on a small display card at the scale, then **number:** Space or a click shows a speech bubble with `speech`. Riyaz never touches a phone.
  3. **wait:** the attendant switches to the type pose for 1 s and `number_masked` appears on a small screen card.
  4. **paid:** emit `sfx: upi_ping`, pulse the HUD phone corner if task 09 is done (otherwise skip), show the slip card, and run `tag.flipTo(params.tag_after)`. Store the new tag in state.
  5. **leave.**
  - Draw the rate board from `params.rate_board` and `rate_note` with a brown "Proposed" chip.

## Acceptance criteria

- [ ] No digit other than "1.0 kg" appears on screen. Rates and the payout are only ever `₹[__]`.
- [ ] Riyaz never holds or touches a phone. The number is spoken (bubble) and typed by the attendant.
- [ ] The payment confirms without the player having to look at a phone: the `upi_ping` event fires and the tag flips.
- [ ] The rate board, slip and every blueprint row except "evidence" show Proposed.
- [ ] Drag works with a mouse and with touch (Playwright `page.touchscreen`), and Space alone completes the station.
- [ ] `check_palette.py s03` passes.

## Screenshots

`review/s03/{1920x1080,1280x720}-run2-01-start.png`, `-02-on-scale.png`, `-03-number.png`, `-04-paid-flip.png`, `-05-blueprint.png`.

## Questions

## Notes

## Blocked
