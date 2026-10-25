// Review composite of the packed s03 art (task 14) before Station03.ts uses it: the layers placed from
// layers.json over the void lattice, plus the text Phaser will draw (rate board, scale readout, door
// words) so the blank render can be judged in context. Not shipped.
// Usage: node tools/preview_s03_art.mjs [out.png] [pose]   (pose: type | idle, default type)
import { chromium } from "@playwright/test";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = process.argv[2] ?? join(ROOT, "review", "s03-art.png");
const pose = process.argv[3] ?? "type";
const dir = join(ROOT, "public", "assets", "stations", "s03");
const { layers, anchors } = JSON.parse(readFileSync(join(dir, "layers.json"), "utf8"));
const order = ["bg", "crate_shadow", "crate", "riyaz_idle", `attendant_${pose}`];
const img = (name) => {
  const l = layers[name];
  const src = `data:image/png;base64,${readFileSync(join(dir, `${name}.png`)).toString("base64")}`;
  return `<img src="${src}" style="position:absolute;left:${l.x}px;top:${l.y}px;width:${l.w}px;height:${l.h}px">`;
};
const at = ([x, y], html, style = "") => `<div style="position:absolute;left:${x}px;top:${y}px;transform:translate(-50%,-50%);${style}">${html}</div>`;
const chip = `<span style="font:700 15px 'Baloo 2';background:#7A4B2C;color:#F4ECDE;border:2px solid #1C1714;border-radius:6px;padding:0 8px;margin-left:8px">Proposed</span>`;
const rates = [["Bone, sorted", "₹[__]/kg"], ["Offal, sorted", "₹[__]/kg"], ["Mixed", "₹[__]/kg"]];
// The board faces -Y, so on screen its rows run down-right along the wall (2:1 dimetric: 26.57°).
const board = `<div style="font:500 19px Hind;color:#1C1714;width:200px;transform:skewY(26.57deg)">${rates
  .map(([l, r]) => `<div style="display:flex;justify-content:space-between"><span>${l}</span><b style="font:700 19px 'Baloo 2'">${r}</b></div>`)
  .join("")}<div style="font:700 20px 'Baloo 2';margin-top:4px">Sorted earns more</div><div style="margin-top:2px">${chip.replace("margin-left:8px", "")}</div></div>`;
const card = (text, colour) =>
  `<div style="font:700 20px 'Baloo 2';background:#FBF7EF;color:${colour};border:3px solid #1C1714;border-radius:10px;padding:0 12px;white-space:nowrap">${text}</div>`;

const html = `<!doctype html><html><head>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Hind:wght@400;500&display=swap">
<style>body{margin:0}#f{position:relative;width:1920px;height:1080px;overflow:hidden;background:#1C1714}</style></head><body><div id="f">
${order.filter((n) => layers[n]).map(img).join("")}
${at(anchors.rate_board, board)}
${at(anchors.scale_display, card("1.0 kg", "#1C1714"))}
${at(anchors.door_a, card("Chamber A", "#2E6B34"), "margin-top:-46px")}
${at(anchors.door_b, card("Chamber B", "#1F5BA8"), "margin-top:-46px")}
<div style="position:absolute;left:24px;bottom:16px;font:400 18px Hind;color:#8F877C">Review composite · text overlays are what Station03.ts draws, not part of the render</div>
</div></body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.setContent(html, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
await page.locator("#f").screenshot({ path: out });
await browser.close();
console.log(out.replace(ROOT, "."));
