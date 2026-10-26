// Station 6 · Renderer (example), Run 2: the kilo becomes a product. The same kilo sits on a belt
// along the front of the plant in five forms (crate of bone and offal → crushed → cooked → pressed
// cake and oil → meal); each Space runs it through the next machine, and the last press bags it as
// meat and bone meal, with the oil in a drum. The forms are in-place layers from
// art/scripts/s06_build.py, swapped one for the next. A strip of stage chips and an enlarged inset
// of the current form keep the conversion readable. "Renderer (example)" and "Typical process" stay
// on screen throughout (truth rules). Off-site cards are blue.
import type { GameObjects } from 'phaser';
import { colour, css, font, FRAME, layout, motion } from '../../theme';
import { drawCard } from '../../ui/card';
import { labelCard, paidTag } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'convert' | 'leave';
interface Stage { chip: string; caption: string }
interface Params { process_label: string; stages: Stage[]; product: { chip: string; meal: string; oil: string; uses: string }; inset_label: string }

const INSET = { x: 1520, y: 200, w: 350, h: 300 };       // under the docked tag, over the empty back wall
const BUSY_MS = 700;                                     // one machine's run; a press during it is queued

export default class Station06 extends StationScene {
    private phase: Phase = 'convert';
    private stage = 0;
    private forms: GameObjects.Image[] = [];
    private product!: GameObjects.Image;
    private chips: GameObjects.Container[] = [];
    private inset?: GameObjects.Container;
    private ring?: GameObjects.Arc;
    private busy = false;
    private queued = false;
    private p!: Params;

    constructor() {
        super('s06');
    }

    preload() {
        this.loadLayers();
    }

    protected build() {
        this.phase = 'convert';
        this.stage = 0;
        this.busy = this.queued = false;
        this.p = this.stationData.params as unknown as Params;
        this.layer('bg');
        this.forms = this.p.stages.map((_, i) => this.layer(`form_${i}`).setAlpha(i === 0 ? 1 : 0));
        this.product = this.layer('product').setAlpha(0);

        const head = labelCard(this, 0, 0, `${this.stationData.label} · ${this.p.process_label}`, { band: colour.offsite, size: 28 });
        head.setPosition(layout.prompt.x + head.getBounds().width / 2, 150);
        this.chipStrip(layout.prompt.x, 224);
        new KiloTag(this, FRAME.width - 260, 20, paidTag(this), this.state.reducedMotion).setDepth(30);

        const kb = this.input.keyboard!;
        kb.on('keydown-SPACE', () => this.press());
        kb.on('keydown-ENTER', () => this.press());
        kb.on('keydown-RIGHT', () => this.phase === 'leave' && this.leave());
        this.input.on('pointerup', () => this.press());
        this.prompt.show(this.prompts().start, 'Space');
        this.showStage();
    }

    private press() {
        if (this.phase === 'leave') return this.leave();
        if (this.busy) { this.queued = true; return; }
        this.run();
    }

    // --- the conversion --------------------------------------------------------------------------

    /** Run the kilo through the next machine: the current form goes in, the machine works, the next
     * form comes out on the belt below it. After the last machine, the product. */
    private run() {
        const from = this.forms[this.stage];
        const last = this.stage === this.forms.length - 1;
        this.busy = true;
        this.ring?.destroy();
        const ms = this.state.reducedMotion ? 1 : BUSY_MS;
        this.tweens.add({ targets: from, alpha: 0, duration: ms / 2 });
        this.events.emit('sfx', `renderer_step_${this.stage + 1}`);
        this.machineWorks(last ? 'product' : `form_${this.stage + 1}`, this.stage + 1);
        this.time.delayedCall(ms, () => {
            this.stage++;
            if (last) return this.reveal();
            const to = this.forms[this.stage];
            if (this.state.reducedMotion) to.setAlpha(1);
            else this.tweens.add({ targets: to, alpha: { from: 0, to: 1 }, y: { from: to.y - 24, to: to.y }, duration: 320, ease: 'Back.easeOut' });
            this.prompt.show(this.prompts().next, 'Space');
            this.showStage();
            this.busy = false;
            if (this.queued) { this.queued = false; this.time.delayedCall(240, () => this.press()); }
        });
    }

    /** The chips, the inset (with the stage's caption) and the hint ring for the current stage. */
    private showStage() {
        const s = this.p.stages[this.stage];
        const at = this.anchor(`form_${this.stage}`);
        this.ring = this.hint(at.x, at.y + 30, 96);
        this.markChips(this.stage);
        this.showInset(`s06_form_${this.stage}`, s.chip, s.caption);
    }

    /** The product: sacks of meal on the pallet and the oil drum; then on to where it is used. */
    private reveal() {
        this.busy = false;
        this.phase = 'leave';
        this.markChips(this.p.stages.length);
        const pr = this.p.product;
        if (this.state.reducedMotion) this.product.setAlpha(1);
        else this.tweens.add({ targets: this.product, alpha: { from: 0, to: 1 }, y: { from: this.product.y - 30, to: this.product.y }, duration: 420, ease: 'Back.easeOut' });
        const meal = this.anchor('product_meal');
        const oil = this.anchor('product_oil');
        labelCard(this, meal.x - 60, meal.y - 130, pr.meal, { band: colour.income, size: 30 });
        labelCard(this, oil.x + 40, oil.y - 120, pr.oil, { band: colour.pay, size: 28 });
        this.showInset('s06_product', pr.chip, pr.uses);
        this.prompt.show(this.prompts().leave, '→');
    }

    /** A puff at the machine that is working: crushed bits, steam, oil drips or meal dust. */
    private machineWorks(_into: string, stage: number) {
        if (this.state.reducedMotion) return;
        const m = this.anchor(`machine_${Math.min(stage, this.p.stages.length - 1)}`);
        const kind = ['', 'bits', 'steam', 'oil', 'dust', 'dust'][stage] ?? 'dust';
        const tint = { bits: 0xa2584c, steam: 0xf4ecde, oil: 0xd9a23a, dust: 0xc9b48e }[kind] ?? 0xc9b48e;
        for (let i = 0; i < 10; i++) {
            const dot = this.add.circle(m.x + (Math.random() - 0.5) * 60, m.y + (Math.random() - 0.5) * 20, kind === 'steam' ? 10 : 4, tint, 0.85).setDepth(26);
            const rise = kind === 'oil' ? 60 : kind === 'bits' ? 30 : -90;
            this.tweens.add({
                targets: dot, y: dot.y + rise + Math.random() * 20, x: dot.x + (Math.random() - 0.5) * 40,
                alpha: 0, scale: kind === 'steam' ? 2.2 : 1, delay: i * 40, duration: 600, ease: 'Sine.easeOut',
                onComplete: () => dot.destroy(),
            });
        }
    }

    // --- UI: the stage strip and the inset -------------------------------------------------------

    /** Bone & offal → Crushed → Cooked → Pressed → Meal → Product, as small chips under the header. */
    private chipStrip(x: number, y: number) {
        const names = [...this.p.stages.map((s) => s.chip), this.p.product.chip];
        this.chips = [];
        names.forEach((name, i) => {
            const t = this.add.text(0, 0, name, { fontFamily: font.display, fontSize: 22, fontStyle: '700', color: css.ink }).setOrigin(0.5);
            const w = t.width + 28;
            const g = this.add.graphics();
            const c = this.add.container(x + w / 2, y, [g, t]).setDepth(35).setSize(w, 40);
            c.setData({ g, t, w });
            this.chips.push(c);
            x += w + 10;
            if (i < names.length - 1) {
                this.add.text(x + 2, y, '→', { fontFamily: font.display, fontSize: 24, fontStyle: '700', color: css.cream }).setOrigin(0, 0.5).setDepth(35);
                x += 32;
            }
        });
    }

    private markChips(current: number) {
        this.chips.forEach((c, i) => {
            const g = c.getData('g') as GameObjects.Graphics, t = c.getData('t') as GameObjects.Text, w = c.getData('w') as number;
            const fill = i === current ? colour.offsite : i < current ? colour.cream : colour.card;
            g.clear().fillStyle(fill, i > current ? 0.75 : 1).fillRoundedRect(-w / 2, -20, w, 40, 10);
            g.lineStyle(2, colour.ink, i > current ? 0.4 : 1).strokeRoundedRect(-w / 2, -20, w, 40, 10);
            t.setColor(i === current ? css.cream : i < current ? css.muted : css.ink);
        });
    }

    /** The current form, enlarged, in a card at the top right: what the kilo looks like now. */
    private showInset(key: string, title: string, sub?: string) {
        this.inset?.destroy();
        const { x, y, w, h } = INSET;
        const g = this.add.graphics();
        drawCard(g, 0, 0, w, h, colour.offsite);
        const head = this.add.text(20, 24, `${this.p.inset_label}: ${title}`, { fontFamily: font.display, fontSize: 26, fontStyle: '700', color: css.ink });
        const img = this.add.image(w / 2, 62 + (h - 150) / 2, key);
        img.setScale(Math.min((w - 40) / img.width, (h - 160) / img.height, 3));
        const parts: GameObjects.GameObject[] = [g, head, img];
        if (sub) parts.push(this.add.text(w / 2, h - 44, sub, { fontFamily: font.body, fontSize: 22, color: css.ink, wordWrap: { width: w - 36 }, align: 'center' }).setOrigin(0.5));
        this.inset = this.add.container(x, y, parts).setDepth(34);
        if (!this.state.reducedMotion) this.tweens.add({ targets: this.inset, alpha: { from: 0, to: 1 }, duration: motion.normal });
    }
}
