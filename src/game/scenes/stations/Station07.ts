// Station 7 · Farm → back to the stall, "How it could close" (Run 2), code-only grey box (task 07; Blender
// set comes with task 18). The camera pans left to right through three beats, about 1.5 s each, with a
// caption at each. No supply chain back to the stall was found, so the label, the Kannur precedent and
// that caveat stay on screen for the whole station.
import type { GameObjects, Time } from 'phaser';
import { colour, css, font, FRAME, layout, motion } from '../../theme';
import { drawCard } from '../../ui/card';
import { GreyBox, labelCard, paidTag, type V3 } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'watch' | 'leave';
interface Params { beats: { caption: string; anchor: string }[]; precedent: string; caveat: string }

const TARGET: V3 = [0, 2.4, 0.5];
const BEAT_MS = 1500;
// Grey-box anchors in world metres (the Blender set of task 18 keeps these names).
const ANCHORS: Record<string, V3> = { feed: [-3.4, 2.0, 0.6], flock: [-0.6, 1.6, 0.4], stall: [5.6, 2.6, 1.2] };

export default class Station07 extends StationScene {
    private phase: Phase = 'watch';
    private beat = -1;
    private caption?: GameObjects.Container;
    private timer?: Time.TimerEvent;
    private gb!: GreyBox;
    private p!: Params;

    constructor() {
        super('s07');
    }

    protected build() {
        this.phase = 'watch';
        this.beat = -1;
        this.caption = undefined;
        this.p = this.stationData.params as unknown as Params;
        const gb = (this.gb = new GreyBox(this, TARGET));
        this.world.add(gb.plinth(-6, 9));
        // the farm: an open-sided shed with a feeder trough, and a few birds as simple shapes
        for (const x of [-5.2, -3.4, -1.6]) this.world.add(gb.box([x - 0.08, 3.0, 0], [x + 0.08, 3.16, 2.6]));
        this.world.add(gb.box([-5.6, 1.4, 2.6], [-1.2, 3.4, 2.75], { top: 0xa39d95 }));
        this.world.add(gb.box([-4.4, 1.8, 0], [-2.4, 2.2, 0.35]));
        for (const [x, y] of [[-1.2, 1.3], [-0.6, 1.9], [-0.1, 1.4], [0.3, 2.1], [-0.9, 2.4]]) {
            this.world.add(gb.box([x - 0.14, y - 0.1, 0], [x + 0.14, y + 0.1, 0.28], { top: 0xd2ccc3 }));
        }
        // back at Cockburn Road: the stall frontage as a grey block, with its counter
        this.world.add(gb.box([3.0, 3.0, 0], [8.5, 3.25, 4.2]));
        this.world.add(gb.box([4.8, 2.2, 0], [6.6, 2.8, 1.0], { top: 0xc4bfb7 }));

        // the label, the precedent and the caveat: fixed on screen, never behind a click
        const label = labelCard(this, 0, 0, this.stationData.label ?? '', { band: colour.brown, size: 30 });
        label.setPosition(layout.prompt.x + label.getBounds().width / 2, 150).setScrollFactor(0);
        this.noteCard(layout.prompt.x, 196);
        new KiloTag(this, FRAME.width - 260, 20, paidTag(this), this.state.reducedMotion).setDepth(30);

        const kb = this.input.keyboard!;
        kb.on('keydown-SPACE', () => this.advance());
        kb.on('keydown-ENTER', () => this.advance());
        kb.on('keydown-RIGHT', () => this.phase === 'leave' && this.leave());
        this.prompt.show(this.prompts().watch, 'Space');
        this.advance();
    }

    private noteCard(x: number, y: number) {
        const g = this.add.graphics();                       // first, so the text draws over it
        const pre = this.add.text(x + 24, y + 18, this.p.precedent, { fontFamily: font.body, fontSize: 28, color: css.ink });
        const cav = this.add.text(x + 24, y + 56, this.p.caveat, { fontFamily: font.body, fontSize: 28, color: css.muted });
        drawCard(g, x, y, Math.max(pre.width, cav.width) + 48, 104);
        for (const o of [g, pre, cav]) o.setDepth(35);
    }

    /** Pan to the next beat and caption it; after the last, leave for the end card. */
    private advance() {
        if (this.phase === 'leave') return this.leave();
        this.timer?.remove();
        this.beat++;
        this.caption?.destroy();
        if (this.beat >= this.p.beats.length) {
            this.phase = 'leave';
            this.prompt.show(this.prompts().leave, '→');
            return;
        }
        const b = this.p.beats[this.beat];
        const at = this.gb.point(ANCHORS[b.anchor]);
        const worldX = FRAME.width * 0.62 - at.x;              // anchor right of centre, clear of the note card
        if (this.state.reducedMotion) this.world.x = worldX;
        else this.tweens.add({ targets: this.world, x: worldX, duration: motion.transition, ease: 'Sine.easeInOut' });
        this.caption = labelCard(this, at.x, at.y - 90, b.caption, { proposed: true, size: 30 });
        this.world.add(this.caption);
        this.timer = this.time.delayedCall(BEAT_MS, () => this.advance());
    }
}
