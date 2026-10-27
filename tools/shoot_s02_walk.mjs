// Drive Station 2's free walk and screenshot it: the start, walking behind set pieces, the handcart
// coming down the pavement, stepping aside, the pile. Starts its own Vite dev server.
// Usage: node tools/shoot_s02_walk.mjs [--run 2]   -> review/s02/1280x720[-run2]-walk-NN-<state>.png
import { chromium } from "@playwright/test";
import { createServer } from "vite";
import { mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const run = args.includes("--run") ? args[args.indexOf("--run") + 1] : "1";
const out = join(ROOT, "review", "s02");
mkdirSync(out, { recursive: true });

const server = await createServer({ root: ROOT, configFile: join(ROOT, "vite/config.dev.mjs"), server: { port: 8098 }, logLevel: "error" });
await server.listen();
const browser = await chromium.launch({ args: ["--use-angle=d3d11", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
page.on("pageerror", (e) => errors.push(e.message));
await page.goto(`http://localhost:8098/?station=s02&run=${run}&noBrief`);
await page.waitForFunction(() => window.__ready, null, { timeout: 180000 });

const scene = () => page.evaluate(() => {
    const s = window.__game.scene.getScene("s02");
    return { pos: s.riyaz.pos, dir: s.riyaz.dir, phase: s.phase, cart: s.cart.state, cartDx: s.cart.dx };
});
let n = 0;
const shot = async (name) => {
    n += 1;
    await page.screenshot({ path: join(out, `1280x720${run === "2" ? "-run2" : ""}-walk-${String(n).padStart(2, "0")}-${name}.png`) });
    console.log(name, JSON.stringify(await scene()));
};
const hold = async (keys, ms) => {
    for (const k of keys) await page.keyboard.down(k);
    await page.waitForTimeout(ms);
    for (const k of keys) await page.keyboard.up(k);
};

await shot("start");
await hold(["ArrowUp"], 500);                       // toward the shops, behind the stove cart's line
await hold(["ArrowRight"], 900);
await shot("by-the-crates");
await hold(["ArrowRight"], 600);
await page.waitForTimeout(250);
await shot("walking");
await hold(["ArrowDown"], 700);                     // to the kerb side
await hold(["ArrowRight"], 900);
await shot("cart-coming");
await hold(["ArrowUp"], 900);                       // step aside toward the shops
await shot("stepped-aside");
await page.waitForTimeout(3500);
await shot("cart-passing");
await hold(["ArrowLeft"], 600);                     // and back the other way
await shot("walking-back");
for (let i = 0; i < 30 && (await scene()).phase === "walk"; i++) await hold(["ArrowRight"], 700);
await page.waitForTimeout(600);
await shot("arrived");
if ((await scene()).phase === "dump") {
    await page.keyboard.press("Space");
    await page.waitForTimeout(800);
    await shot("dumped");
}
console.log(errors.length ? `ERRORS:\n${errors.join("\n")}` : "no console errors");
await browser.close();
await server.close();
