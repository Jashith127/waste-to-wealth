// The whole market (beat "map", after each run): Shivajinagar's real street grid (OSM, M01) with the
// same day played by every stall at once, so the system is something you play, not a caption.
// Run 1: every kilo goes to its nearest dump, separate trucks make trip after trip, every stall pays
// −₹5; tap a pile to clear it and watch it come back. Run 2: open the hub's drop window and the kilos
// converge (stalls hold theirs while it is shut), one pickup leaves for Renderer (example), and the
// loop comes back to the stalls (How it could close). Lenses 1/2/3: waste, money, power.
import { GameObjects, Math as PMath, Scene } from 'phaser';
import data from '../../data/map.json';
import { howTo, runs } from '../content';
import { goNext, type Beat } from '../flow';
import { getState } from '../state';
import { colour, css, font, FRAME, layout, motion } from '../theme';
import { drawCard, drawChip } from '../ui/card';
import { labelCard } from '../ui/greybox';
import { LevelComplete, levelInfo } from '../ui/LevelComplete';
import { Prompt } from '../ui/Prompt';

interface Way { tags: Record<string, string>; geom: [number, number][] }
interface Pt { x: number; y: number }
type Lens = 'waste' | 'money' | 'power';
interface Dot { o: GameObjects.Arc; from: Pt; to: Pt; t: number; speed: number; done: () => void }

const BOX = { x: 560, y: 160, w: 1300, h: 870 };          // the map card, below the objective card
const STALLS = 36;
const ROADS: Record<string, number> = { primary: 5, tertiary: 4, tertiary_link: 3, unclassified: 3, residential: 2.5, living_street: 2, service: 1.6 };

export class MarketMap extends Scene {
    private run: 1 | 2 = 1;
    private prompt!: Prompt;
    private project!: (lat: number, lon: number) => Pt;
    private market: Pt = { x: 0, y: 0 };
    private stalls: Pt[] = [];
    private dumps: { at: Pt; pile: GameObjects.Arc; size: number }[] = [];
    private dots: Dot[] = [];
    private layer: Record<Lens, GameObjects.Container> = {} as Record<Lens, GameObjects.Container>;
    private lens: Lens = 'waste';
    private lensButtons: Record<Lens, GameObjects.Container> = {} as Record<Lens, GameObjects.Container>;
    private phase = '';
    private clears = 0;
    private held: number[] = [];
    private leaving = false;

    constructor() {
        super('MarketMap');
    }

    preload() {
        this.load.json('market_streets', 'assets/map/shivajinagar-streets.json');
    }

    create({ beat }: { beat: Beat }) {
        this.run = beat.run;
        this.leaving = false;
        this.dots = [];
        this.dumps = [];
        this.clears = 0;
        this.held = [];
        this.add.tileSprite(0, 0, FRAME.width, FRAME.height, 'lattice').setOrigin(0);
        this.drawMap(this.cache.json.get('market_streets').ways as Way[]);
        for (const lens of ['waste', 'money', 'power'] as Lens[]) this.layer[lens] = this.add.container(0, 0).setDepth(10);
        this.sidePanel();
        const prompts = data.runs[String(this.run) as '1' | '2'].prompts as Record<string, string>;
        this.prompt = new Prompt(this, layout.prompt.x, layout.prompt.y, {
            badge: 'MAP', title: data.title, phase: runs[this.run].clock?.map,
            steps: howTo(this.run, 'map')?.steps.map((st) => ({ label: st.label, mouse: st.mouse, match: st.prompts.map((k) => prompts[k]).filter(Boolean) })),
        });

        const kb = this.input.keyboard!;
        kb.on('keydown-ONE', () => this.setLens('waste'));
        kb.on('keydown-TWO', () => this.setLens('money'));
        kb.on('keydown-THREE', () => this.setLens('power'));
        kb.on('keydown-SPACE', () => this.press());
        kb.on('keydown-RIGHT', () => this.phase === 'leave' && this.leave());
        this.setLens('waste');
        if (this.run === 1) this.startRun1();
        else this.startRun2();
        (window as unknown as { __ready?: string }).__ready = 'map';
        this.cameras.main.fadeIn(getState(this).reducedMotion ? 1 : motion.transition, 28, 23, 20);
    }

    update(_t: number, delta: number) {
        for (const d of [...this.dots]) {
            d.t = Math.min(1, d.t + delta * d.speed);
            d.o.setPosition(d.from.x + (d.to.x - d.from.x) * d.t, d.from.y + (d.to.y - d.from.y) * d.t);
            if (d.t >= 1) {
                this.dots.splice(this.dots.indexOf(d), 1);
                d.o.destroy();
                d.done();
            }
        }
    }

    // --- the map -------------------------------------------------------------------------------------

    private drawMap(ways: Way[]) {
        const pts = ways.flatMap((w) => w.geom);
        const lat0 = Math.min(...pts.map((p) => p[0])), lat1 = Math.max(...pts.map((p) => p[0]));
        const lon0 = Math.min(...pts.map((p) => p[1])), lon1 = Math.max(...pts.map((p) => p[1]));
        const k = Math.cos((lat0 * Math.PI) / 180);
        const s = Math.min(BOX.w / ((lon1 - lon0) * k), BOX.h / (lat1 - lat0));
        const ox = BOX.x + (BOX.w - (lon1 - lon0) * k * s) / 2, oy = BOX.y + (BOX.h - (lat1 - lat0) * s) / 2;
        this.project = (lat, lon) => ({ x: ox + (lon - lon0) * k * s, y: oy + (lat1 - lat) * s });

        const g = this.add.graphics();
        drawCard(g, BOX.x - 20, BOX.y - 20, BOX.w + 40, BOX.h + 40);
        const poly = (w: Way) => w.geom.map(([la, lo]) => this.project(la, lo));
        for (const w of ways) {
            if (!w.tags.building) continue;
            const p = poly(w);
            const market = /rus+el+ market/i.test(w.tags.name ?? '');
            g.fillStyle(market ? 0xe8d8cc : 0xe2d8c4, 1).fillPoints(p.map((q) => new PMath.Vector2(q.x, q.y)), true);
            g.lineStyle(market ? 3 : 1, colour.ink, market ? 0.9 : 0.25).strokePoints(p.map((q) => new PMath.Vector2(q.x, q.y)), true);
            if (market) this.market = p.reduce((a, q) => ({ x: a.x + q.x / p.length, y: a.y + q.y / p.length }), { x: 0, y: 0 });
        }
        const roadPts: Pt[] = [];
        for (const w of ways) {
            const width = ROADS[w.tags.highway ?? ''];
            if (!width) continue;
            const p = poly(w);
            g.lineStyle(width, 0x8f877c, 0.9).strokePoints(p.map((q) => new PMath.Vector2(q.x, q.y)));
            for (let i = 0; i + 1 < p.length; i++) {
                const n = Math.ceil(Math.hypot(p[i + 1].x - p[i].x, p[i + 1].y - p[i].y) / 18);
                for (let j = 0; j < n; j++) roadPts.push({ x: p[i].x + ((p[i + 1].x - p[i].x) * j) / n, y: p[i].y + ((p[i + 1].y - p[i].y) * j) / n });
            }
        }
        for (const [name, re] of [['Russell Market', /rus+el+ market/i], ['Cockburn Road', /cockburn/i], ['Shivaji Road', /shivaji road/i]] as const) {
            const w = ways.find((x) => re.test(x.tags.name ?? ''));
            if (!w) continue;
            const p = poly(w)[Math.floor(w.geom.length / 2)];
            this.add.text(p.x, p.y - (name === 'Russell Market' ? 58 : 16), name, { fontFamily: font.display, fontSize: 22, fontStyle: '700', color: css.ink }).setOrigin(0.5).setDepth(12);
        }
        this.add.text(BOX.x + BOX.w, BOX.y + BOX.h + 4, data.attribution, { fontFamily: font.body, fontSize: 18, color: css.muted }).setOrigin(1, 1);

        // stalls along the streets near the market (placed to show the pattern, not a survey)
        const rnd = new PMath.RandomDataGenerator(['shivajinagar']);
        const near = roadPts.filter((p) => Math.hypot(p.x - this.market.x, p.y - this.market.y) < 330 && Math.hypot(p.x - this.market.x, p.y - this.market.y) > 70);
        this.stalls = [];
        while (this.stalls.length < STALLS && near.length) {
            const p = near.splice(rnd.between(0, near.length - 1), 1)[0];
            if (this.stalls.every((q) => Math.hypot(q.x - p.x, q.y - p.y) > 26)) this.stalls.push(p);
        }
        for (const p of this.stalls) {
            this.add.rectangle(p.x, p.y, 13, 13, 0xd9774f, 1).setStrokeStyle(2, colour.ink, 0.9).setDepth(11);
        }
    }

    private sidePanel() {
        const x = layout.gutter, y = layout.hudBottom + 10;
        const g = this.add.graphics();
        drawCard(g, x, y, 450, 560);
        this.add.text(x + 28, y + 48, data.title, { fontFamily: font.display, fontSize: 40, fontStyle: '800', color: css.ink }).setOrigin(0, 0.5);
        const run = data.runs[String(this.run) as '1' | '2'];
        this.add.text(x + 28, y + 98, run.subtitle, { fontFamily: font.body, fontSize: 28, color: css.ink, wordWrap: { width: 400 } }).setOrigin(0, 0.5);
        if ('proposed' in run && run.proposed) {
            const cg = this.add.graphics();
            drawChip(cg, x + 28, y + 130, 130, 36, colour.brown);
            this.add.text(x + 93, y + 148, 'Proposed', { fontFamily: font.display, fontSize: 22, fontStyle: '700', color: css.cream }).setOrigin(0.5);
        }
        (['waste', 'money', 'power'] as Lens[]).forEach((lens, i) => {
            const by = y + 220 + i * 78;
            const c = this.add.container(x + 28, by);
            const bg = this.add.graphics();
            const t = this.add.text(70, 0, data.lenses[lens], { fontFamily: font.display, fontSize: 30, fontStyle: '700', color: css.ink }).setOrigin(0, 0.5);
            const key = this.add.text(26, 0, String(i + 1), { fontFamily: font.display, fontSize: 24, fontStyle: '700', color: css.cream }).setOrigin(0.5);
            c.add([bg, key, t]).setSize(390, 62).setInteractive({ useHandCursor: true }).on('pointerup', () => this.setLens(lens));
            c.setData('bg', bg);
            this.lensButtons[lens] = c;
        });
        this.add.text(x + 28, y + 500, data.stall_count_note, { fontFamily: font.body, fontSize: 21, color: css.muted, wordWrap: { width: 400 } }).setOrigin(0, 0.5);
    }

    private setLens(lens: Lens) {
        this.lens = lens;
        for (const [k, c] of Object.entries(this.lensButtons) as [Lens, GameObjects.Container][]) {
            const bg = c.getData('bg') as GameObjects.Graphics;
            bg.clear().fillStyle(k === lens ? colour.ink : colour.cream, 1).fillRoundedRect(0, -31, 390, 62, 14);
            bg.fillStyle(k === lens ? colour.cream : colour.ink, 1).fillRoundedRect(8, -20, 36, 40, 8);
            (c.list[1] as GameObjects.Text).setColor(k === lens ? css.ink : css.cream);
            (c.list[2] as GameObjects.Text).setColor(k === lens ? css.cream : css.ink);
            this.layer[k].setVisible(k === lens);
        }
    }

    // --- Run 1: every stall dumps ---------------------------------------------------------------------

    private startRun1() {
        const p = data.runs['1'].prompts;
        this.phase = 'watch';
        this.prompt.show(p.watch);
        // dump spots: just outside the market, round its back
        const m = this.market;
        for (const [dx, dy] of [[70, 40], [-60, 70], [95, -30], [-20, -85]]) {
            const at = { x: m.x + dx, y: m.y + dy };
            const pile = this.add.circle(at.x, at.y, 8, 0x5e5249, 1).setStrokeStyle(2, colour.ink, 0.8);
            this.layer.waste.add(pile);
            this.dumps.push({ at, pile, size: 6 });
            pile.setInteractive({ useHandCursor: true }).on('pointerup', () => this.clearPile(this.dumps.find((d) => d.pile === pile)!));
        }
        this.time.addEvent({ delay: 260, loop: true, callback: () => this.emitRun1() });
        this.time.addEvent({ delay: 1400, loop: true, callback: () => this.truckTrip() });
        this.time.delayedCall(4500, () => { this.phase = 'clear'; this.prompt.show(p.clear); });
        this.time.delayedCall(14000, () => this.toLeave(p.leave));
        this.time.addEvent({ delay: 700, loop: true, callback: () => this.powerFlicker() });
    }

    private emitRun1() {
        const from = this.stalls[PMath.Between(0, this.stalls.length - 1)];
        const dump = this.dumps.reduce((a, d) => (Math.hypot(d.at.x - from.x, d.at.y - from.y) < Math.hypot(a.at.x - from.x, a.at.y - from.y) ? d : a));
        this.dot(this.layer.waste, from, dump.at, 0xb9b3a3, 0.0012, () => {
            dump.size = Math.min(34, dump.size + 0.8);
            dump.pile.setRadius(dump.size);
        });
        this.moneyTag(from, data.runs['1'].fee, colour.cost, true);
    }

    /** A city truck takes a little from one pile, on its own trip, again and again. */
    private truckTrip() {
        const d = this.dumps[PMath.Between(0, this.dumps.length - 1)];
        const truck = this.add.rectangle(d.at.x, d.at.y, 20, 12, 0x5e5952).setStrokeStyle(2, colour.ink, 0.8);
        this.layer.waste.add(truck);
        d.size = Math.max(6, d.size - 3);
        d.pile.setRadius(d.size);
        const exit = { x: BOX.x + BOX.w + 10, y: d.at.y + PMath.Between(-120, 120) };
        this.tweens.add({ targets: truck, ...exit, duration: 1600, ease: 'Sine.easeIn', onComplete: () => truck.destroy() });
    }

    /** Clearing one pile by hand: it empties, and the street fills it again. */
    private clearPile(d: { pile: GameObjects.Arc; size: number }) {
        if (this.run !== 1) return;
        d.size = 6;
        d.pile.setRadius(6);
        this.events.emit('sfx', 'sweep');
        if (++this.clears === 3) this.prompt.show(data.runs['1'].prompts.again);
    }

    // --- Run 2: the hub -------------------------------------------------------------------------------

    private hubRing?: GameObjects.Arc;

    private startRun2() {
        const p = data.runs['2'].prompts;
        this.phase = 'open';
        this.prompt.show(p.open, 'Space');
        const hub = this.add.circle(this.market.x, this.market.y, 22, colour.card, 1).setStrokeStyle(4, colour.ink, 1).setDepth(12);
        this.add.text(this.market.x, this.market.y, data.runs['2'].hub, { fontFamily: font.display, fontSize: 20, fontStyle: '700', color: css.ink }).setOrigin(0.5).setDepth(13);
        hub.setInteractive({ useHandCursor: true }).on('pointerup', () => this.press());
        this.hubRing = this.add.circle(this.market.x, this.market.y, 40).setStrokeStyle(4, colour.cream, 0.95).setDepth(12);
        if (!getState(this).reducedMotion) this.tweens.add({ targets: this.hubRing, scale: 1.15, alpha: 0.4, duration: 700, yoyo: true, repeat: -1 });
        // until the window opens, each stall holds its kilo
        this.held = this.stalls.map(() => 1);
        this.time.addEvent({ delay: 700, loop: true, callback: () => this.powerSolar() });
    }

    private press() {
        if (this.phase === 'open') return this.openWindow();
        if (this.phase === 'leave') this.leave();
    }

    /** The drop window: while it is open every stall's kilo converges on the hub. */
    private openWindow() {
        const p = data.runs['2'].prompts;
        this.phase = 'window';
        this.hubRing?.destroy();
        this.prompt.show(p.window);
        const ring = this.add.arc(this.market.x, this.market.y, 44, -90, 270).setStrokeStyle(6, colour.cream, 1).setDepth(12);
        this.tweens.add({ targets: ring, endAngle: -90, duration: 4500, onComplete: () => { ring.destroy(); this.closeWindow(); } });
        this.stalls.forEach((s, i) => this.time.delayedCall(PMath.Between(0, 3800), () => {
            if (!this.held[i]) return;
            this.held[i] = 0;
            this.dot(this.layer.waste, s, this.market, 0x1f5ba8, 0.0011, () => undefined);
            this.dot(this.layer.money, this.market, s, colour.income, 0.0009, () => undefined);
            this.moneyTag(s, data.runs['2'].payout, colour.income, false);
        }));
    }

    private closeWindow() {
        const p = data.runs['2'].prompts;
        this.phase = 'pickup';
        this.prompt.show(p.pickup);
        const truck = this.add.rectangle(this.market.x, this.market.y, 30, 18, 0xd9d6ce).setStrokeStyle(3, colour.ink, 1).setDepth(12);
        const edge = { x: BOX.x + BOX.w - 30, y: this.market.y - 40 };
        this.tweens.add({
            targets: truck, ...edge, duration: getState(this).reducedMotion ? 1 : 1600, ease: 'Sine.easeInOut',
            onComplete: () => {
                labelCard(this, edge.x - 140, edge.y - 60, data.runs['2'].renderer, { band: colour.offsite, size: 26 });
                this.loop();
            },
        });
    }

    /** The loop back: a dashed arc from the renderer, round to the stalls (How it could close). */
    private loop() {
        const p = data.runs['2'].prompts;
        this.phase = 'loop';
        this.prompt.show(p.loop);
        const g = this.add.graphics().setDepth(11);
        const a = { x: BOX.x + BOX.w - 60, y: this.market.y - 20 }, c = { x: this.market.x + 40, y: BOX.y + BOX.h - 80 };
        const ctrl = { x: BOX.x + BOX.w - 40, y: BOX.y + BOX.h - 60 };
        const curve = new PMath.Vector2(0, 0);
        for (let i = 0; i < 26; i += 2) {
            const t0 = i / 26, t1 = (i + 1) / 26;
            const q = (t: number) => curve.set((1 - t) * (1 - t) * a.x + 2 * (1 - t) * t * ctrl.x + t * t * c.x, (1 - t) * (1 - t) * a.y + 2 * (1 - t) * t * ctrl.y + t * t * c.y).clone();
            const p0 = q(t0), p1 = q(t1);
            g.lineStyle(4, colour.brown, 0.9).lineBetween(p0.x, p0.y, p1.x, p1.y);
        }
        labelCard(this, c.x + 40, c.y - 40, p.loop, { proposed: true, size: 26 });
        this.time.delayedCall(1800, () => this.toLeave(p.leave));
    }

    // --- shared ---------------------------------------------------------------------------------------

    private dot(layer: GameObjects.Container, from: Pt, to: Pt, fill: number, speed: number, done: () => void) {
        const o = this.add.circle(from.x, from.y, 6, fill, 1).setStrokeStyle(2, colour.ink, 0.7);
        layer.add(o);
        this.dots.push({ o, from, to, t: 0, speed: getState(this).reducedMotion ? 1 : speed, done });
    }

    /** −₹5 leaving a stall (Run 1) or the estimated payout arriving (Run 2), on the money lens. */
    private moneyTag(at: Pt, text: string, fill: number, rising: boolean) {
        if (PMath.Between(0, 2) > 0) return;
        const t = this.add.text(at.x, at.y - 12, text, { fontFamily: font.display, fontSize: 22, fontStyle: '800', color: `#${fill.toString(16).padStart(6, '0')}` }).setOrigin(0.5);
        this.layer.money.add(t);
        this.tweens.add({ targets: t, y: at.y - (rising ? 46 : 30), alpha: 0, duration: 1200, onComplete: () => t.destroy() });
    }

    /** Power lens, Run 1: the grid flickers out across the blocks; nothing keeps the cold. */
    private powerFlicker() {
        if (this.lens !== 'power') return;
        const p = this.stalls[PMath.Between(0, this.stalls.length - 1)];
        const o = this.add.circle(p.x, p.y, 16, 0x2a3550, 0.5);
        this.layer.power.add(o);
        this.tweens.add({ targets: o, alpha: 0, duration: 900, onComplete: () => o.destroy() });
    }

    /** Power lens, Run 2: the grid goes, the hub stays lit on its own solar. */
    private powerSolar() {
        if (this.lens !== 'power' || this.layer.power.length) return;
        const dark = this.add.rectangle(BOX.x, BOX.y, BOX.w, BOX.h, 0x141a2e, 0.45).setOrigin(0);
        const glow = this.add.circle(this.market.x, this.market.y, 60, 0xfff3d6, 0.35);
        this.layer.power.add([dark, glow]);
        this.tweens.add({ targets: glow, scale: 1.15, duration: 900, yoyo: true, repeat: -1 });
    }

    private toLeave(text: string) {
        if (this.phase === 'leave') return;
        this.phase = 'leave';
        this.prompt.show(text, '→');
        const info = levelInfo(this.run, getState(this).beat, data.title);
        if (info) this.time.delayedCall(getState(this).reducedMotion ? 0 : 650, () => !this.leaving && new LevelComplete(this, info, () => this.leave()));
    }

    private leave() {
        if (this.leaving) return;
        this.leaving = true;
        goNext(this);
    }
}
