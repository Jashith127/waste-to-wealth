// Station 7 · The meal in use, "How it could close" (Run 2). One farm in one frame
// (art/scripts/s07_build.py): the renderer's sacks between a poultry run and two vegetable beds.
// Two presses, two uses, each a before/after pair of in-place layers:
//   feed  meal arcs from the farmer's scoop into the feeder; the hens crowd in and peck
//   soil  meal is scattered on the beds; the thin seedlings become full, fruiting plants
// The label, the Kannur precedent and the caveat stay on screen throughout (truth rules).
import type { GameObjects } from 'phaser';
import { colour, css, font, FRAME, layout, motion } from '../../theme';
import { drawCard } from '../../ui/card';
import { labelCard, paidTag } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'feed' | 'soil' | 'leave';
interface Use { key: 'feed' | 'soil'; caption: string }
interface Params { uses: Use[]; precedent: string; caveat: string }

const MEAL = 0xb89a6e;

export default class Station07 extends StationScene {
    private phase: Phase = 'feed';
    private busy = false;
    private ring?: GameObjects.Arc;
    private l: Record<string, GameObjects.Image> = {};
    private p!: Params;

    constructor() {
        super('s07');
    }

    preload() {
        this.loadLayers();
    }

    protected build() {
        this.phase = 'feed';
        this.busy = false;
        this.p = this.stationData.params as unknown as Params;
        this.layer('bg');
        for (const name of ['feed', 'hens_a', 'hens_b', 'plants_a', 'plants_b']) this.l[name] = this.layer(name);
        this.l.feed.setAlpha(0);
        this.l.hens_b.setAlpha(0);
        this.l.plants_b.setAlpha(0);

        // the label, the precedent and the caveat: fixed on screen, never behind a click
        const label = labelCard(this, 0, 0, this.stationData.label ?? '', { band: colour.brown, size: 30 });
        label.setPosition(layout.prompt.x + label.getBounds().width / 2, 150);
        this.noteCard(layout.prompt.x, 196);
        new KiloTag(this, FRAME.width - 260, 20, paidTag(this), this.state.reducedMotion).setDepth(30);

        const kb = this.input.keyboard!;
        kb.on('keydown-SPACE', () => this.press());
        kb.on('keydown-ENTER', () => this.press());
        kb.on('keydown-RIGHT', () => this.phase === 'leave' && this.leave());
        this.input.on('pointerup', () => this.press());
        this.cue();
    }

    private noteCard(x: number, y: number) {
        const g = this.add.graphics();                       // first, so the text draws over it
        const pre = this.add.text(x + 24, y + 18, this.p.precedent, { fontFamily: font.body, fontSize: 28, color: css.ink });
        const cav = this.add.text(x + 24, y + 56, this.p.caveat, { fontFamily: font.body, fontSize: 28, color: css.muted });
        drawCard(g, x, y, Math.max(pre.width, cav.width) + 48, 104);
        for (const o of [g, pre, cav]) o.setDepth(35);
    }

    /** The prompt and hint ring for the use that is next. */
    private cue() {
        this.ring?.destroy();
        if (this.phase === 'leave') return this.prompt.show(this.prompts().leave, '→');
        const at = this.anchor(this.phase === 'feed' ? 'feeder' : 'beds');
        this.ring = this.hint(at.x, at.y, this.phase === 'feed' ? 120 : 190);
        this.prompt.show(this.prompts()[this.phase], 'Space');
    }

    private press() {
        if (this.busy) return;
        if (this.phase === 'leave') return this.leave();
        this.busy = true;
        this.ring?.destroy();
        const use = this.p.uses.find((u) => u.key === this.phase)!;
        const done = this.phase === 'feed' ? this.feed() : this.soil();
        this.time.delayedCall(done, () => {
            // captions stack on the open ground at the bottom left, clear of the note card, the run and the beds
            const c = labelCard(this, 0, use.key === 'feed' ? 880 : 960, use.caption, { proposed: true, size: 28 });
            c.setX(layout.gutter + c.getBounds().width / 2);
            this.phase = use.key === 'feed' ? 'soil' : 'leave';
            this.busy = false;
            this.cue();
        });
    }

    /** Meal from the scoop into the feeder; the hens come in. Returns when it has settled (ms). */
    private feed() {
        this.events.emit('sfx', 'scatter_feed');
        const from = this.anchor('farmer_hand'), to = this.anchor('feeder');
        const ms = this.state.reducedMotion ? 1 : 700;
        if (!this.state.reducedMotion) this.arc(from, to, 18, 140, 70);
        this.time.delayedCall(ms * 0.6, () => this.fade(this.l.feed, 1));
        this.time.delayedCall(ms, () => this.swap(this.l.hens_a, this.l.hens_b));
        return ms + 500;
    }

    /** Meal scattered over both beds; the plants fill out. */
    private soil() {
        this.events.emit('sfx', 'scatter_feed');
        const from = this.anchor('farmer_hand'), to = this.anchor('beds');
        const ms = this.state.reducedMotion ? 1 : 800;
        if (!this.state.reducedMotion) this.arc(from, to, 30, 420, 160);
        this.time.delayedCall(ms, () => {
            this.swap(this.l.plants_a, this.l.plants_b);
            const b = this.l.plants_b;
            if (!this.state.reducedMotion) this.tweens.add({ targets: b, y: { from: b.y + 14, to: b.y }, duration: 600, ease: 'Back.easeOut' });
        });
        return ms + 700;
    }

    /** n grains of meal thrown from a hand to a spot, spread over w × h. */
    private arc(from: { x: number; y: number }, to: { x: number; y: number }, n: number, w: number, h: number) {
        for (let i = 0; i < n; i++) {
            const grain = this.add.circle(from.x, from.y, 3.5, MEAL, 1).setDepth(26);
            const tx = to.x + (Math.random() - 0.5) * w, ty = to.y + (Math.random() - 0.5) * h * 0.4;
            const k = { t: 0 };
            this.tweens.add({
                targets: k, t: 1, duration: 480 + i * 12, ease: 'Linear',
                onUpdate: () => grain.setPosition(from.x + (tx - from.x) * k.t, from.y + (ty - from.y) * k.t - Math.sin(Math.PI * k.t) * h),
                onComplete: () => grain.destroy(),
            });
        }
    }

    private fade(img: GameObjects.Image, to: number) {
        if (this.state.reducedMotion) img.setAlpha(to);
        else this.tweens.add({ targets: img, alpha: to, duration: motion.normal * 2 });
    }

    private swap(out: GameObjects.Image, into: GameObjects.Image) {
        this.fade(out, 0);
        this.fade(into, 1);
    }
}
