// Screenshot a station's states at review sizes. Starts its own Vite dev server.
// Usage: node tools/shoot.mjs s01 [--run 2] [--reduced]   -> review/<station>/<w>x<h>[-run2]-NN-<state>.png
//        node tools/shoot.mjs full                         -> review/full/NN-run<r>-<beat>.png + timing.md
//        node tools/shoot.mjs s01-night                    -> review/s01/<w>x<h>-night-NN-<state>.png
import { chromium } from "@playwright/test";
import { createServer } from "vite";
import { mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const script = args[0] ?? "s01";
const night = script.endsWith("-night");
const station = night ? script.slice(0, -"-night".length) : script;   // the scene / asset id
const run = args.includes("--run") ? args[args.indexOf("--run") + 1] : "1";
const reduced = args.includes("--reduced");
const SIZES = [[1920, 1080], [1280, 720]];

if (script === "full") process.exit(await full());

/** Task 08: play Run 1 · s01 to Run 2's end card with one generic driver (Space acts, a held → walks
 * and leaves), one 1280x720 shot per beat into review/full/, per-beat and per-run times into
 * review/full/timing.md. Fails on any console error or a beat that does not advance in 90 s. */
async function full() {
  const { writeFileSync } = await import("node:fs");
  const out = join(ROOT, "review", "full");
  mkdirSync(out, { recursive: true });
  const server = await createServer({ root: ROOT, configFile: join(ROOT, "vite/config.dev.mjs"), server: { port: 8099 }, logLevel: "error" });
  await server.listen();
  const browser = await chromium.launch({ args: ["--use-angle=d3d11", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("http://localhost:8099/?run=1&beat=0");
  const state = () => page.evaluate(() => { const s = window.__game.registry.get("state"); return { run: s.run, beat: s.beat, tag: s.kilo.tag?.value ?? null }; });
  await page.waitForFunction(() => window.__ready, null, { timeout: 30000 });
  await page.mouse.click(4, 716);
  const rows = [], t0 = Date.now();
  for (let n = 1; n < 30; n++) {
    const ready = await page.evaluate(() => window.__ready);
    const at = await state();
    const name = `${String(n).padStart(2, "0")}-run${at.run}-${ready}`;
    await page.waitForTimeout(400);
    await page.screenshot({ path: join(out, `${name}.png`) });
    if (ready === "end") { rows.push({ name, run: at.run, secs: 0, tag: at.tag }); break; }
    const start = Date.now();
    await page.evaluate(() => (window.__ready = null));
    while (true) {
      const now = await state();
      if (now.run !== at.run || now.beat !== at.beat) break;
      if (Date.now() - start > 90000) { errors.push(`stuck at ${name}`); break; }
      await page.keyboard.press("Space");
      await page.waitForTimeout(350);
      await page.keyboard.down("ArrowRight");
      await page.waitForTimeout(900);
      await page.keyboard.up("ArrowRight");
    }
    rows.push({ name, run: at.run, secs: (Date.now() - start) / 1000, tag: at.tag });
    if (errors.length) break;
    await page.waitForFunction(() => window.__ready, null, { timeout: 30000 });
  }
  const total = (Date.now() - t0) / 1000;
  const run1 = rows.filter((r) => r.run === 1).reduce((a, r) => a + r.secs, 0);
  const table = rows.map((r) => `| ${r.name} | ${r.tag ?? "—"} | ${r.secs.toFixed(1)} |`).join("\n");
  const md = `# Full playthrough timing

Made by \`node tools/shoot.mjs full\` (generic driver: Space, then → held 0.9 s, until the beat changes; so these are upper bounds on the minimum inputs).

| Beat | Tag at start | Seconds |
|---|---|---|
${table}

Run 1: ${run1.toFixed(1)} s · whole game: ${total.toFixed(1)} s
`;
  writeFileSync(join(out, "timing.md"), md);
  console.log(md);
  await browser.close();
  await server.close();
  if (errors.length) { console.error(errors.join("\n")); return 1; }
  return 0;
}

// Each station lists its states as [name, action]; actions are key presses or waits.
const SCRIPTS = {
  s01: [
    ["start", []],
    ["chop-1", ["Space"]],
    ["kilo-ready", ["Space", "Space"]],
    ["picked-up", ["Space"]],
    ["blueprint", ["b"]],
    ["evidence", ["b", "i"]],
    ["card", ["i", "ArrowRight", 900]],
    ["s02", [1800]],
  ],
  "s01-night": [
    ["dark", []],
    ["lost", [1000]],
    ["run2-card", ["ArrowRight"]],
  ],
};

const server = await createServer({ root: ROOT, configFile: join(ROOT, "vite/config.dev.mjs"), server: { port: 8099 }, logLevel: "error" });
await server.listen();
const browser = await chromium.launch({ args: ["--use-angle=d3d11", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"] });
const out = join(ROOT, "review", station);
mkdirSync(out, { recursive: true });

for (const [w, h] of SIZES) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, reducedMotion: reduced ? "reduce" : "no-preference" });
  const q = night ? new URLSearchParams({ run: "1", beat: "2" }) : new URLSearchParams({ station, run });
  await page.goto(`http://localhost:8099/?${q}`);
  await page.waitForFunction((s) => window.__ready === s, station, { timeout: 30000 });
  await page.mouse.click(4, h - 4);           // focus the page without hitting a hotspot
  await page.waitForTimeout(300);
  let n = 0;
  for (const [name, steps] of SCRIPTS[script]) {
    for (const step of steps) {
      if (typeof step === "number") await page.waitForTimeout(step);
      else { await page.keyboard.press(step); await page.waitForTimeout(520); }
    }
    await page.waitForTimeout(500);
    const suffix = night ? "-night" : run === "2" ? "-run2" : "";
    const file = join(out, `${w}x${h}${suffix}${reduced ? "-reduced" : ""}-${String(++n).padStart(2, "0")}-${name}.png`);
    await page.screenshot({ path: file });
    console.log(file.replace(ROOT, "."));
  }
  await page.close();
}
await browser.close();
await server.close();
