// Renders every in-world sign in src/data/stations/*.json to a PNG texture for Blender.
// Text comes only from JSON (art-bible §7); the browser shapes Kannada and Urdu correctly.
// Usage: node tools/render_signs.mjs      -> art/build/signs/<station>-<sign>.png
//
// Styles follow the field photos: printed flex banners (F04: trilingual top line, outlined
// condensed name, black tagline band, address line) and painted boards (F02).
import { chromium } from "@playwright/test";
import { readFileSync, readdirSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(ROOT, "art", "build", "signs");

const line = (sign, role) => sign.lines.find((l) => l.role === role);
const span = (l, cls) => (l ? `<div class="${cls}" lang="${l.lang}">${l.text}</div>` : "");

// Flex prints fade, crease and collect grime at the bottom edge.
const WEAR = `<div class="wear"></div>`;

const STYLES = {
  "flex-meat": (s) => `
    <div class="sign flex" style="background:#F1EEE6">
      <div class="row top">${span(line(s, "top"), "kn red")}${span(line(s, "top-right"), "ur")}</div>
      ${span(line(s, "name"), "name teal")}
      ${span(line(s, "band"), "band")}
      ${span(line(s, "address"), "address")}
      ${WEAR}
    </div>`,
  "flex-red": (s) => `
    <div class="sign flex" style="background:#8E2F2C">
      ${span(line(s, "top"), "kn cream center")}
      ${span(line(s, "name"), "name yellow")}
      ${WEAR}
    </div>`,
  "board-maroon": (s) => `
    <div class="sign board" style="background:#6E2E2C">
      ${span(line(s, "top"), "kn cream center small")}
      ${span(line(s, "name"), "serif")}
      ${span(line(s, "band"), "band thin")}
      ${WEAR}
    </div>`,
  "flex-yellow": (s) => `
    <div class="sign flex" style="background:#E8C64A">
      <div class="row top">${span(line(s, "top"), "kn green")}${span(line(s, "top-right"), "ur")}</div>
      ${span(line(s, "name"), "name darkgreen")}
      ${span(line(s, "band"), "band")}
      ${WEAR}
    </div>`,
  "flex-green": (s) => `
    <div class="sign flex" style="background:#2F6B3A">
      <div class="row top">${span(line(s, "top"), "kn cream")}${span(line(s, "top-right"), "ur cream")}</div>
      ${span(line(s, "name"), "name yellow")}
      ${WEAR}
    </div>`,
  "flex-red-tri": (s) => `
    <div class="sign flex" style="background:#8E2F2C">
      <div class="row top">${span(line(s, "top"), "kn cream")}${span(line(s, "top-right"), "ur cream")}</div>
      ${span(line(s, "name"), "name yellow")}
      ${WEAR}
    </div>`,
  // Projecting flex board (V04): a portrait print with the name, the trilingual lines, and a drawn
  // plate of food where real boards carry a photo (no photos are copied).
  "flex-food": (s) => `
    <div class="sign flex portrait" style="background:${s.bg ?? "#B8302A"}">
      ${span(line(s, "top"), "kn cream center small")}
      ${span(line(s, "name"), "pname")}
      <div class="plate"><div class="food" style="background:${s.food ?? "#C9762E"}"></div><div class="garnish"></div></div>
      ${span(line(s, "top-right"), "ur cream center")}
      ${span(line(s, "band"), "band")}
      ${WEAR}
    </div>`,
  // QR sticker: three finder squares and deterministic noise. Decorative, does not scan.
  "sticker-upi": (s) => {
    let seed = 7;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const n = 21, cells = [];
    const finder = (x, y) => (x < 7 && y < 7) || (x >= n - 7 && y < 7) || (x < 7 && y >= n - 7);
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      let on = rnd() > 0.52;
      if (finder(x, y)) {
        const fx = x >= n - 7 ? x - (n - 7) : x, fy = y >= n - 7 ? y - (n - 7) : y;
        on = fx === 0 || fx === 6 || fy === 0 || fy === 6 || (fx >= 2 && fx <= 4 && fy >= 2 && fy <= 4);
      }
      if (on) cells.push(`<rect x="${x}" y="${y}" width="1" height="1"/>`);
    }
    return `
      <div class="sign sticker">
        <svg viewBox="-1 -1 23 23" class="qr"><g fill="#1C1714">${cells.join("")}</g></svg>
        ${span(line(s, "name"), "upi")}
      </div>`;
  },
};

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Anton&family=Noto+Sans+Kannada:wght@800;900&family=Noto+Nastaliq+Urdu:wght@700&family=Noto+Sans:wght@600;700&family=Rozha+One&display=block');
  html, body { margin: 0; background: transparent; }
  .sign { box-sizing: border-box; width: 100vw; height: 100vh; display: flex; flex-direction: column;
          overflow: hidden; position: relative; }
  .flex { filter: saturate(0.86) contrast(0.96); border: 0.8vh solid #2B2624; }
  .board { border: 1.4vh solid #3A2A26; }
  .row { display: flex; justify-content: space-between; align-items: center; padding: 3.5vh 4vw 0; }
  .kn { font: 900 15vh/1.2 'Noto Sans Kannada'; }
  .ur { font: 700 13vh/1.3 'Noto Nastaliq Urdu'; color: #1E1B19; direction: rtl; }
  .red { color: #A33A3F; } .cream { color: #EFE2C4; } .center { text-align: center; padding-top: 4vh; }
  .small { font-size: 12vh; }
  .green { color: #1F4A2A; }
  .ur.cream { color: #EFE2C4; }
  .portrait { align-items: center; justify-content: space-between; }
  .portrait .kn { font-size: 8vh; padding-top: 2vh; }
  .portrait .ur { font-size: 6.5vh; line-height: 1.7; }
  .portrait .band { font-size: 5vh; width: 100%; padding: 1.4vh 0 1.2vh; }
  .pname { font: 400 11vh/1 'Anton'; color: #F6E7A8; text-align: center; padding: 1vh 2vw; -webkit-text-stroke: 0.3vh #3A1412; }
  .plate { width: 70vw; height: 38vw; margin: 1.5vh auto; border-radius: 50%; background: #F4F2EC; border: 0.6vh solid #D8D2C4;
           position: relative; box-shadow: 0 1vh 0 rgba(0,0,0,0.25); }
  .food { position: absolute; inset: 18% 14%; border-radius: 50%; filter: saturate(0.9); }
  .garnish { position: absolute; left: 44%; top: 30%; width: 14%; height: 18%; border-radius: 50%; background: #4E7A3A; }
  .darkgreen { color: #1F4A2A; -webkit-text-stroke: 0.5vh #10261A; font-size: 30vh; }
  .name { font: 400 33vh/1 'Anton'; text-align: center; letter-spacing: 0.03em; flex: 1;
          display: flex; align-items: center; justify-content: center; }
  .teal { color: #22857A; -webkit-text-stroke: 0.7vh #0E3B35; text-shadow: 0.9vh 0.9vh 0 rgba(14,59,53,0.35); }
  .yellow { color: #EBD58A; -webkit-text-stroke: 0.6vh #3A1412; text-shadow: 0.8vh 0.8vh 0 rgba(0,0,0,0.3); font-size: 30vh; }
  .serif { font: 400 23vh/1 'Rozha One'; color: #EFE2C4; text-align: center; flex: 1;
           display: flex; align-items: center; justify-content: center; letter-spacing: 0.02em; }
  .band { font: 400 12vh/1 'Anton'; color: #F1EEE6; background: #1E1B19; text-align: center;
          padding: 2.2vh 0 1.8vh; letter-spacing: 0.12em; text-transform: uppercase; }
  .band.thin { font-size: 9vh; background: #3A2A26; color: #D9C9A8; }
  .address { font: 600 8vh/1 'Noto Sans'; color: #3A3330; text-align: center; padding: 1.6vh 0 1.4vh; }
  .wear { position: absolute; inset: 0; pointer-events: none;
          background:
            linear-gradient(to bottom, rgba(255,255,255,0) 60%, rgba(70,55,40,0.28)),
            linear-gradient(to right, rgba(0,0,0,0.10), rgba(0,0,0,0) 12%, rgba(0,0,0,0) 88%, rgba(0,0,0,0.12)),
            linear-gradient(to right, rgba(0,0,0,0) 49.6%, rgba(0,0,0,0.08) 50%, rgba(0,0,0,0) 50.4%); }
  .sticker { background: #F4F2EC; border-radius: 4vh; padding: 6vh 6vw; align-items: center; border: 1vh solid #D8D2C4; }
  .qr { width: 86vw; height: auto; }
  .upi { font: 700 13vh/1 'Noto Sans'; color: #1C1714; margin-top: 3vh; letter-spacing: 0.08em; }
`;

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
const stationsDir = join(ROOT, "src", "data", "stations");
for (const file of readdirSync(stationsDir).filter((f) => f.endsWith(".json"))) {
  const station = JSON.parse(readFileSync(join(stationsDir, file), "utf8"));
  for (const sign of station.signs ?? []) {
    const pxPerM = Math.max(...sign.size_m) < 0.5 ? 2400 : 600;   // small stickers need more pixels
    const [w, h] = sign.size_m.map((m) => Math.round(m * pxPerM));
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
