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
const FRAME_MS = 140;                      // one walk frame: right foot, pass, left foot, pass
const CART_FROM = 0.36;                    // walk progress at which the handcart sets off
const CART_MS = 2400;                      // its trip from the shopfront to the kerb
const CART_LANE = [0.05, 0.45];            // the part of that trip where it blocks Riyaz's line
const CART_ZONE = [0.42, 0.62];            // walk progress where Riyaz would walk into it
const M_PX = { x: 123.4, y: 61.7 };        // one world metre along +Y, on screen (2:1 dimetric)

interface Fly { dot: GameObjects.Arc; phase: number; r: number; speed: number; home: { x: number; y: number } }

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
    private frames: GameObjects.Image[] = [];
    private walkMs = 0;
    private cart?: { img: GameObjects.Image; shadow: GameObjects.Image; home: { x: number; y: number }; off: { x: number; y: number }; k: number };
    private bumped = 0;
    private pileFlies: Fly[] = [];
    private bagFlies: Fly[] = [];

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

        // the handcart (mini-game): it rolls out from the shopfront mid-walk; let it pass
        const cartShadow = this.layer('cart_shadow'), cartImg = this.layer('cart');
        this.cart = {
            img: cartImg, shadow: cartShadow, home: { x: cartImg.x, y: cartImg.y },
            off: { x: cartShadow.x - cartImg.x, y: cartShadow.y - cartImg.y }, k: -1,
        };
        this.placeCart(0);

        this.frames = [this.layer('riyaz_walk_a'), this.layer('riyaz_walk'), this.layer('riyaz_walk_b')];
        this.riyaz = this.frames[1];
        this.bag = this.layer('kilo');
        this.base.riyaz = { x: this.riyaz.x, y: this.riyaz.y };
        this.base.bag = { x: this.bag.x, y: this.bag.y };
        this.walkMs = 0;
        this.bumped = 0;
        this.showFrame(1);

        // flies: a cloud over the pile (Run 1) and a few round the carried bag
        const pile = this.anchor('litter_centre');
        this.pileFlies = this.state.run === 1 ? this.flies(10, 70, true, pile.x, pile.y - 30) : [];
        this.bagFlies = this.flies(this.state.run === 1 ? 4 : 2, 34, false);

        // The tag hangs from the bag's knot, to the left so it never covers Riyaz or the bag.
        const tagData = this.state.kilo.tag ?? station('s01').kilo!.tag;
        const knot = this.anchor('riyaz_hand');
        new KiloTag(this, knot.x, knot.y, tagData, this.state.reducedMotion, { dx: -150, dy: 14 })
            .setDepth(30);

        // The walk: hold → (task 02) or Space, or hold the pointer on the right half.
        const kb = this.input.keyboard!;
        kb.on('keydown-SPACE', () => this.press());
        kb.on('keyup-SPACE', () => { this.holding = false; });
        kb.on('keydown-ENTER', () => this.act());
        kb.on('keydown-RIGHT', () => this.press());
        kb.on('keyup-RIGHT', () => { this.holding = false; });
        this.input.on('pointerdown', (p: Phaser.Input.Pointer) => {
            if (this.phase === 'walk' && p.x >= 960) this.holding = true;
        });
        this.input.on('pointerup', () => { this.holding = false; });

        this.prompt.show(this.prompts().walk, 'Hold →');

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

    update(time: number, delta: number) {
        this.buzz(time);
        this.moveCart(delta);
        if (this.phase !== 'walk' || !this.holding) return this.showFrame(1);
        if (this.cartBlocks()) return this.bump();
        const seconds = (this.stationData.params as { walk_seconds: number }).walk_seconds;
        this.t = Math.min(1, this.t + delta / (seconds * 1000));
        this.walkMs += delta;
        this.showFrame([0, 1, 2, 1][Math.floor(this.walkMs / FRAME_MS) % 4]);
        this.applyPan();
        if (this.t >= 1) this.reachEnd();
    }

    /** One walk frame visible; the passing frame rides a little higher (the bob). */
    private showFrame(i: number) {
        const bob = this.state.reducedMotion || i !== 1 || !this.holding ? 0 : -3;
        this.frames.forEach((f, k) => f.setVisible(k === i).setY(this.base.riyaz.y - this.world.y + bob));
    }

    /** The cart sets off once Riyaz is part-way down the street and rolls out to the kerb. */
    private moveCart(delta: number) {
        const c = this.cart;
        if (!c) return;
        if (c.k < 0 && this.t >= CART_FROM) {
            c.k = 0;
            if (this.phase === 'walk') this.prompt.show(this.prompts().wait, 'Release →');
        }
        if (c.k < 0 || c.k >= 1) return;
        c.k = Math.min(1, c.k + delta / CART_MS);
        this.placeCart(c.k);
        if (c.k >= 1) {
            this.tweens.add({ targets: [c.img, c.shadow], alpha: 0, duration: 300 });
            if (this.phase === 'walk') this.prompt.show(this.prompts().walk, 'Hold →');
        }
    }

    /** k 0..1 along the cart's trip: from 0.65 m behind its render spot (by the shops) to 1.85 m in front. */
    private placeCart(k: number) {
        const c = this.cart!;
        const m = 0.65 - 2.5 * k;
        c.img.setPosition(c.home.x + M_PX.x * m, c.home.y - M_PX.y * m);
        c.shadow.setPosition(c.img.x + c.off.x, c.img.y + c.off.y);
    }

    private cartBlocks() {
        const c = this.cart;
        return !!c && c.k >= CART_LANE[0] && c.k <= CART_LANE[1] && this.t >= CART_ZONE[0] && this.t <= CART_ZONE[1];
    }

    /** Walked into the cart: a jolt, a step back, the bag swings. */
    private bump() {
        this.showFrame(1);
        if (this.time.now - this.bumped < 500) return;
        this.bumped = this.time.now;
        this.t = Math.max(0, this.t - 0.02);
        this.applyPan();
        this.events.emit('sfx', 'bump');
        if (this.state.reducedMotion) return;
        this.cameras.main.shake(120, 0.003);
        this.tweens.add({ targets: this.bag, angle: { from: -10, to: 0 }, duration: 380, ease: 'Back.easeOut' });
    }

    /** n flies: round a fixed point in the world (the pile), or following the bag. */
    private flies(n: number, r: number, inWorld: boolean, x = 0, y = 0): Fly[] {
        if (this.state.reducedMotion) return [];
        return Array.from({ length: n }, (_, i) => {
            const dot = this.add.circle(x, y, 2.6, 0x1c1714, 0.9).setDepth(inWorld ? 0 : 31);
            if (inWorld) this.world.add(dot);
            return { dot, phase: i * 2.1, r: r * (0.5 + (i % 3) * 0.25), speed: 0.004 + (i % 4) * 0.0012, home: { x, y } };
        });
    }

    private buzz(time: number) {
        for (const f of this.pileFlies) {
            f.dot.setPosition(f.home.x + Math.cos(time * f.speed + f.phase) * f.r, f.home.y + Math.sin(time * f.speed * 1.7 + f.phase) * f.r * 0.45);
        }
        if (!this.bagFlies.length) return;
        const knot = this.anchor('kilo_centre');
        const bx = this.bag.x + knot.x - this.base.bag.x + this.world.x, by = this.bag.y + knot.y - this.base.bag.y + this.world.y - 10;
        for (const f of this.bagFlies) {
            f.dot.setPosition(bx + Math.cos(time * f.speed + f.phase) * f.r, by + Math.sin(time * f.speed * 1.9 + f.phase) * f.r * 0.6);
        }
    }

    /** Slide the plate; Riyaz and the bag counter-shift so he stays near the centre, walking. */
    private applyPan() {
        const wx = this.pan.x * this.t;
        const wy = this.pan.y * this.t;
        this.world.setPosition(wx, wy);
        this.frames.forEach((f) => f.setX(this.base.riyaz.x - wx));
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
