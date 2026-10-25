// Station 6 · Renderer (example), Run 2. The material moves through a typical process, one machine
// every 1.2 s; Space skips ahead. The plant is fictional: "Renderer (example)" and "Typical process"
// stay on screen throughout. Off-site labels are blue. Set and layers from art/scripts/s06_build.py.
import type { GameObjects, Time } from 'phaser';
import { colour, FRAME, layout, motion } from '../../theme';
import { labelCard, paidTag } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'watch' | 'leave';
interface Params { process_label: string; steps: string[]; outputs: string[] }

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
        this.timer = this.time.delayedCall(STEP_MS, () => this.advance());
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
