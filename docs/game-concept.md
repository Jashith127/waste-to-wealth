# Waste to Wealth — Game Concept Note

Oct 25, 2026 · @Jash

## Summary

*Waste to Wealth* is a five-minute browser game. The reviewer follows one kilo of bone and offal from a Cockburn Road meat stall to a poultry farm and back. Along the way it passes through the Meat Waste Hub, the cold room our concept proposes near Russell Market. The game makes one point: **the same kilo moves from a cost to an income.**

The game is the playable form of the hub concept, not a replacement for it. It turns the concept note's seven-step journey and before/after storyboard into something a reviewer does with their own hands: weighing, sorting, storing and getting paid. A toggle turns any scene into the matching row of the service blueprint, so the game doubles as our blueprint.

## What changed

We moved from a flat SVG page to a 2.5D game: Phaser runs the game, and the art is pre-rendered from Blender. The aim is scenes that feel three-dimensional and specific to Russell Market, without the cost of a real-time 3D engine.

|  | Earlier plan | Now |
| --- | --- | --- |
| Rendering | Flat vector, drawn in code | Scenes modelled in Blender, rendered from one fixed isometric camera, exported as layered PNGs |
| Engine | One hand-written HTML file | Phaser + TypeScript, built with Vite |
| Look | Deck palette, flat cards with ink outlines | Weathered Russell Market materials, with the deck's colours kept for meaning |
| Research | Large research phase | Reuses the evidence already gathered; no new research phase |

We ruled out two alternatives. Godot only pays off if walking around the market in real time is central, and it isn't. Three.js gives full real-time 3D but takes considerably more build work for the same seven scenes.

## The journey

The game plays the same day twice. **Run 1, Today**, lasts about 60 seconds: the morning cut, the ₹5/kg fee, waste dumped behind Russell Market, and leftover meat spoiling during the night's power cut. **Run 2, With the hub**, is the full seven stations. The contrast between the two runs is our before/after storyboard, made playable.

The player is Riyaz Q., our meat-corner persona, for stations 1–4. From station 5 the camera follows the crate, whose value tag flips from **−₹5** to **+₹\[\_\_\]**. That tag is the one thing the player tracks.

| # | Station | Player does | It shows |
| --- | --- | --- | --- |
| 1 | The stall, Cockburn Road | Finishes the morning cut; picks up the kilo | The kilo starts as a ₹5 problem; a flickering fridge |
| 2 | The walk | Moves the kilo through the market street to the hub | Fixed drop window; walking time; a cleaner pavement in Run 2 |
| 3 | Weigh-in and payment | Drags the crate onto the scale and says his phone number | Rate board, colour-coded crate, slip, UPI ping; sorted waste earns more |
| 4 | Cold room | Sorts waste into sealed crates in Chamber B; puts unsold meat in Chamber A | Two doors, never shared; solar carries through the power cut |
| 5 | Bulk pickup | Taps to load the truck | One pickup replaces many; an authorised collector |
| 6 | Renderer, off-site | Watches the material move through the plant | Size reduction, cooking, pressing out oil, drying, milling → meal and oil |
| 7 | Farm → back to the stall | Watches the loop close | Labelled “How it could close” (see Truth rules) |

The HUD shows only three things: a time-of-day clock, the kilo's tag, and a phone corner for the UPI ping. The end card shows the kilo's ledger for both runs, then four before → after beliefs:

- Waste is my problem to dump cheaply → My waste is worth money if I keep it clean
- Anything official will cost me money → The hub is the market's own
- A fridge isn't worth it with these power cuts → I can keep stock cold without buying one
- Leftover meat is a loss I just take → Leftovers wait overnight in Chamber A, free

## The service-design layer

Played straight, the game is a story; toggled, it is a service blueprint. That layer is what makes this a design piece rather than just a game.

- **Blueprint toggle (B).** A swimlane panel slides up under any station, synced to it. It has five lanes: vendor action, frontstage (attendant, scale, rate board), backstage (the association's scheduling, the collector agreement), support (authorisation, solar unit, UPI) and evidence (the source behind the station). Items that are our proposal carry a “Proposed” label.
- **Stakeholder cameos.** Tapping a character opens a small card saying what they want, taken from our stakeholder table. The characters are Anthony at the Basilica flower stall, Arif at the saree shop, the attendant, the collector's driver and a farm worker.
- **Wet hands.** Riyaz never touches his phone at the scale. He says his number and the attendant types it in. This comes from “wet hands make handling the phone uncomfortable.”
- **Payment by sound.** The UPI confirmation is a sound, because nobody looks at a phone mid-rush.

## Truth rules

Every station, line of dialogue, number and prop traces to our field material or a cited source, and a small “i” on each station shows which. Our research checkpoint changed several things in the original concept, and the game follows the corrected version.

| Item | In the game | Why |
| --- | --- | --- |
| Waste fees | ₹5/kg animal waste, ₹3/kg bone | Both September 2026 reports agree; our deck's ₹5 for bone had no source |
| Vendor payout | Shown as ₹\[\_\_\]/kg | No source shows a renderer paying vendors; in the Kerala precedent, shops pay |
| 32–35 kg a day | Not shown as a fact | It is a traders' association estimate, not a measured figure |
| Renderer | “Renderer (example)”, fictional | Bana Eco Works and the other leads are not partners; naming one implies a deal |
| Rendering steps | Generic process, labelled as typical | Evidence covers rendering in general, not a specific plant |
| Farm loop (station 7) | “How it could close” | No supply chain back to the stall was found |
| Hub details | Labelled “Proposed” | Two chambers, drop times, UPI and the attendant are our design, not existing facts |

Art is traced from our own field photos, never from generic “Indian market” imagery. Audio uses only ambient sections of our recordings, with no identifiable voices.

## Art direction

Each station is a hand-crafted miniature set seen from one fixed isometric camera: chunky, slightly exaggerated geometry, textured worn surfaces, warm directional light. Shivajinagar keeps its imperfections. It should look neither like a clean smart city nor like a cartoon of India.

- **Camera:** one orthographic isometric angle and scale for every station, so the sets read as one world.
- **Asset kit:** Russell Market's arches and pink-terracotta masonry, painted stall fronts, metal counters, chopping blocks, plastic crates, tarpaulins, platform scales, handwritten and trilingual signs (Kannada / English / Urdu). The kit is built once and reused.
- **Environment palette:** faded terracotta, dusty cream, worn blue, deep charcoal. This is a proposed direction, not colour measured at the market.
- **Meaning colours (from our deck):** red `#C42B20` for waste as a cost, green `#2E6B34` for money in and Chamber A, saffron `#F0A31F` for the payment accent, blue `#1F5BA8` for off-site. They are used sparingly, on top of the environment.
- **Type:** Baloo 2 and Hind, matching the deck.
- **Sound:** ambient market sound from our recordings, the cleaver on the block, the scale's clunk, the cold-room door seal, and one short payment ping.
- **Avoid:** heavy particles, neon gradients, sci-fi panels, floating HUD clutter.

The rate board, WhatsApp slip and crate graphics are exported as separate files, so the same artwork can be printed for the physical props.

## Stack and pipeline

The game runs on Phaser and TypeScript, built with Vite. The art is made in Blender and exported as layered PNGs. Keeping the art pipeline separate from the game code means a change to a button never makes the art regress.

&#91;embedded content: asset and game pipeline · field photos to browser\]

The coding agent drives Blender through its MCP connection, but only for making assets; the game never depends on Blender at runtime. Renders are judged inside the game, not in Blender's viewport.

- **Phaser + TypeScript:** stations, drag-and-drop, the scale, transitions, sound and game state. Pin one stable version and follow its matching docs.
- **Vite:** the dev server and the browser build. No React unless something outside the game needs it.
- **Blender:** stall, scale, crates, cold room, renderer and farm as miniature sets, all with the same camera, lights and scale.
- **Git:** commit after each working milestone, because the agent can change many files in one pass.
- **MCP safety:** Blender's MCP server can run AI-generated code without safeguards. Keep it to the project's .blend files, keep backups, and read scripts before they run anything destructive.

## Build plan

The style gets locked on one finished scene before the rest is built. Then the whole game runs end to end on placeholders, and only after that is the final art made in batches. Asking the agent to build everything at once is the main thing to avoid.

1. **Art bible.** Camera angle, proportions, palette, materials, lighting, composition and type, all referenced to our field photos.
2. **Vertical slice.** Station 1 at final quality: the stall, the kilo, one interaction, one transition to station 2, and the blueprint toggle. *Review gate: does it look like Russell Market?*
3. **Lock the style.** Save the camera, lights, materials and scale as reusable Blender templates.
4. **Whole journey on placeholders.** All seven stations, both runs, game state, the tag flip and the end card, using grey-box art. *Review gate: is it playable in five minutes?*
5. **Final art in batches.** Replace placeholders station by station, judging each render inside the game.
6. **Polish.** Animation timing, sound, transitions, scaling to laptop and projector, and a full playtest with someone outside the group.

## Open decisions

- [ ] **Coding agent and model.** OpenCode no longer accepts Claude Pro/Max subscriptions; it needs an API key with usage billing. Our options are Claude Code on a subscription, OpenCode with an API key, or Codex. Check which models the plan actually includes before committing.
- [ ] **Review setup.** Will it run on a laptop, a projector, or reviewers' phones? This sets the layout and how far we scope it.
- [ ] **Payout figure.** Keep ₹\[\_\_\]/kg, or show an illustrative range clearly labelled as a scenario?
- [ ] **Belief table.** Approve the re-paired rows in the journey section, and fix the original concept note to match.
- [ ] **Missing photos.** The Russell Market back lane, a platform scale, crates, and the market's arches up close.
- [ ] **Deadline.** Fixes how many stations get final art and how many stay simpler.

## Sources

- Research checkpoint, Phase 1 (`research/evidence.csv`, entries E003–E006, E023–E025, E045, E073–E079)
- [Meat Waste Hub — Concept Note](https://claude.ai/code/artifact/e7c8cc7d-4d01-4444-bb0d-d7b5cdb3801f)
- [South First — waste collection charges](https://thesouthfirst.com/karnataka/janmashtami-ban-protest-against-waste-collection-charges-bengaluru-meat-shops-to-shut-on-3-and-4-september/)
- [The News Minute — chicken shops bandh](https://www.thenewsminute.com/karnataka/bengaluru-chicken-shops-call-bandh-to-protest-animal-waste-collection-fee)
- [Krishi Jagran — Kannur poultry-waste-free district](https://krishijagran.com/animal-husbandry/kannur-to-become-the-first-poultry-waste-free-district-in-kerala/?amp=1)
- [Emanuele Feronato — Phaser 4 with Vite and TypeScript, official Create Game App](https://emanueleferonato.com/2026/04/17/getting-started-with-phaser-4-vite-typescript-setup-using-the-official-create-game-app/)
- [Developers Digest — official Blender MCP server](https://www.developersdigest.tech/mcp-servers/blender-mcp)
