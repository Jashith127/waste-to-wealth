// Renders every in-world sign in src/data/stations/*.json to a PNG texture for Blender.
// Text comes only from JSON (art-bible §7); the browser handles Kannada shaping.
// Usage: node tools/render_signs.mjs      -> art/build/signs/<station>-<sign>.png
import { chromium } from "@playwright/test";
import { readFileSync, readdirSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(ROOT, "art", "build", "signs");
const PX_PER_M = 600;

const STYLES = {
  // Layout and colour after F04: cream board, dusty-red script line, green name, dark band.
  "board-cream-green": (sign) => {
    const line = (role) => sign.lines.find((l) => l.role === role);
    const top = line("top"), name = line("name"), band = line("band");
    return `
      <div class="board">
        ${top ? `<div class="top" lang="${top.lang}">${top.text}</div>` : ""}
        ${name ? `<div class="name" lang="${name.lang}">${name.text}</div>` : ""}
        ${band ? `<div class="band" lang="${band.lang}">${band.text}</div>` : ""}
      </div>`;
  },
  // Unreadable faded signage: letter-like blocks, blurred. Adds density without inventing content.
  illegible: (sign) => {
    const [ground, ink, band] = sign.palette;
    const blocks = (n, h) => Array.from({ length: n }, (_, i) =>
      `<span style="display:inline-block;width:${4 + ((i * 7) % 5)}vw;height:${h}vh;margin:0 0.8vw;background:${ink};border-radius:1vh"></span>`).join("");
    return `
      <div class="board" style="background:${ground};filter:blur(0.6vh) saturate(0.75)">
        <div style="text-align:center;padding-top:10vh">${blocks(9, 16)}</div>
        <div style="text-align:center;padding-top:9vh">${blocks(6, 30)}</div>
        <div class="band" style="background:${band};margin-top:auto;height:16vh"></div>
      </div>`;
  },
};

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;800&family=Baloo+Tamma+2:wght@600;700&display=block');
  html, body { margin: 0; background: transparent; }
  .board { box-sizing: border-box; width: 100vw; height: 100vh; background: #E9E2D0;
           border: 0.9vh solid #3A3330; display: flex; flex-direction: column; overflow: hidden; }
  .top  { font: 700 17vh/1 'Baloo Tamma 2'; color: #A8585E; text-align: center; padding-top: 4vh; }
  .name { font: 800 34vh/1 'Baloo 2'; color: #2F7564; text-align: center; letter-spacing: 0.02em; flex: 1;
          display: flex; align-items: center; justify-content: center; }
  .band { font: 600 13vh/1 'Baloo 2'; color: #E9E2D0; background: #3A3330; text-align: center;
          padding: 3vh 0 2vh; letter-spacing: 0.08em; text-transform: uppercase; }
`;

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
const stationsDir = join(ROOT, "src", "data", "stations");
for (const file of readdirSync(stationsDir).filter((f) => f.endsWith(".json"))) {
  const station = JSON.parse(readFileSync(join(stationsDir, file), "utf8"));
  for (const sign of station.signs ?? []) {
    const [w, h] = sign.size_m.map((m) => Math.round(m * PX_PER_M));
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.setContent(`<!doctype html><meta charset="utf-8"><style>${CSS}</style>${STYLES[sign.style](sign)}`);
    await page.evaluate(() => document.fonts.ready);
    const out = join(OUT, `${station.id}-${sign.id}.png`);
    await page.screenshot({ path: out, omitBackground: true });
    console.log("sign", out.replace(ROOT, "."), `${w}x${h}`);
    await page.close();
  }
}
await browser.close();
