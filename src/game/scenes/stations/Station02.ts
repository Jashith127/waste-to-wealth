// Station 2 · The walk, Market street to Russell Market. Hold to walk: the wide plate slides
// under Riyaz. Run 1 ends at the back-lane pile (the −₹5 stays on the tag); Run 2 reaches the
// hub's drop window along a clean pavement.
//
// The set is a 3200×1920 plate at the normal 174.5 px/m (see s02_build.py), and this scene shows
// a 1920×1080 window over it. That is the one camera, just a wider canvas, so the pan never
// slides the diorama off the frame. All anchors are in plate pixels.
import { GameObjects } from 'phaser';
import { station } from '../../content';
import { goNext } from '../../flow';
import { setState } from '../../state';
import { motion } from '../../theme';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'walk' | 'dump' | 'leave';

// Where the back-lane pile should sit on screen when the walk ends. The x pan follows the street
// (street_start → street_end); the y pan is chosen so the pile lands here, above the blueprint line.
const END = { x: 1290, y: 640 };

export default class Station02 extends StationScene {
    private phase: Phase = 'walk';
    private holding = false;
    private t = 0;
    private pan = { x: 0, y: 0 };
    private riyaz!: GameObjects.Image;
    private bag!: GameObjects.Image;
    private base = { riyaz: { x: 0, y: 0 }, bag: { x: 0, y: 0 } };
    private ring?: GameObjects.Arc;
    private arrivedAt = 0;
    private left = false;

    constructor() {
        super('s02');
    }

    preload() {
        this.loadLayers();
    }

    protected build() {
        this.phase = 'walk';
        this.holding = false;
        this.t = 0;
        this.left = false;

        this.layer('bg');
        if (this.state.run === 1) {
            this.layer('litter_shadow');
            this.layer('litter');
        }
        this.layer('anthony_idle');
        this.layer('arif_idle');

        this.riyaz = this.layer('riyaz_walk');
        this.bag = this.layer('kilo');
        this.base.riyaz = { x: this.riyaz.x, y: this.riyaz.y };
        this.base.bag = { x: this.bag.x, y: this.bag.y };

        // The tag hangs from the bag's knot, to the left so it never covers Riyaz or the bag.
        const tagData = this.state.kilo.tag ?? station('s01').kilo!.tag;
        const knot = this.anchor('riyaz_hand');
        new KiloTag(this, knot.x, knot.y, tagData, this.state.reducedMotion, { dx: -150, dy: 14 })
            .setDepth(30);

        // The walk: hold Space, or hold the pointer on the right half.
        const kb = this.input.keyboard!;
        kb.on('keydown-SPACE', () => this.press());
        kb.on('keyup-SPACE', () => { this.holding = false; });
        kb.on('keydown-ENTER', () => this.act());
        kb.on('keydown-RIGHT', () => this.act());
        this.input.on('pointerdown', (p: Phaser.Input.Pointer) => {
            if (this.phase === 'walk' && p.x >= 960) this.holding = true;
        });
        this.input.on('pointerup', () => { this.holding = false; });

        this.prompt.show(this.prompts().walk, 'Hold Space');

        const start = this.anchor('street_start');
        const end = this.anchor('street_end');
        const dump = this.anchor('dump');
        this.pan = { x: start.x - end.x, y: END.y - dump.y };
    }

    /** Hold starts the walk; Space/click later handles the dump and the exit. */
    private press() {
        if (this.phase === 'walk') this.holding = true;
        else this.act();
    }

    private act() {
        if (this.phase === 'dump') this.dump();
        else if (this.phase === 'leave' && this.time.now - this.arrivedAt > 400) this.leave();
    }

    update(_time: number, delta: number) {
        if (this.phase !== 'walk' || !this.holding) return;
        const seconds = (this.stationData.params as { walk_seconds: number }).walk_seconds;
        this.t = Math.min(1, this.t + delta / (seconds * 1000));
        this.applyPan();
        if (this.t >= 1) this.reachEnd();
    }

    /** Slide the plate; Riyaz and the bag counter-shift so he stays near the centre, walking. */
    private applyPan() {
        const wx = this.pan.x * this.t;
        const wy = this.pan.y * this.t;
        this.world.setPosition(wx, wy);
        this.riyaz.setPosition(this.base.riyaz.x - wx, this.base.riyaz.y - wy);
        this.bag.setPosition(this.base.bag.x - wx, this.base.bag.y - wy);
    }

    private reachEnd() {
        this.holding = false;
        this.arrivedAt = this.time.now;
        if (this.state.run !== 1) return this.toLeave();

        this.phase = 'dump';
        this.prompt.show(this.prompts().dump, 'Space');
        const pile = this.pileScreen();
        this.ring = this.hint(pile.x, pile.y, 92);
        this.add.zone(pile.x, pile.y, 300, 220).setInteractive({ useHandCursor: true })
            .on('pointerup', () => this.dump());
    }

    /** Where the dump anchor is on screen once the pan has finished. */
    private pileScreen() {
        const dump = this.anchor('dump');
        return { x: dump.x + this.pan.x, y: dump.y + this.pan.y };
    }

    /** Run 1: the bag leaves Riyaz's hand and lands on the pile; the tag stays −₹5. */
    private dump() {
        if (this.phase !== 'dump') return;
        this.phase = 'leave';
        this.ring?.destroy();
        this.arrivedAt = this.time.now;

        const pile = this.pileScreen();
        const centre = this.anchor('kilo_centre');
        const offset = { x: centre.x - this.base.bag.x, y: centre.y - this.base.bag.y };
        const to = {
            x: pile.x - offset.x - this.world.x,
            y: pile.y - 20 - offset.y - this.world.y,
        };
        if (this.state.reducedMotion) this.bag.setPosition(to.x, to.y);
        else this.tweens.add({ targets: this.bag, ...to, duration: 420, ease: 'Cubic.easeOut' });

        setState(this, { kilo: { carried: false, tag: this.state.kilo.tag } });
        this.toLeave();
    }

    private toLeave() {
        this.phase = 'leave';
        this.prompt.show(this.prompts().leave, 'Space');
        this.makeExit();
    }

    private makeExit() {
        const g = this.add.graphics();
        g.fillStyle(0x1c1714, 0.92).fillRoundedRect(-150, -36, 300, 72, 36);
        const label = this.add.text(0, 0, 'Walk on  →', {
            fontFamily: '"Baloo 2", system-ui, sans-serif', fontSize: 32, fontStyle: '700', color: '#F4ECDE',
        }).setOrigin(0.5);
        const b = this.add.container(1560, 590, [g, label]).setSize(300, 72).setDepth(45).setAlpha(0);
        b.setInteractive({ useHandCursor: true }).on('pointerup', () => this.leave());
        if (this.state.reducedMotion) b.setAlpha(1);
        else this.tweens.add({ targets: b, alpha: 1, x: { from: 1540, to: 1560 }, duration: motion.normal });
    }

    /** The base `leave()` tweens world.x to -260, which would undo the pan. Slide on from here. */
    protected leave() {
        if (this.left) return;
        this.left = true;
        if (!this.state.reducedMotion) {
            this.tweens.add({ targets: this.world, x: this.world.x - 260, duration: motion.transition, ease: 'Sine.easeIn' });
        }
        goNext(this);
    }
}
