# Patterns

How *Waste to Wealth* is put together, for anyone adding to it. Read [game-concept.md](game-concept.md) (the spec) and [art-bible.md](art-bible.md) (the look) first. Station 1 is the worked example for everything here: copy its shape, not just its code.

## 1. The pipeline

```
src/data/stations/sNN.json ─┬─► art/scripts/sNN_build.py ──► art/blender/sNN_<name>.blend
  (text, numbers, evidence)  │      (Blender, headless)            │
                             │                                     ▼
tools/render_signs.mjs ◄─────┘                  art/scripts/render_station.py
  (sign text → PNG textures)                      (layers by collection name)
                                                                   │
                                                                   ▼
                                       art/build/renders/sNN/*.png + anchors.json
                                                                   │
                                                  tools/pack_layers.py sNN
                                                                   ▼
                               public/assets/stations/sNN/  pack.json · layers.json · *.png
                                                                   │
src/game/scenes/stations/StationNN.ts ◄────────────────────────────┘
  (Phaser: places layers, wires the interaction)
```

Commands, from the repo root (Blender is `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"`, written `blender` below):

```bash
node tools/render_signs.mjs                                    # only if the station has signs
blender -b --python art/scripts/s01_build.py                   # builds and saves the .blend (backs up first)
blender -b art/blender/s01_stall.blend --python art/scripts/render_station.py            # ~9 min full, add -- --draft for ~2 min
python tools/pack_layers.py s01
python tools/check_palette.py s01
npm run dev                                                    # http://localhost:8080/?station=s01
node tools/shoot.mjs s01                                       # screenshots into review/s01/
```

Rules that keep the pipeline honest:

- **Every Blender operation lives in a script** under `art/scripts/`. Never edit a `.blend` by hand and never run one-off Python against it without saving that Python as a script. Re-running the script must rebuild the file from nothing.
- **Scripts only write inside `art/`** (`lib/safety.py` refuses anything else) and **back up any `.blend` before overwriting it** (to `art/blender/backups/`, not committed). If a script deletes or overwrites anything other than its own station's `.blend`, mark it `DESTRUCTIVE` in its docstring and ask the lead before running it.
- **The game never depends on Blender.** It only reads `public/assets/`. Commit the packed assets with the scripts that made them.

## 2. Station data (`src/data/`)

| File | Schema | What it holds |
|---|---|---|
| `stations/sNN.json` | `schema/station.schema.json` | One station: title, place, set, signs, per-run prompts, kilo tag, blueprint rows, `params`, evidence |
| `runs.json` | `schema/runs.schema.json` | The two runs and their beats in order (`"s01"`, `"s01:night"`, `"end"`) |
| `evidence-map.json` | `schema/evidence-map.schema.json` | Every source the game may cite |

**All player-facing text and every number lives in this JSON**, never in `.ts` or `.py`. That includes prompts, sign text, tag values, blueprint rows, card text and captions.

**Every item cites evidence ids** that exist in `evidence-map.json`:
- `F##` is one of our photos.
- `D-p##` is a page of our deck.
- `X##` is an open-licence photo (it needs licence and credit fields).
- `M##` is map data.
- `C-*` is a cited report.
- `SPEC-*` is our own proposal (always shown as Proposed).

If you can't find evidence for something, it doesn't go in. Write it up as a question in your task file instead.

The **truth rules** from the spec, which the check script enforces:
- Fees are ₹5/kg animal waste and ₹3/kg bone.
- The payout is always the placeholder `₹[__]/kg` and never a number. The tag shows `+₹[__]`.
- The renderer is always "Renderer (example)".
- Station 7's `label` is "How it could close".
- Every hub detail has `"proposed": true` (blueprint rows, run summaries, card lines).

## 3. How a station scene is structured

Every station is one file, `src/game/scenes/stations/StationNN.ts`, which default-exports a subclass of `StationScene` (`src/game/scenes/StationScene.ts`). It is registered automatically (`main.ts` globs the folder), and `runs.json` decides when it plays. Until the file exists, its beats play the grey-box `Placeholder`.

`StationScene` already does everything that is the same for every station:

- it draws the diorama void with the lattice;
- it creates the `world` container, the **prompt pill** (top left), the **blueprint panel** (B), the **evidence card** (the "i" button, or I) and Esc to close both;
- it reads `layers.json` so that `this.layer(name)` places a rendered layer exactly where Blender rendered it and `this.anchor(name)` returns a screen point;
- `this.hint(x, y, r)` draws a pulsing ring around a hotspot;
- `this.leave()` slides the set away, fades, shows the next station card and starts the next beat;
- it sets `window.__ready` once the fade-in is done, so screenshots never catch a half-faded frame.

A station subclass only writes its interaction, as a small **phase machine**:

```ts
export default class Station01 extends StationScene {
    private phase: 'cut' | 'pickup' | 'leave' = 'cut';
    constructor() { super('s01'); }
    preload() { this.loadLayers(); }
    protected build() {
        this.layer('bg');                                  // layers in back-to-front order
        ...
        this.prompt.show(this.prompts().cut, 'Space');     // prompt text from JSON, by phase
        this.ring = this.hint(block.x, block.y, 92);
    }
    private act() { if (this.phase === 'cut') this.chop(); else if (this.phase === 'pickup') this.pickUp(); }
}
```

Conventions inside a scene:

- **One action per phase, with two inputs.** Click or tap the hotspot, *and* press Space or Enter. → walks on. Never require a key the prompt doesn't show.
- **Never drop input.** If an action is animating, buffer one press and replay it (see `queued` in `Station01.chop`).
- **Layers come from Blender, so don't hand-place art.** Position UI from `this.anchor(...)`. If you need a new anchor, add it in the build script (`st.anchor(name, world_point)`) and re-render.
- **Sounds are events:** `this.events.emit('sfx', 'cleaver')`. The sound task maps names to files and captions. Don't play audio directly.
- **Reduced motion:** check `this.state.reducedMotion` before every tween that moves, shakes or flickers, and give a still alternative.
- **Variants:** `this.variant` is set when the beat is `"sNN:variant"` (e.g. `s01:night`). The variant uses different render layers (`-- --preset night`) and different prompts (`runs["1"].prompts`), but stays in the same scene file.

## 4. How state, the kilo tag, the blueprint and the "i" are wired

**State** (`src/game/state.ts`) is one object in Phaser's registry: `run`, `beat`, `station`, `kilo { carried, tag }`, `blueprintOpen` and `reducedMotion`. Read it with `getState(this)` and change it only with `setState(this, patch)`. Anything that must survive a scene change goes there, and nothing else. `flow.ts` moves `run` and `beat` forward. URL params set the start point for reviews and screenshots: `?run=2&beat=3`, `?station=s04`, `?reducedMotion`.

**The kilo tag** (`src/game/ui/KiloTag.ts`) is the one thing the player tracks.
- *While the kilo is on screen*, the tag hangs from the kilo's knot anchor with a `hang` offset, so it sits **beside** the kilo, never over it: `new KiloTag(scene, knot.x, knot.y, tag, reducedMotion, { dx: -130, dy: 26 })`.
- *When the kilo isn't on screen*, it docks in the HUD band, left of the "i" (`FRAME.width - 260, 20`).
- Its value and meaning always come from JSON (`kilo.tag`, e.g. `{ "value": "−₹5", "meaning": "cost", "note": "₹5/kg animal waste" }`) and are stored in `state.kilo.tag`.
- The one flip, at the weigh-in, is `tag.flipTo({ value: "+₹[__]", meaning: "income", ... })` (300 ms).
- Meaning colours are `cost`, `income`, `pay` and `offsite`, from `theme.ts`. Never use a raw hex.

**The blueprint panel** (`ui/BlueprintPanel.ts`) is built from `blueprint["1"|"2"]` in the station JSON for the current run. It has five lanes in a fixed order: vendor, frontstage, backstage, support and evidence. A row with `"proposed": true` gets the brown "Proposed" chip. Missing lanes show "—". B toggles it, and the open/closed state carries across stations (`state.blueprintOpen`). It covers y 660 to 1080, so **nothing the player needs may sit below y 660** (art bible §6.3).

**The evidence card** (`ui/EvidencePanel.ts`) lists the station's top-level `evidence` ids with their titles, kinds, deck pages and licences, from `evidence-map.json`. Our proposals show as "Proposed". The "i" button sits top right; I toggles it.

## 5. Naming

| Thing | Pattern | Example |
|---|---|---|
| Station id, Phaser scene key | `sNN` | `s03` |
| Station data | `src/data/stations/sNN.json` | `s03.json` |
| Station scene | `src/game/scenes/stations/StationNN.ts`, default export | `Station03.ts` |
| Build script / .blend | `art/scripts/sNN_build.py` / `art/blender/sNN_<word>.blend` | `s03_build.py` / `s03_weighin.blend` |
| Blender collections | `SET`, `PROPS`, `PROP_<name>`, `FX_<name>`, `CHAR_<name>_<pose>` | `PROP_crate`, `FX_ping`, `CHAR_attendant_idle` |
| Blender objects | `AREA_part` in capitals by area | `FACADE_pier_L`, `SCALE_platform`, `KILO_bag` |
| Materials | `MAT_<what>` from `kit.materials()`; station-only ones in its build script | `MAT_tiles_checker` |
| Shadow catcher | object with `["shadow_catcher"] = True` inside its `PROP_` collection | `KILO_shadow_catcher` |
| Rendered layers | `bg`, `fx_<name>`, `<prop>`, `<prop>_shadow`, `<char>_<pose>` (+`_night` for presets) | `crate_shadow` |
| Phaser texture key | `<sid>_<layer>` | `s01_kilo` |
| Anchors | snake_case; `<prop>_centre` is required for every prop with a shadow | `kilo_knot`, `scale_pan` |
| Phases / prompt keys | short verbs | `cut`, `pickup`, `leave` |
| Sound events | `sfx` + noun | `cleaver`, `scale`, `door_seal`, `upi_ping` |
| Screenshots | `review/<sid>/<w>x<h>[-run2][-reduced]-NN-<state>.png` | `1280x720-run2-03-weighed.png` |
| Task files | `tasks/NN-name.md`; rename to `NN-name-blocked.md` if blocked | `tasks/04-s03-weigh-in-greybox.md` |

## 6. How to add a station with one JSON file and one scene file

Using Station 3 as the example.

1. **Data.** Create `src/data/stations/s03.json` (set `"$schema": "../schema/station.schema.json"`; your editor will then check it). Copy the shape of `s01.json`:
   - id, number and title from the spec's journey table;
   - `set`;
   - `runs` with prompts for each phase;
   - `blueprint` rows for each run, with `"proposed": true` on hub details;
   - the kilo tag if it changes;
   - `params`;
   - `evidence`.

   The station shows up in the game at once, as a grey-box placeholder in the run order `runs.json` already gives it.
2. **Set.** Write `art/scripts/s03_build.py` by copying the shape of `s01_build.py`: `st = station.begin("s03")`, then `kit.*` pieces, station-only geometry, `PROP_` / `FX_` / `CHAR_` collections, then `st.anchor(...)` for each hotspot and `st.finish(TARGET)`. For a grey box, use `m["grey"]` and `m["grey_dark"]` boxes at true size; the art task replaces them later without changing names or anchors. Then render and pack (section 1).
3. **Scene.** Create `src/game/scenes/stations/Station03.ts`: `export default class Station03 extends StationScene`, `super('s03')`, `preload() { this.loadLayers(); }`, and a `build()` with your phases.

That's all. No registry to edit, no other file to touch. If you think you need to change `StationScene`, `flow.ts`, the UI components or `kit.py`, stop and mark the task `-blocked`, saying why. Those are shared and the lead changes them.

## 7. Checking your work

Before marking a task done:

- `npx tsc --noEmit` and `npm run build` pass.
- `python tools/check_palette.py <sid>` passes.
- Every new evidence id resolves (the check script will enforce this once it exists, task 22).
- **The screenshots the task lists** are in `review/<sid>/`, at 1920×1080 and 1280×720, for every run the station appears in. Add your station's states to `SCRIPTS` in `tools/shoot.mjs`.
- Look at them against the art bible, especially "kilo first" (§6.3), nothing needed below y 660, the meaning colours used only with a word or number, and type sizes (§8).
- Commit with `sNN: <what changed>` and list the screenshots in the message.
