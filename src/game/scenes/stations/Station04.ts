// Station 4 · Cold room, inside the hub (Run 2). Drag the sealed crate into Chamber B and the unsold
// meat into Chamber A: each door swings open as its item goes in (never both at once). Then up to the
// roof for the evening: a time-lapse from day to dusk, the neighbourhood's lights come on, the grid
// goes, only the hub stays lit on its own solar, and the camera drops through the skylight back to
// the chambers, still cold. Each door carries its word as well as its colour.
// Flow after DeepSeek's first pass at task 04; sets from art/scripts/s04_build.py and s04roof_build.py.
import { GameObjects, Display } from 'phaser';
import { colour, css, font, FRAME, motion } from '../../theme';
import { drawCard, keepClear } from '../../ui/card';
import { labelCard, paidTag } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import type { Layers } from '../StationScene';
import { StationScene } from '../StationScene';

type Phase = 'waste' | 'meat' | 'cut' | 'solar' | 'leave';
type Key = 'A' | 'B';
interface Chamber { label: string; sub: string; meaning: 'income' | 'offsite' }
interface Params { chambers: Record<Key, Chamber>; rule: string; solar_label: string }
interface Item { img: GameObjects.Image; shadow: GameObjects.Image; centre: { x: number; y: number }; home: { x: number; y: number } }

const SNAP_PX = 140;             // how close to a door's centre a drop counts
const LAPSE_MS = 4200;           // day to dusk on the roof
const SKY = {                    // [top, bottom] of the sky behind the roof
    day: [0x8fb3d1, 0xdce6ec],
    dusk: [0x3e4a78, 0xf2a15e],
    night: [0x141a2e, 0x2a3550],
} as const;

export default class Station04 extends StationScene {
    private phase: Phase = 'waste';
    private items!: Record<'crate' | 'tray', Item>;
    private doors!: Record<Key, { shut: GameObjects.Image; open: GameObjects.Image; shutNight: GameObjects.Image; openNight: GameObjects.Image }>;
    private nightLayers!: GameObjects.Image[];
    private riyaz!: GameObjects.Image;
    private ruleCard!: GameObjects.Container;
    private labels: GameObjects.Container[] = [];
    private ring?: GameObjects.Arc;
    private p!: Params;
    private roof?: { box: GameObjects.Container; sky: GameObjects.Graphics; sun: GameObjects.Arc; energy: GameObjects.Graphics; dusk: GameObjects.Image; night: GameObjects.Image; layers: Layers };
    private skyT = { day: 1, dusk: 0, night: 0 };
    private flow = false;

    constructor() {
        super('s04');
    }

    preload() {
        this.loadLayers();
        this.load.pack('s04roof', 'assets/stations/s04roof/pack.json');
        this.load.json('s04roof_layers', 'assets/stations/s04roof/layers.json');
    }

    protected build() {
        this.phase = 'waste';
        this.flow = false;
        this.labels = [];
        this.p = this.stationData.params as unknown as Params;
        this.layer('bg');
        const night = this.layer('bg_night').setAlpha(0);
        this.doors = {
            A: { shut: this.layer('door_a'), open: this.layer('door_a_open').setVisible(false), shutNight: this.layer('door_a_night').setAlpha(0), openNight: this.layer('door_a_open_night').setVisible(false) },
            B: { shut: this.layer('door_b'), open: this.layer('door_b_open').setVisible(false), shutNight: this.layer('door_b_night').setAlpha(0), openNight: this.layer('door_b_open_night').setVisible(false) },
        };
        this.riyaz = this.layer('riyaz_idle');
        const riyazNight = this.layer('riyaz_idle_night').setAlpha(0);
        this.nightLayers = [night, this.doors.A.shutNight, this.doors.B.shutNight, riyazNight];
        this.items = { crate: this.item('crate'), tray: this.item('meat_tray') };

        for (const key of ['A', 'B'] as const) this.labels.push(this.doorLabel(key));
        this.ruleCard = this.rule();
        new KiloTag(this, FRAME.width - 260, 20, paidTag(this), this.state.reducedMotion).setDepth(30);

        const kb = this.input.keyboard!;
        kb.on('keydown-SPACE', () => this.press());
        kb.on('keydown-ENTER', () => this.press());
        kb.on('keydown-RIGHT', () => this.phase === 'leave' && this.leave());
        this.input.on('drag', (_p: unknown, img: GameObjects.Image, x: number, y: number) => {
            const it = this.itemFor(img);
            it.img.setPosition(x, y);
            it.shadow.setAlpha(0.4);
        });
        this.input.on('dragend', (_p: unknown, img: GameObjects.Image) => this.drop(this.itemFor(img)));

        this.prompt.show(this.prompts().waste, 'Space');
        this.focus();
    }

    update(time: number) {
        if (this.flow) this.drawEnergy(time);
    }

    /** A draggable prop layer with its contact shadow; `centre` is its anchor relative to the image. */
    private item(name: 'crate' | 'meat_tray'): Item {
        const shadow = this.layer(`${name}_shadow`);
        const img = this.layer(name);
        const a = this.anchor(`${name}_centre`);
        return { img, shadow, centre: { x: a.x - img.x, y: a.y - img.y }, home: { x: img.x, y: img.y } };
    }

    private itemFor(img: GameObjects.Image) {
        return img === this.items.crate.img ? this.items.crate : this.items.tray;
    }

    /** The one item that may move now, with its hint ring. */
    private focus() {
        this.ring?.destroy();
        for (const it of Object.values(this.items)) it.img.disableInteractive();
        const it = this.phase === 'waste' ? this.items.crate : this.phase === 'meat' ? this.items.tray : undefined;
        if (!it) return;
        it.img.setInteractive({ draggable: true, useHandCursor: true });
        this.ring = this.hint(it.home.x + it.centre.x, it.home.y + it.centre.y, 80);
    }

    private doorLabel(key: Key) {
        const ch = this.p.chambers[key];
        const at = this.anchor(`door_${key.toLowerCase()}_label`);
        // A sits up-left of its door and B down-right of its own, so the two cards never overlap
        const c = this.add.container(at.x + (key === 'A' ? -110 : 60), at.y).setDepth(35);
        const title = this.add.text(0, -14, ch.label, { fontFamily: font.display, fontSize: 30, fontStyle: '700', color: css[ch.meaning] }).setOrigin(0.5);
        const sub = this.add.text(0, 20, ch.sub, { fontFamily: font.body, fontSize: 21, color: css.muted }).setOrigin(0.5);
        const w = Math.max(title.width, sub.width) + 36, h = 90;
        const g = this.add.graphics();
        drawCard(g, -w / 2, -h / 2 - 4, w, h, colour[ch.meaning]);
        c.add([g, title, sub]);
        keepClear(c, w, h + 8);
        return c;
    }

    private rule() {
        // on the open floor in front of the doors: clear of both windows, the doorways and Riyaz
        const at = this.anchor('rule');
        return labelCard(this, at.x - 60, at.y + 520, this.p.rule, { size: 24 });
    }

    private press() {
        if (this.phase === 'waste') this.accept(this.items.crate, 'B');
        else if (this.phase === 'meat') this.accept(this.items.tray, 'A');
        else if (this.phase === 'leave') this.leave();
    }

    private drop(it: Item) {
        const want: Key = this.phase === 'waste' ? 'B' : 'A';
        const other: Key = want === 'A' ? 'B' : 'A';
        const c = { x: it.img.x + it.centre.x, y: it.img.y + it.centre.y };
        const near = (k: Key) => { const d = this.anchor(`door_${k.toLowerCase()}`); return Math.hypot(c.x - d.x, c.y - d.y) <= SNAP_PX; };
        if (near(want)) return this.accept(it, want);
        if (near(other)) this.refuse();
        this.tweens.add({ targets: it.img, ...it.home, duration: this.state.reducedMotion ? 1 : 300, ease: 'Back.easeOut', onComplete: () => it.shadow.setAlpha(1) });
    }

    /** Through its door: the door swings open, the item goes in, the door shuts. */
    private accept(it: Item, key: Key) {
        const wasWaste = this.phase === 'waste';
        this.phase = wasWaste ? 'meat' : 'cut';
        it.img.disableInteractive();
        it.shadow.setVisible(false);
        const d = this.anchor(`door_${key.toLowerCase()}`);
        const door = this.doors[key];
        door.shut.setVisible(false);
        door.open.setVisible(true);
        this.events.emit('sfx', 'door_open');
        const shut = () => { door.open.setVisible(false); door.shut.setVisible(true); this.events.emit('sfx', 'door_shut'); };
        if (this.state.reducedMotion) {
            it.img.setVisible(false);
            this.time.delayedCall(600, shut);
        } else {
            this.tweens.add({
                targets: it.img, x: d.x - it.centre.x, y: d.y - it.centre.y + 30, alpha: 0, duration: 520, delay: 120, ease: 'Cubic.easeIn',
                onComplete: () => this.time.delayedCall(250, shut),
            });
        }
        if (wasWaste) this.prompt.show(this.prompts().meat, 'Space');
        this.focus();                                   // after the prompt: the hint shows its key
        if (wasWaste) return;
        this.time.delayedCall(1300, () => this.toRoof());
    }

    /** Wrong door: the item springs back and the rule says why. */
    private refuse() {
        if (!this.state.reducedMotion) this.tweens.add({ targets: this.ruleCard, scale: { from: 1.12, to: 1 }, duration: 320, ease: 'Sine.easeOut' });
    }

    // --- the roof: the evening, the cut, the solar ----------------------------------------------------

    private toRoof() {
        const layers = this.cache.json.get('s04roof_layers') as Layers | undefined;
        if (!layers || !this.textures.exists('s04roof_bg')) return this.powerCutHere();     // roof not packed: cut in place
        const box = this.add.container(0, 0).setDepth(25).setAlpha(0);
        const sky = this.add.graphics();
        const sun = this.add.circle(FRAME.width * 0.62, 120, 46, 0xffe2b8, 1);
        const img = (name: string) => { const l = layers.layers[name]; return this.add.image(l.x, l.y, `s04roof_${name}`).setOrigin(0); };
        const day = img('bg'), dusk = img('bg_dusk').setAlpha(0), night = img('bg_night').setAlpha(0);
        const energy = this.add.graphics();
        box.add([sky, sun, day, dusk, night, energy]);
        this.roof = { box, sky, sun, energy, dusk, night, layers };
        this.labels.forEach((l) => l.setVisible(false));
        this.ruleCard.setVisible(false);
        this.skyT = { day: 1, dusk: 0, night: 0 };
        this.drawSky();
        this.flow = true;

        const rm = this.state.reducedMotion;
        this.tweens.add({ targets: box, alpha: 1, duration: rm ? 1 : motion.transition });
        this.prompt.show(this.prompts().solar);
        // the time-lapse: the sky warms, the sun sinks behind the skyline, the windows light up
        this.tweens.add({ targets: this.skyT, dusk: 1, duration: rm ? 1 : LAPSE_MS, ease: 'Sine.easeInOut', onUpdate: () => this.drawSky() });
        this.tweens.add({ targets: sun, y: 430, x: FRAME.width * 0.78, duration: rm ? 1 : LAPSE_MS, ease: 'Sine.easeIn' });
        this.tweens.add({ targets: dusk, alpha: 1, duration: rm ? 1 : LAPSE_MS * 0.8, delay: rm ? 0 : LAPSE_MS * 0.2 });
        this.time.delayedCall(rm ? 400 : LAPSE_MS + 400, () => this.cutOnRoof());
    }

    /** The grid goes: a flicker, then the neighbourhood is dark. The hub's skylight and lamp stay on. */
    private cutOnRoof() {
        const r = this.roof!;
        this.prompt.show(this.prompts().cut);
        this.events.emit('sfx', 'power_cut');
        const go = () => { r.night.setAlpha(1); this.skyT.night = 1; this.drawSky(); };
        if (this.state.reducedMotion) go();
        else {
            this.tweens.add({ targets: r.night, alpha: { from: 1, to: 0 }, duration: 70, yoyo: true, repeat: 1, onComplete: go });
        }
        this.time.delayedCall(900, () => {
            this.phase = 'solar';
            this.prompt.show(this.prompts().solar);
            const a = this.roofAnchor('inverter');
            const card = labelCard(this, a.x, a.y - 90, this.p.solar_label, { size: 26 });
            r.box.add(card);
            this.time.delayedCall(this.state.reducedMotion ? 900 : 2200, () => this.diveIn());
        });
    }

    /** Through the skylight and back down to the chambers, now in the power cut. */
    private diveIn() {
        const r = this.roof!;
        const k = this.roofAnchor('skylight');
        const s = 3.2;
        const back = () => {
            this.flow = false;
            r.box.destroy();
            this.roof = undefined;
            this.labels.forEach((l) => l.setVisible(true));
            this.ruleCard.setVisible(true);
            this.nightLayers.forEach((l) => l.setAlpha(1));
            this.riyaz.setAlpha(0);
            this.cameras.main.fadeIn(this.state.reducedMotion ? 1 : 500, 28, 23, 20);
            this.toLeave();
        };
        if (this.state.reducedMotion) return back();
        this.tweens.add({ targets: r.box, scale: s, x: k.x * (1 - s), y: k.y * (1 - s), duration: 1100, ease: 'Cubic.easeIn' });
        this.time.delayedCall(800, () => {
            this.cameras.main.fadeOut(300, 28, 23, 20);
            this.cameras.main.once('camerafadeoutcomplete', back);
        });
    }

    /** No roof layers (e.g. not yet packed): the old in-place power cut. */
    private powerCutHere() {
        this.prompt.show(this.prompts().cut);
        this.tweens.add({ targets: this.nightLayers, alpha: 1, duration: this.state.reducedMotion ? 1 : motion.transition });
        this.time.delayedCall(1200, () => {
            this.phase = 'solar';
            this.prompt.show(this.prompts().solar);
            this.time.delayedCall(1600, () => this.toLeave());
        });
    }

    private roofAnchor(name: string) {
        const [x, y] = this.roof!.layers.anchors[name];
        return { x, y };
    }

    private drawSky() {
        const r = this.roof;
        if (!r) return;
        const mix = (a: number, b: number, t: number) => Display.Color.Interpolate.ColorWithColor(
            Display.Color.ValueToColor(a), Display.Color.ValueToColor(b), 100, Math.round(t * 100));
        const pick = (i: 0 | 1) => {
            const c1 = mix(SKY.day[i], SKY.dusk[i], this.skyT.dusk);
            const v1 = Display.Color.GetColor(c1.r, c1.g, c1.b);
            const c2 = mix(v1, SKY.night[i], this.skyT.night);
            return Display.Color.GetColor(c2.r, c2.g, c2.b);
        };
        const top = pick(0), bottom = pick(1);
        r.sky.clear().fillGradientStyle(top, top, bottom, bottom, 1).fillRect(0, 0, FRAME.width, FRAME.height);
        r.sun.setVisible(this.skyT.night < 0.5);
    }

    /** Energy running from the panels to the inverter and down to the skylight: moving dashes. */
    private drawEnergy(time: number) {
        const r = this.roof;
        if (!r) return;
        const panels = [0, 1, 2, 3, 4, 5].map((i) => this.roofAnchor(`panel_${i}`));
        const inv = this.roofAnchor('inverter'), sky = this.roofAnchor('skylight');
        const g = r.energy.clear();
        const dash = (a: { x: number; y: number }, b: { x: number; y: number }, alpha: number) => {
            const len = Math.hypot(b.x - a.x, b.y - a.y), n = Math.floor(len / 22);
            for (let i = 0; i < n; i++) {
                const t = ((i + (time / 140) % 1) / n);
                g.fillStyle(0xfff3d6, alpha).fillCircle(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, 3);
            }
        };
        const sun = r.night.alpha < 0.5 ? 0.9 : 0.25;                      // after dark the battery feeds the chambers
        panels.forEach((p) => dash(p, inv, sun));
        dash(inv, sky, 0.9);
    }

    private toLeave() {
        this.phase = 'leave';
        this.ring?.destroy();
        this.prompt.show(this.prompts().leave, '→');
    }
}
