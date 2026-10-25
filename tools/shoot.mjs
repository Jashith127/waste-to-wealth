// Screenshot a station's states at review sizes. Starts its own Vite dev server.
// Usage: node tools/shoot.mjs s01 [--run 2] [--reduced]   -> review/<station>/<w>x<h>[-run2]-NN-<state>.png
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
