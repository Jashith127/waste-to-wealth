// Station 5 · Bulk pickup (Run 2), code-only grey box (task 05; Blender set comes with task 16).
// Tap or Space loads the next crate into the authorised collector's truck; ours goes last and its docked
// tag bounces. From here the camera follows the crate: Riyaz is not in the scene.
import type { GameObjects } from 'phaser';
import { FRAME, motion } from '../../theme';
import { GreyBox, labelCard, paidTag, type V3 } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'load' | 'leave';

const TARGET: V3 = [0, 2.4, 0.5];
const CRATE: V3 = [0.55, 0.36, 0.3];
const BAY_TOP = 0.9;
const STACKS = [-3.0, -2.3];                 // crate i sits in stack i % 2, level floor(i / 2): crate 0 bottom of the back stack
const TRUCK_REAR: V3 = [1.15, 1.6, 1.5];     // where a loaded crate disappears into the cargo box

export default class Station05 extends StationScene {
    private phase: Phase = 'load';
    private crates: GameObjects.Graphics[] = [];
    private loaded = 0;
    private busy = false;
    private truck: GameObjects.Graphics[] = [];
    private tag!: KiloTag;
    private gb!: GreyBox;

    constructor() {
        super('s05');
    }

    protected build() {
        this.phase = 'load';
        this.loaded = 0;
        this.busy = false;
        this.crates = [];
        const p = this.stationData.params as { crates_to_load: number; truck_label: string; one_for_many: string };
        const gb = (this.gb = new GreyBox(this, TARGET));
        this.world.add([
            gb.plinth(-5, 7),
            gb.box([-5, 3.0, 0], [1.0, 3.25, 3.4]),                         // the hub's side wall
            gb.box([-4.2, 1.6, 0], [0.6, 3.0, BAY_TOP], { top: 0xa39d95 }), // loading bay at kerb height
        ]);
        this.truck = [
            gb.box([1.0, 0.7, 0.45], [4.6, 2.5, 2.7], { top: 0xc4bfb7, front: 0xaaa59d, side: 0x7d7973 }),   // cargo box, no marks
            gb.box([4.6, 0.9, 0.45], [5.7, 2.3, 2.3], { top: 0xc4bfb7, front: 0xaaa59d, side: 0x7d7973 }),   // cab
            gb.box([4.75, 0.88, 1.5], [5.6, 0.9, 2.15], { front: 0x3a3836, side: 0x3a3836, top: 0x3a3836 }), // windscreen
        ];
        for (const x of [1.6, 4.0, 5.2]) {                                                                    // wheels
            this.truck.push(gb.box([x - 0.35, 0.6, 0], [x + 0.35, 0.72, 0.6], { front: 0x2a2624, side: 0x2a2624, top: 0x2a2624 }));
        }
        this.world.add(this.truck);

        const count = p.crates_to_load;
        const order = Array.from({ length: count }, (_, i) => i).sort((a, b) => (a % 2) - (b % 2) || a - b);   // back stack first
        for (const i of order) {
            const x = STACKS[i % 2], z = BAY_TOP + Math.floor(i / 2) * CRATE[2];
            this.crates[i] = gb.box([x - CRATE[0] / 2, 2.1, z], [x + CRATE[0] / 2, 2.1 + CRATE[1], z + CRATE[2]]);
            this.world.add(this.crates[i]);
        }

        const bay = gb.point([3.0, 1.6, 2.9]);
        this.world.add(labelCard(this, bay.x, bay.y - 40, p.truck_label, { proposed: true, size: 28 }));
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
        // load from the tops of the stacks down, so crate 0 (ours, bottom of the back stack) goes last
        const next = this.crates.length - 1 - this.loaded;
        const crate = this.crates[next];
        const end = this.gb.point(TRUCK_REAR);
        const start = { x: crate.x, y: crate.y };
        this.busy = true;
        crate.setDepth(20);
        const arc = { t: 0 };
        this.tweens.add({
            targets: arc, t: 1, duration: this.state.reducedMotion ? 1 : 300, ease: 'Sine.easeInOut',
            onUpdate: () => crate.setPosition(start.x + (end.x - start.x) * arc.t, start.y + (end.y - start.y) * arc.t - Math.sin(Math.PI * arc.t) * 120),
            onComplete: () => {
                crate.setVisible(false);
                this.busy = false;
                this.loaded++;
                if (next === 0) this.ourCrateLoaded();
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

    /** The truck slides off right, then the walk-out transition follows it. */
    private driveOff() {
        if (this.busy) return;
        this.busy = true;
        if (this.state.reducedMotion) return this.leave();
        this.tweens.add({ targets: this.truck, x: `+=${FRAME.width}`, duration: 900, ease: 'Sine.easeIn' });
        this.time.delayedCall(motion.normal * 2, () => this.leave());
    }
}
