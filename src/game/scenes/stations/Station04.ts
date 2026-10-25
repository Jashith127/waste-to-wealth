// Station 4 · Cold room, inside the hub (Run 2). Drag the sealed crate into Chamber B, the unsold
// meat into Chamber A; then the power goes out, the room goes dark, and the chamber windows stay lit
// on solar. Each door carries its word as well as its colour: two doors, never shared.
// Flow after DeepSeek's first pass at task 04; set and layers from art/scripts/s04_build.py.
import type { GameObjects } from 'phaser';
import { colour, css, font, FRAME, motion } from '../../theme';
import { drawCard } from '../../ui/card';
import { labelCard, paidTag } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'waste' | 'meat' | 'cut' | 'solar' | 'leave';
type Key = 'A' | 'B';
interface Chamber { label: string; sub: string; meaning: 'income' | 'offsite' }
interface Params { chambers: Record<Key, Chamber>; rule: string; solar_label: string }
interface Item { img: GameObjects.Image; shadow: GameObjects.Image; centre: { x: number; y: number }; home: { x: number; y: number } }

const SNAP_PX = 140;             // how close to a door's centre a drop counts

export default class Station04 extends StationScene {
    private phase: Phase = 'waste';
    private items!: Record<'crate' | 'tray', Item>;
    private night!: GameObjects.Image[];
    private riyaz!: GameObjects.Image;
    private ruleCard!: GameObjects.Container;
    private ring?: GameObjects.Arc;
    private p!: Params;

    constructor() {
        super('s04');
    }

    preload() {
        this.loadLayers();
    }

    protected build() {
        this.phase = 'waste';
        this.p = this.stationData.params as unknown as Params;
        this.layer('bg');
        this.layer('fx_chamber_light');
        this.night = [this.layer('bg_night').setAlpha(0), this.layer('fx_chamber_light_night').setAlpha(0)];
        this.riyaz = this.layer('riyaz_idle');
        this.items = { crate: this.item('crate'), tray: this.item('meat_tray') };

        for (const key of ['A', 'B'] as const) this.doorLabel(key);
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
        const c = this.add.container(at.x, at.y).setDepth(35);
        const title = this.add.text(0, -14, ch.label, { fontFamily: font.display, fontSize: 30, fontStyle: '700', color: css[ch.meaning] }).setOrigin(0.5);
        const sub = this.add.text(0, 20, ch.sub, { fontFamily: font.body, fontSize: 21, color: css.muted }).setOrigin(0.5);
        const w = Math.max(title.width, sub.width) + 36, h = 90;
        const g = this.add.graphics();
        drawCard(g, -w / 2, -h / 2 - 4, w, h, colour[ch.meaning]);
        c.add([g, title, sub]);
    }

    private rule() {
        // between the doors, low: clear of both windows, which are the cue when the power goes
        const at = this.anchor('rule');
        return labelCard(this, at.x, at.y + 170, this.p.rule, { size: 24 });
    }

    private press() {
        if (this.phase === 'waste') this.accept(this.items.crate, 'B');
        else if (this.phase === 'meat') this.accept(this.items.tray, 'A');
        else if (this.phase === 'solar') this.toLeave();
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

    /** Through its door: the item goes in and the next beat starts. */
    private accept(it: Item, key: Key) {
        const wasWaste = this.phase === 'waste';
        this.phase = wasWaste ? 'meat' : 'cut';
        it.img.disableInteractive();
        const d = this.anchor(`door_${key.toLowerCase()}`);
        it.shadow.setVisible(false);
        if (this.state.reducedMotion) it.img.setVisible(false);
        else this.tweens.add({ targets: it.img, x: d.x - it.centre.x, y: d.y - it.centre.y, alpha: 0, duration: 420, ease: 'Cubic.easeIn' });
        this.focus();
        if (wasWaste) return this.prompt.show(this.prompts().meat, 'Space');
        this.prompt.show(this.prompts().cut);
        this.time.delayedCall(this.state.reducedMotion ? 350 : 700, () => this.powerCut());
    }

    /** Wrong door: the item springs back and the rule says why. */
    private refuse() {
        if (!this.state.reducedMotion) this.tweens.add({ targets: this.ruleCard, scale: { from: 1.12, to: 1 }, duration: 320, ease: 'Sine.easeOut' });
    }

    /** The practicals go out: the room drops to the power-cut render; the chamber windows stay lit. */
    private powerCut() {
        const ms = this.state.reducedMotion ? 1 : motion.transition;
        this.tweens.add({ targets: this.night, alpha: 1, duration: ms, ease: 'Sine.easeInOut' });
        this.tweens.addCounter({ from: 255, to: 110, duration: ms, onUpdate: (t) => { const v = Math.round(t.getValue() ?? 255); this.riyaz.setTint((v << 16) | (v << 8) | v); } });
        this.time.delayedCall(ms + 500, () => this.solar());
    }

    private solar() {
        this.phase = 'solar';
        this.prompt.show(this.prompts().solar, 'Space');
        const at = this.anchor('solar');
        labelCard(this, at.x, at.y - 95, this.p.solar_label, { size: 26 });
        this.ring = this.hint(at.x, at.y, 70);
        this.time.delayedCall(this.state.reducedMotion ? 900 : 1800, () => this.toLeave());
    }

    private toLeave() {
        if (this.phase === 'leave') return;
        this.phase = 'leave';
        this.ring?.destroy();
        this.prompt.show(this.prompts().leave, '→');
    }
}
