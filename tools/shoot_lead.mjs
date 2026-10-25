// Lead review shots: the HUD clock, the end card, and a grey-box playthrough from Run 1 · s01 to the end card.
// Usage: node tools/shoot_lead.mjs   -> review/hud/*.png, review/end/*.png; fails on any console error.
import { chromium } from "@playwright/test";
import { createServer } from "vite";
import { mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const [W, H] = [1920, 1080];
const errors = [];

const server = await createServer({ root: ROOT, configFile: join(ROOT, "vite/config.dev.mjs"), server: { port: 8098 }, logLevel: "error" });
await server.listen();
const browser = await chromium.launch({ args: ["--use-angle=d3d11", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"] });

async function open(query, ready) {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on("console", (m) => m.type() === "error" && errors.push(`${query}: ${m.text()}`));
  page.on("pageerror", (e) => errors.push(`${query}: ${e.message}`));
  await page.goto(`http://localhost:8098/?${query}`);
  await waitReady(page, ready);
  await page.mouse.click(4, H - 4);
  await page.waitForTimeout(400);
  return page;
}
const waitReady = (page, ready) => page.waitForFunction((s) => window.__ready === s, ready, { timeout: 30000 });
const unready = (page) => page.evaluate(() => (window.__ready = null));
async function press(page, ...keys) {
  for (const k of keys) { await page.keyboard.press(k); await page.waitForTimeout(520); }
}
const shot = async (page, dir, name) => {
  mkdirSync(join(ROOT, "review", dir), { recursive: true });
  const file = join(ROOT, "review", dir, `${W}x${H}-${name}.png`);
  await page.screenshot({ path: file });
  console.log(file.replace(ROOT, "."));
};

// HUD clock: one beat per phase.
for (const [query, ready, name] of [
  ["run=1&beat=0", "s01", "01-s01-morning-cut"],
  ["run=2&beat=3", "s04", "02-s04-evening-rush"],
  ["run=1&beat=2", "s01", "03-s01-night"],
]) {
  const page = await open(query, ready);
  await shot(page, "hud", name);
  await page.close();
}

// End card: ledger, first and last belief, Play again, and the clean Run 1 it starts.
{
  const page = await open("run=2&beat=7", "end");
  await page.waitForTimeout(700);             // the card's fade-in
  await shot(page, "end", "01-ledger");
  await press(page, "Space");
  await shot(page, "end", "02-belief-1");
  await press(page, "Space", "Space", "Space");
  await page.waitForTimeout(300);
  await shot(page, "end", "03-belief-4-play-again");
  await unready(page);
  await page.mouse.click(W / 2, Math.round(965 * (H / 1080)));
  await waitReady(page, "s01");
  const state = await page.evaluate(() => window.__game.registry.get("state"));
  if (state.run !== 1 || state.beat !== 0 || state.kilo.tag || state.blueprintOpen) errors.push(`replay state not clean: ${JSON.stringify(state)}`);
  await shot(page, "end", "04-replay-run1");
  await page.close();
}

// Grey-box playthrough: Run 1 · s01 → … → Run 2 → end card, with the keys each beat needs.
{
  const t0 = Date.now();
  const page = await open("run=1&beat=0", "s01");
  const beats = [];
  for (let i = 0; i < 20; i++) {
    const { run, beat, station } = await page.evaluate(() => window.__game.registry.get("state"));
    beats.push(`${run}:${beat}:${station}`);
    if (station === "s01") await press(page, "Space", "Space", "Space", "Space");
    await unready(page);
    await press(page, "ArrowRight");
    const next = await page.waitForFunction(() => window.__ready, null, { timeout: 30000 }).then((h) => h.jsonValue());
    await page.waitForTimeout(400);
    if (next === "end") break;
  }
  await shot(page, "end", "05-reached-by-play");
  console.log(`played ${beats.join(" → ")} → end in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  await page.close();
}

await browser.close();
await server.close();
if (errors.length) { console.error(errors.join("\n")); process.exit(1); }
console.log("no console errors");
