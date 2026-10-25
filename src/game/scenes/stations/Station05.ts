// Station 5 · Bulk pickup (Run 2). Tap or Space loads the next sealed crate into the authorised
// collector's truck; ours goes last and its docked tag bounces. From here the camera follows the
// crate: Riyaz is not in the scene. Set and layers from art/scripts/s05_build.py.
import type { GameObjects } from 'phaser';
import { FRAME, motion } from '../../theme';
import { labelCard, paidTag } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'load' | 'leave';
const COUNT = 6;

export default class Station05 extends StationScene {
    private phase: Phase = 'load';
    private crates: GameObjects.Image[] = [];
    private loaded = 0;
    private busy = false;
    private truck!: GameObjects.Image;
    private label!: GameObjects.Container;
    private tag!: KiloTag;

    constructor() {
        super('s05');
    }

    preload() {
        this.loadLayers();
    }

    protected build() {
        this.phase = 'load';
        this.loaded = 0;
        this.busy = false;
        const p = this.stationData.params as { truck_label: string; one_for_many: string };
        this.layer('bg');
        this.truck = this.layer('truck');
        // back stack first, bottom up, so nearer and higher crates draw over the ones behind them
        const order = [0, 2, 4, 1, 3, 5];
        this.crates = [];
        for (const i of order) this.crates[i] = this.layer(`crate_${i}`);

        const bay = this.anchor('truck_bay');
        this.label = labelCard(this, bay.x, bay.y - 30, p.truck_label, { proposed: true, size: 28 });
        this.tag = new KiloTag(this, FRAME.width - 260, 20, paidTag(this), this.state.reducedMotion).setDepth(30);

        const kb = this.input.keyboard!;
        kb.on('keydown-SPACE', () => this.act());
        kb.on('keydown-ENTER', () => this.act());
        kb.on('keydown-RIGHT', () => this.phase === 'leave' && this.driveOff());
        this.input.on('pointerup', (_p: unknown, over: GameObjects.GameObject[]) => over.length === 0 && this.act());
        this.prompt.show(this.prompts().load, 'Space');
    }

    private act() {
        if (this.phase === 'leave') return this.driveOff();
        if (this.busy) return;
        // from the tops of the stacks down, so crate 0 (ours, bottom of the back stack) goes last
        const next = [5, 4, 3, 2, 1, 0][this.loaded];
        const crate = this.crates[next];
        const c = this.anchor(`crate_${next}_centre`), rear = this.anchor('truck_rear');
        const start = { x: crate.x, y: crate.y };
        const end = { x: crate.x + rear.x - c.x, y: crate.y + rear.y - c.y };
        this.busy = true;
        crate.setDepth(20);
        this.events.emit('sfx', 'crate_load');
        const arc = { t: 0 };
        this.tweens.add({
            targets: arc, t: 1, duration: this.state.reducedMotion ? 1 : 340, ease: 'Sine.easeInOut',
            onUpdate: () => crate.setPosition(start.x + (end.x - start.x) * arc.t, start.y + (end.y - start.y) * arc.t - Math.sin(Math.PI * arc.t) * 130),
            onComplete: () => {
                crate.setVisible(false);
                this.busy = false;
                if (!this.state.reducedMotion) this.tweens.add({ targets: this.truck, y: this.truck.y + 3, duration: 90, yoyo: true });
                if (++this.loaded === COUNT) this.ourCrateLoaded();
            },
        });
    }

    private ourCrateLoaded() {
        if (!this.state.reducedMotion) this.tweens.add({ targets: this.tag, y: this.tag.y + 10, duration: 140, yoyo: true, repeat: 1, ease: 'Sine.easeOut' });
        const p = this.stationData.params as { one_for_many: string };
        labelCard(this, FRAME.width / 2, 190, p.one_for_many, { proposed: true, size: 34 });
        this.phase = 'leave';
        this.prompt.show(this.prompts().leave, '→');
    }

    /** The truck pulls off right with its label, then the walk-out transition follows it. */
    private driveOff() {
        if (this.busy) return;
        this.busy = true;
        if (this.state.reducedMotion) return this.leave();
        this.events.emit('sfx', 'truck');
        this.tweens.add({ targets: [this.truck, this.label], x: `+=${FRAME.width}`, y: `+=${FRAME.width / 2}`, duration: 1100, ease: 'Sine.easeIn' });
        this.time.delayedCall(motion.normal * 2, () => this.leave());
    }
}
