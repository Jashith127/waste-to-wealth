// Station 6 · Renderer (example), Run 2. The material moves through a typical process, one machine
// every 1.2 s; Space skips ahead. The plant is fictional: "Renderer (example)" and "Typical process"
// stay on screen throughout. Off-site labels are blue. Set and layers from art/scripts/s06_build.py.
import type { GameObjects, Time } from 'phaser';
import { colour, css, font, FRAME, layout, motion } from '../../theme';
import { drawCard } from '../../ui/card';
import { labelCard, paidTag } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'watch' | 'leave';
interface Params { process_label: string; steps: string[]; outputs: string[]; tend: { step: number; label: string; hold_ms: number; give_up_ms: number } }

const STEP_MS = 1200;
const AUTO_LEAVE_MS = 2200;      // untouched, the station ends by itself in under 10 s (task 06)

export default class Station06 extends StationScene {
    private phase: Phase = 'watch';
    private step = -1;
    private material!: GameObjects.Image;
    private offset = { x: 0, y: 0 };
    private stepCard?: GameObjects.Container;
    private timer?: Time.TimerEvent;
    private p!: Params;

    constructor() {
        super('s06');
    }

    preload() {
        this.loadLayers();
    }

    protected build() {
        this.phase = 'watch';
        this.step = -1;
        this.stepCard = undefined;
        this.p = this.stationData.params as unknown as Params;
        this.layer('bg');
        this.material = this.layer('material').setVisible(false).setDepth(25);
        const c = this.anchor('material_centre');
        this.offset = { x: c.x - this.material.x, y: c.y - this.material.y };

        // "Renderer (example)" and "Typical process" stay up for the whole station
        const card = labelCard(this, 0, 0, `${this.stationData.label} · ${this.p.process_label}`, { band: colour.offsite, size: 28 });
        card.setPosition(layout.prompt.x + card.getBounds().width / 2, 150);
        new KiloTag(this, FRAME.width - 260, 20, paidTag(this), this.state.reducedMotion).setDepth(30);

        const kb = this.input.keyboard!;
        kb.on('keydown-SPACE', () => this.advance());
        kb.on('keydown-ENTER', () => this.advance());
        kb.on('keydown-RIGHT', () => this.phase === 'leave' && this.leave());
        this.prompt.show(this.prompts().watch, 'Space');
        this.advance();
    }

    /** Put the heap's centre on a screen point. */
    private place(at: { x: number; y: number }, tween: boolean) {
        const to = { x: at.x - this.offset.x, y: at.y - this.offset.y };
        if (!tween || this.state.reducedMotion) this.material.setPosition(to.x, to.y);
        else this.tweens.add({ targets: this.material, ...to, duration: motion.transition, ease: 'Sine.easeInOut' });
    }

    /** Next step (auto every STEP_MS, or Space). After the last machine, the outputs; then leave. */
    private advance() {
        if (this.gauge) return this.nudge();
        if (this.phase === 'leave') return this.leave();
        this.timer?.remove();
        this.step++;
        this.stepCard?.destroy();
        if (this.step >= this.p.steps.length) return this.showOutputs();
        const at = this.anchor(`step_${this.step}`);
        this.material.setVisible(true);
        this.place(at, this.step > 0);
        this.events.emit('sfx', `renderer_step_${this.step}`);
        this.stepCard = labelCard(this, at.x, at.y - 120, this.p.steps[this.step], { band: colour.offsite, size: 30 });
        if (this.step === this.p.tend.step && !this.state.reducedMotion) return this.startTending(at);
        this.timer = this.time.delayedCall(STEP_MS, () => this.advance());
    }

    // --- keep the line running (mini-game) -------------------------------------------------------

    private gauge?: { box: GameObjects.Container; g: GameObjects.Graphics; x: number; v: number; held: number; spent: number };

    /** A gauge over the cooker: the needle drifts; Space nudges it back. Two seconds in the band
     * and the line moves on (it moves on anyway after a while: nobody gets stuck). No numbers. */
    private startTending(at: { x: number; y: number }) {
        const box = this.add.container(at.x + 360, at.y - 40).setDepth(40);   // right of the cooker: the label stays clear
        const g = this.add.graphics();
        const card = this.add.graphics();
        drawCard(card, -190, -60, 380, 120, colour.offsite);
        box.add([card, g, this.add.text(0, -26, this.p.tend.label, { fontFamily: font.display, fontSize: 26, fontStyle: '700', color: css.ink }).setOrigin(0.5)]);
        this.gauge = { box, g, x: 0.15, v: 0.35, held: 0, spent: 0 };
        this.prompt.show(this.prompts().tend, 'Space');
    }

    update(_t: number, delta: number) {
        const gg = this.gauge;
        if (!gg) return;
        const dt = delta / 1000;
        gg.x = Math.min(1, Math.max(0, gg.x + gg.v * dt));
        if (gg.x >= 1 || gg.x <= 0) gg.v = -gg.v;
        const inBand = gg.x > 0.4 && gg.x < 0.6;
        if (inBand) gg.held += delta;
        gg.spent += delta;
        const w = 300, x0 = -150, y = 18;
        gg.g.clear();
        gg.g.fillStyle(colour.ink, 0.15).fillRoundedRect(x0, y - 9, w, 18, 9);
        gg.g.fillStyle(colour.cream, 1).fillRect(x0 + w * 0.4, y - 9, w * 0.2, 18);
        gg.g.lineStyle(2, colour.ink, 0.6).strokeRoundedRect(x0 + w * 0.4, y - 9, w * 0.2, 18, 3);
        gg.g.fillStyle(colour.ink, 1).fillTriangle(x0 + w * gg.x, y + 12, x0 + w * gg.x - 9, y + 26, x0 + w * gg.x + 9, y + 26);
        gg.g.fillStyle(colour.offsite, 1).fillRect(x0, y + 32, w * Math.min(1, gg.held / this.p.tend.hold_ms), 4);
        if (gg.held >= this.p.tend.hold_ms || gg.spent >= this.p.tend.give_up_ms) {
            gg.box.destroy();
            this.gauge = undefined;
            this.prompt.show(this.prompts().watch, 'Space');
            this.timer = this.time.delayedCall(400, () => this.advance());
        }
    }

    /** Space while tending: push the needle back toward the band, and it drifts the other way. */
    private nudge() {
        const gg = this.gauge!;
        gg.x += (0.5 - gg.x) * 0.6;
        gg.v = (Math.random() < 0.5 ? -1 : 1) * (0.25 + Math.random() * 0.25);
        this.events.emit('sfx', 'valve');
    }

    private showOutputs() {
        this.material.setVisible(false);
        (['out_meal', 'out_oil'] as const).forEach((name, i) => {
            const at = this.anchor(name);
            labelCard(this, at.x, at.y - 80, this.p.outputs[i], { band: colour.offsite, size: 30 });
        });
        this.phase = 'leave';
        this.prompt.show(this.prompts().leave, '→');
        this.timer = this.time.delayedCall(AUTO_LEAVE_MS, () => this.leave());
    }
}
