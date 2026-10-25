// Station 6 · Renderer (example), Run 2, code-only grey box (task 06; Blender set comes with task 17).
// The material moves through a typical process, one machine every 1.2 s; Space skips ahead. The plant is
// fictional: "Renderer (example)" and "Typical process" stay on screen throughout. Off-site labels are blue.
import type { GameObjects, Time } from 'phaser';
import { colour, FRAME, layout, motion } from '../../theme';
import { GreyBox, labelCard, paidTag, type V3 } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'watch' | 'leave';
interface Params { process_label: string; steps: string[]; outputs: string[] }

const TARGET: V3 = [0.4, 2.4, 1.2];
const STEP_MS = 1200;
const AUTO_LEAVE_MS = 2200;      // untouched, the station ends by itself in under 10 s (task 06)
// One simple machine per step, left to right, as [lo, hi] boxes; the material sits on top of each.
const MACHINES: [V3, V3][][] = [
    [[[-3.6, 1.9, 0], [-2.8, 2.7, 0.9]], [[-3.75, 1.75, 0.9], [-2.65, 2.85, 1.3]]],   // hopper over a shredder
    [[[-2.3, 1.9, 0], [-0.9, 2.7, 1.0]]],                                         // cooker drum
    [[[-0.45, 1.95, 0], [0.25, 2.65, 1.3]], [[-0.55, 1.85, 1.3], [0.35, 2.75, 1.45]]], // press
    [[[0.8, 1.9, 0], [2.2, 2.7, 1.0]]],                                           // dryer drum
    [[[2.7, 1.95, 0], [3.3, 2.65, 1.2]], [[2.8, 2.05, 1.2], [3.2, 2.55, 1.55]]],     // mill
];
const OUTPUTS: [V3, V3][] = [[[3.8, 1.3, 0], [4.4, 1.8, 0.6]], [[3.8, 2.3, 0], [4.4, 2.9, 0.85]]];   // meal sacks, oil drum

export default class Station06 extends StationScene {
    private phase: Phase = 'watch';
    private step = -1;
    private material!: GameObjects.Graphics;
    private stepCard?: GameObjects.Container;
    private timer?: Time.TimerEvent;
    private gb!: GreyBox;
    private p!: Params;

    constructor() {
        super('s06');
    }

    protected build() {
        this.phase = 'watch';
        this.step = -1;
        this.stepCard = undefined;
        this.p = this.stationData.params as unknown as Params;
        const gb = (this.gb = new GreyBox(this, TARGET));
        this.world.add(gb.plinth(-4.5, 5));
        this.world.add(gb.box([-4.5, 3.2, 0], [5, 3.4, 3.0], { front: 0xa8a29a }));      // plant wall
        for (const parts of MACHINES) parts.forEach(([lo, hi]) => this.world.add(gb.box(lo, hi)));
        OUTPUTS.forEach(([lo, hi]) => this.world.add(gb.box(lo, hi)));
        this.material = gb.box([-0.15, -0.15, 0], [0.15, 0.15, 0.2], { top: 0x6e6a65, front: 0x5a5651, side: 0x45423e }).setDepth(25);
        this.material.setPosition(gb.point(this.top(0)).x, gb.point(this.top(0)).y).setVisible(false);

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

    /** World point on top of machine i's highest part. */
    private top(i: number): V3 {
        const [lo, hi] = MACHINES[i][MACHINES[i].length - 1];
        return [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, hi[2]];
    }

    /** Next step (auto every STEP_MS, or Space). After the last machine, the outputs; then leave. */
    private advance() {
        if (this.phase === 'leave') return this.leave();
        this.timer?.remove();
        this.step++;
        this.stepCard?.destroy();
        if (this.step >= this.p.steps.length) return this.showOutputs();
        const to = this.gb.point(this.top(this.step));
        this.material.setVisible(true);
        if (this.step === 0 || this.state.reducedMotion) this.material.setPosition(to.x, to.y);
        else this.tweens.add({ targets: this.material, x: to.x, y: to.y, duration: motion.transition, ease: 'Sine.easeInOut' });
        this.stepCard = labelCard(this, to.x, to.y - 110, this.p.steps[this.step], { band: colour.offsite, size: 30 });
        this.timer = this.time.delayedCall(STEP_MS, () => this.advance());
    }

    private showOutputs() {
        this.material.setVisible(false);
        OUTPUTS.forEach(([lo, hi], i) => {
            const at = this.gb.point([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, hi[2]]);
            labelCard(this, at.x, at.y - 60 - i * 70, this.p.outputs[i], { band: colour.offsite, size: 30 });
        });
        this.phase = 'leave';
        this.prompt.show(this.prompts().leave, '→');
        this.timer = this.time.delayedCall(AUTO_LEAVE_MS, () => this.leave());
    }
}
