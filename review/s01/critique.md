# Station 1 vertical slice: critique log

Screenshots: `1920x1080-NN-<state>.png` and `1280x720-NN-<state>.png` in this folder, made by `node tools/shoot.mjs s01` (Run 1) and `node tools/shoot.mjs s01 --run 2`. States: start, first chop, kilo ready, picked up, blueprint open, evidence open, station card, Station 2.

Judged against `docs/art-bible.md`. Each pass lists what failed and what changed.

## Pass 1: first render (art only)

| Rule | Finding | Fix |
|---|---|---|
| §1 camera | The art bible's 6 × 6 m square plinth crops the back walls at 1–2 m and puts any shopfront at the right edge of the frame | Street-slice diorama: 10 m of frontage, doorway at frame centre (art bible 0.3) |
| §5 light | Sun travelling away from the camera left every shopfront in its own shadow | Sun travels toward +Y, in front of the walls |
| §6 kilo first | Shop interior black: the building mass filled the room | Mass split around the shop |
| §10 sources | Sign's Kannada line hidden by the sunshade; awning plain pink; counter front a chessboard; paving like bathroom tiles; hung meat hidden | Sunshade raised and shortened; hard stripes; photo-menu board; grimier slabs; meat moved under the awning |

## Pass 2–3: layout

| Rule | Finding | Fix |
|---|---|---|
| §6 overhang | From 30° above, the 0.85 m awning hid everything inside the shop above 1.3 m, Riyaz included | Awning 0.57 m deep, raised to 2.74–3.02 m; counter and Riyaz moved forward to the doorway, as in F04. Wrote the overhang rule into the art bible |
| §6 kilo first | Riyaz would cover the cooler (the flicker) | Riyaz at x 0.55, cooler shallower |
| §4 materials | 2D textures (bricks, checker) striped on vertical faces | `Nodes.planar()` picks the face's own plane |
| §7 signs | A power cable crossed the Kannada line | Cables moved up to the first-floor wall |

## Pass 4–6: props and people

| Rule | Finding | Fix |
|---|---|---|
| §2 proportions | Riyaz a stick puppet | Chunkier torso, 1.3× hands and forearms, shoulders, brows, moustache, muted small checks |
| §10 sources | Hung meat read as carrots, then pears | Carcass slabs with a fat edge, after X05/R26 |
| §6.3 density | Left half of the frame empty | F04's parked scooter, bevelled boxes so it reads as one body |
| §7 signs | Blank neighbour boards and posters read as windows | Neighbour boards rendered "illegible" (blurred letter blocks, maroon after F02); posters removed |
| §2 kilo | The bag read as a garlic bulb; its tied handles flew off (rotation about the world origin) | Slumped body, gathered neck, handles rotated in place (`geo.sphere(rot=)`) |
| §5 tone | Frame washed out under AgX base contrast | `AgX - Medium High Contrast` |

## Pass 7: in the game

| Rule | Finding | Fix |
|---|---|---|
| §6.3 HUD | Centred prompt covered the shop sign; evidence card covered the shop | Prompt top-left, "i" top-right, card opens under it, right-aligned |
| §6.3 kilo first | The −₹5 tag hung straight down over the bag | Tag hangs beside the bag on a sagging string (`KiloTag` `hang`) |
| §8 type | Blueprint body 24 px, below the 28 px base; evidence id chips too narrow | Body 26 px in 64 px rows (19 px at 720p); chips widened |
| Input | A press during a chop was dropped, so a quick player (or the test) lost a chop | One press is buffered during a chop |
| S2 placeholder | Cream text on light grey | Dark backing card |

## Still open (not blocking the slice)

- **Fridge form** has no photo reference (art bible §0 gaps). It is a generic glass-door cooler.
- **The cream monoblock chair** still reads as a toy. It sits below the blueprint line, so it's low priority; the Blender task for S1 polish can fix it.
- **Sound** hooks fire (`sfx` event: `cleaver`) but no audio files exist yet. The field recordings are not in the repo.
- **Urdu sign line** waits for a speaker's check (art bible §7).
- Renders ship at 1920 × 1080 PNG (about 2 MB for `bg`). The 2× masters and WebP conversion belong to the scaling task.
