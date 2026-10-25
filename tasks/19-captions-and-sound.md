# 19 · Captions and sound hooks

**Phase:** polish · **Depends on:** 08, 09 · **Read first:** spec "Sound" and "Payment by sound"; patterns §3 ("Sounds are events")

## Goal

Every `sfx` event plays its sound if the file exists, and **always** shows a caption. Ambient sound comes only from the ambient sections of our own recordings, with no identifiable voices. **The recordings aren't in the repo yet**, so the system must work silently until they arrive, with captions still on.

## Content (use exactly)

New `src/data/audio.json` (with a schema):

```json
{
  "sfx": {
    "cleaver":   { "caption": "[cleaver on the block]",        "file": "assets/audio/cleaver.ogg",   "evidence": ["D-p34"] },
    "scale":     { "caption": "[the scale clunks]",            "file": "assets/audio/scale.ogg",     "evidence": ["SPEC-journey"] },
    "door_seal": { "caption": "[the cold-room door seals]",     "file": "assets/audio/door_seal.ogg", "evidence": ["SPEC-journey"] },
    "upi_ping":  { "caption": "[payment ping: paid]",          "file": "assets/audio/upi_ping.ogg",  "evidence": ["SPEC-journey", "D-p26"] }
  },
  "ambient": {
    "market":    { "caption": "[market: auto horns, talk in Dakhni, Tamil and Kannada]", "file": "assets/audio/ambient_market.ogg", "evidence": ["D-p34"],
                   "source": "Ambient sections only of our field recordings; no identifiable voices (spec)." }
  },
  "captions_default": true
}
```

## Files to touch

- `src/data/audio.json` and its schema.
- `src/game/audio.ts` (new): loads whatever files exist, using a `HEAD` check or `this.load` with a file-error handler that marks the sound as missing without throwing. It listens to every station scene's `sfx` events.
- `src/game/ui/Captions.ts` (new): a caption line at bottom-centre, above y 640, or above the blueprint panel when it is open. Hind at 26 px, on an ink pill at 80%. Shown for 1.6 s and stacked if two fire together. C toggles captions; on by default.
- `StationScene.ts`: **mount `audio` and `Captions` only.**
- `public/assets/audio/README.md`: which recordings belong here, the rule (ambient sections only, no identifiable voices), and the file names above.

## Acceptance criteria

- [ ] With no audio files present: no errors, and every sfx shows its caption.
- [ ] With a test `.ogg` dropped in (any short tone; delete it before committing): it plays, and the caption still shows.
- [ ] The UPI ping caption appears at the same moment as the phone corner lights up (task 09).
- [ ] C toggles captions, and the choice persists across beats (put it in `state`, adding one field to `GameState`; that one state change is allowed).
- [ ] No caption ever covers the kilo or its tag.

## Screenshots

`review/captions/{1920x1080,1280x720}-01-cleaver.png`, `-02-upi-ping.png`, `-03-with-blueprint.png`.

## Questions

## Notes

## Blocked
