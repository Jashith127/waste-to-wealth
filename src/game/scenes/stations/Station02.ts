// Station 2 · The walk, Market street to Russell Market. Riyaz walks the pavement freely: on down the
// street and back (→ ←), toward the shops and the kerb (↑ ↓), or wherever the pointer is held. Run 1
// ends at the back-lane pile (the −₹5 stays on the tag); Run 2 reaches the hub's drop window.
//
// The set is a 3200×1920 plate at the normal 174.5 px/m (see s02_build.py), and this scene shows a
// 1920×1080 window over it that follows Riyaz. Riyaz is rendered alone in each direction he walks
// and placed here in world metres; the handcart rolls down across his way. Everyone else stands
// still. The plate keeps every set piece; those he can pass behind are also rendered alone
// (occ_<name>) and depth-sorted with him by their ground footprints (layers.json `world`).
import { GameObjects } from 'phaser';
import { station } from '../../content';
import { goNext } from '../../flow';
import { setState } from '../../state';
import { motion } from '../../theme';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'walk' | 'dump' | 'leave';
type Dir = 'e' | 'w' | 'n' | 's';
type Box = [number, number, number, number];          // world x0, x1, y0, y1 (metres)
interface Pt { x: number; y: number }
interface World {
    occ: Record<string, Box>;
    chars: Record<string, [number, number]>;
    litter: Box;
    cart: Box;
}

const FRAMES = 8;                          // one walk cycle per direction (s02_build.WALK_FRAMES)
const CYCLE = 0.96;                        // metres per walk cycle: 4 × the gait's stride
const R = 0.22;                            // a walker's radius
const BOUNDS = { x0: -1.4, x1: 14.6, y0: 0.32, y1: 2.3 };   // the walkable pavement (kerb to awnings)
const FEET = { x: 900, y: 610 };           // where the camera keeps Riyaz's feet on screen
const CART_START_X = 3.0;                  // Riyaz this far down the street sets the handcart off
const CART_SPEED = 0.9;                    // m/s, straight down from the shopfront toward the road
const CART_END_DY = -3.3;                  // it rolls this far (onto the road), then it is gone
const RUN2_END_X = 12.0;                   // Run 2: the hub's drop window at the market end
const DUMP_REACH = 0.9;                    // Run 1: this close to the pile, he can leave the kilo
interface Fly { dot: GameObjects.Arc; phase: number; r: number; speed: number; home: Pt }

/** One sortable thing: its ground footprint and what draws it. */
interface Item { box: () => Box; img: () => GameObjects.Image | undefined; occ?: boolean }

/** Someone who walks: a frame per direction and phase, all rendered at `origin`, slid to `pos`. */
interface Walker {
    name: string; origin: Pt; pos: Pt; dir: Dir; dist: number; cycle: number;
    frames: Map<string, GameObjects.Image>; shown?: GameObjects.Image; shadow: GameObjects.Ellipse;
}


export default class Station02 extends StationScene {
    private phase: Phase = 'walk';
    private w!: World;
    private proj!: { o: Pt; x: Pt; y: Pt };
    private riyaz!: Walker;
    private holders: Pt[] = [];
    private items: Item[] = [];
    private cart!: { img: GameObjects.Image; shadow: GameObjects.Image; home: Pt; shadowHome: Pt; dy: number; state: 'parked' | 'rolling' | 'gone' };
    private bag!: GameObjects.Image;
    private bagHome = { x: 0, y: 0 };
    private tag!: KiloTag;
    private carrying = true;
    private keys!: Record<string, Phaser.Input.Keyboard.Key>;
    private steer?: Pt;                    // screen point the pointer is held on
    private holdForward = false;
    private detour = 0;                    // which way (±Y) Riyaz is stepping round something in his way
    private cartBlock?: Box;               // the cart's box, when it was the last thing in his way
    private ring?: GameObjects.Arc;
    private arrivedAt = 0;
    private left = false;
    private bumped = 0;
    private waitShown = false;
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
        this.left = false;
        this.carrying = true;
        this.items = [];
        this.holders = [];
        this.waitShown = false;
        this.w = (this.layers as unknown as { world: World }).world;
        const a = (k: string) => this.anchor(`proj_${k}`);
        const o = a('o');
        this.proj = { o, x: { x: a('x').x - o.x, y: a('x').y - o.y }, y: { x: a('y').x - o.x, y: a('y').y - o.y } };

        this.layer('bg').setDepth(0);
        const run1 = this.state.run === 1;
        if (run1) {
            if (this.layers?.layers['litter_shadow']) this.layer('litter_shadow').setDepth(1);
            const litter = this.layer('litter');
            this.items.push({ box: () => this.w.litter, img: () => litter });
        }

        // set pieces a walker can pass behind
        for (const [name, box] of Object.entries(this.w.occ)) {
            if (!this.layers!.layers[`occ_${name}`]) continue;
            const img = this.layer(`occ_${name}`);
            this.items.push({ box: () => box, img: () => img, occ: true });
        }

        // the stall-holders, standing easy
        for (const name of ['anthony', 'arif']) {
            if (!this.layers!.layers[`${name}_idle`]) continue;
            const img = this.layer(`${name}_idle`);
            const [x, y] = this.w.chars[name];
            this.holders.push({ x, y });
            this.items.push({ box: () => [x - 0.25, x + 0.25, y - 0.25, y + 0.25], img: () => img });
        }

        // Riyaz
        this.riyaz = this.walker('riyaz', [
            ...(['e', 'w', 'n', 's'] as Dir[]).flatMap((d) => [...Array(FRAMES).keys()].map((i) => `walk_${d}${i}`)),
            ...['e', 'w', 'n', 's'].flatMap((d) => [`stand_${d}`, `empty_${d}`]),
        ], 'e');
        this.bag = this.layer('kilo').setVisible(false);
        this.bagHome = { x: this.bag.x, y: this.bag.y };

        // the handcart: parked at the shopfront until Riyaz is part-way down the street
        const cartShadow = this.layers?.layers['cart_shadow'] ? this.layer('cart_shadow').setDepth(1) : this.add.image(0, 0, '__DEFAULT').setVisible(false);
        const cartImg = this.layer('cart');
        this.cart = { img: cartImg, shadow: cartShadow, home: { x: cartImg.x, y: cartImg.y }, shadowHome: { x: cartShadow.x, y: cartShadow.y }, dy: 0, state: 'parked' };
        this.items.push({ box: () => this.cartBox(), img: () => this.cart.img });

        // flies: a cloud over the pile (Run 1) and a few round the carried bag
        const pile = this.anchor('litter_centre');
        this.pileFlies = run1 ? this.flies(10, 70, true, pile.x, pile.y - 30) : [];
        this.bagFlies = this.flies(run1 ? 4 : 2, 34, false);

        // The tag hangs from the bag's knot, to the left so it never covers Riyaz or the bag.
        const tagData = this.state.kilo.tag ?? station('s01').kilo!.tag;
        this.tag = new KiloTag(this, 0, 0, tagData, this.state.reducedMotion, { dx: -150, dy: 14 }).setDepth(30);

        // input: arrows or WASD walk; Space or → held walks on down the street; a held pointer steers
        const kb = this.input.keyboard!;
        this.keys = kb.addKeys('LEFT,RIGHT,UP,DOWN,W,A,S,D') as Record<string, Phaser.Input.Keyboard.Key>;
        kb.on('keydown-SPACE', () => { if (this.phase === 'walk') this.holdForward = true; else this.act(); });
        kb.on('keyup-SPACE', () => { this.holdForward = false; });
        kb.on('keydown-ENTER', () => this.act());
        this.input.on('pointerdown', (p: Phaser.Input.Pointer) => { if (this.phase === 'walk') this.steer = { x: p.x, y: p.y }; });
        this.input.on('pointermove', (p: Phaser.Input.Pointer) => { if (this.steer && p.isDown) this.steer = { x: p.x, y: p.y }; });
        this.input.on('pointerup', () => { this.steer = undefined; });

        this.prompt.show(this.prompts().walk, 'Arrows');
        this.place(this.riyaz);
        this.follow(1);
        this.update(this.time.now, 0);
    }

    private act() {
        if (this.phase === 'dump') this.dump();
        else if (this.phase === 'leave' && this.time.now - this.arrivedAt > 400) this.leave();
    }

    // ------------------------------------------------------------------ world ↔ plate

    /** World metres on the ground → plate pixels. */
    private px(p: Pt): Pt {
        const { o, x, y } = this.proj;
        return { x: o.x + p.x * x.x + p.y * y.x, y: o.y + p.x * x.y + p.y * y.y };
    }

    /** Plate pixels → world metres on the ground. */
    private ground(q: Pt): Pt {
        const { o, x, y } = this.proj;
        const det = x.x * y.y - y.x * x.y;
        const dx = q.x - o.x, dy = q.y - o.y;
        return { x: (dx * y.y - y.x * dy) / det, y: (x.x * dy - dx * x.y) / det };
    }

    // ------------------------------------------------------------------ walkers

    private walker(name: string, poses: string[], dir: Dir): Walker {
        const [x, y] = this.w.chars[name];
        const frames = new Map<string, GameObjects.Image>();
        for (const pose of poses) {
            if (this.layers!.layers[`${name}_${pose}`]) frames.set(pose, this.layer(`${name}_${pose}`).setVisible(false));
        }
        const shadow = this.add.ellipse(0, 0, 74, 26, 0x1c1714, 0.26).setDepth(2);
        this.world.add(shadow);
        const wk: Walker = { name, origin: { x, y }, pos: { x, y }, dir, dist: 0, cycle: CYCLE, frames, shadow };
        this.items.push({ box: () => this.circleBox(wk.pos), img: () => wk.shown });
        return wk;
    }

    private circleBox(p: Pt, r = R): Box {
        return [p.x - r, p.x + r, p.y - r, p.y + r];
    }

    /** Show the walker's frame for `pose` at its position. */
    private place(wk: Walker, pose?: string) {
        const key = pose ?? this.standPose(wk);
        const img = wk.frames.get(key) ?? wk.shown;
        if (wk.shown && wk.shown !== img) wk.shown.setVisible(false);
        if (!img) return;
        const info = this.layers!.layers[`${wk.name}_${key}`];
        const a = this.px(wk.pos), b = this.px(wk.origin);
        if (info) img.setPosition(info.x + a.x - b.x, info.y + a.y - b.y);
        img.setVisible(true);
        wk.shown = img;
        wk.shadow.setPosition(a.x + 14, a.y + 2);     // the morning sun throws it a little to the right
    }

    private standPose(wk: Walker) {
        return `${this.carrying ? 'stand' : 'empty'}_${wk.dir}`;
    }

    private walkPose(wk: Walker) {
        return `walk_${wk.dir}${Math.floor((wk.dist / wk.cycle) * FRAMES) % FRAMES}`;
    }

    /** The direction a move faces: whichever world axis it mostly runs along. */
    private facing(v: Pt): Dir {
        return Math.abs(v.x) >= Math.abs(v.y) ? (v.x >= 0 ? 'e' : 'w') : (v.y >= 0 ? 'n' : 's');
    }

    // ------------------------------------------------------------------ collision

    private hitsBox(p: Pt, r: number, b: Box) {
        const cx = Math.max(b[0], Math.min(p.x, b[1])), cy = Math.max(b[2], Math.min(p.y, b[3]));
        return (p.x - cx) ** 2 + (p.y - cy) ** 2 < r * r;
    }

    /** What Riyaz at `p` would run into, or null: the pavement's edges, anything standing on it, the cart. */
    private blocker(p: Pt): Box | null {
        if (p.x < BOUNDS.x0 || p.x > BOUNDS.x1 || p.y < BOUNDS.y0 || p.y > BOUNDS.y1) return [p.x, p.x, p.y, p.y];
        for (const b of Object.values(this.w.occ)) if (this.hitsBox(p, R, b)) return b;
        if (this.state.run === 1 && this.hitsBox(p, R, this.w.litter)) return this.w.litter;
        for (const h of this.holders) if (this.hitsBox(p, R, this.circleBox(h, 0.25))) return this.circleBox(h, 0.25);
        if (this.cart.state !== 'gone' && this.hitsBox(p, R, this.cartBox())) return (this.cartBlock = this.cartBox());
        return null;
    }

    // ------------------------------------------------------------------ the frame

    update(time: number, delta: number) {
        const dt = Math.min(delta, 50) / 1000;
        this.moveRiyaz(dt);
        this.moveCart(dt);
        this.follow(dt);
        this.hangTag();
        this.buzz(time);
        this.sort();
    }

    private input2(): Pt {
        if (this.phase !== 'walk') return { x: 0, y: 0 };
        const k = this.keys;
        let x = (k.RIGHT.isDown || k.D.isDown || this.holdForward ? 1 : 0) - (k.LEFT.isDown || k.A.isDown ? 1 : 0);
        let y = (k.UP.isDown || k.W.isDown ? 1 : 0) - (k.DOWN.isDown || k.S.isDown ? 1 : 0);
        if (!x && !y && this.steer) {               // toward the held pointer, on the ground
            const g = this.ground({ x: this.steer.x - this.world.x, y: this.steer.y - this.world.y });
            x = g.x - this.riyaz.pos.x;
            y = g.y - this.riyaz.pos.y;
            if (Math.hypot(x, y) < 0.15) return { x: 0, y: 0 };
        }
        const n = Math.hypot(x, y);
        return n ? { x: x / n, y: y / n } : { x: 0, y: 0 };
    }

    private moveRiyaz(dt: number) {
        const wk = this.riyaz;
        const v = this.input2();
        if (!v.x && !v.y) return this.place(wk);
        const speed = 10 / (this.stationData.params as { walk_seconds: number }).walk_seconds;
        const step = speed * dt;
        wk.dir = this.facing(v);
        // straight on; else slide along whatever is in the way; else step round it (→ held still gets there)
        const clear = (t: Pt, d = step) => (t.x || t.y) && !this.blocker({ x: wk.pos.x + t.x * d, y: wk.pos.y + t.y * d });
        const block = this.blocker({ x: wk.pos.x + v.x * step, y: wk.pos.y + v.y * step });
        if (!block) this.detour = 0;
        else if (this.cart.state === 'rolling' && block === this.cartBlock && !this.inCartPath(wk.pos)) {
            return this.bump(block);                    // out of its way already: wait for it to pass
        } else if (!this.detour) {
            // pick a side to go round by and keep it until the way ahead is clear (no dithering):
            // the side away from the obstacle, unless only the other side has room
            const away = (block[2] + block[3]) / 2 <= wk.pos.y ? 1 : -1;
            this.detour = clear({ x: 0, y: away }, 0.45) || !clear({ x: 0, y: -away }, 0.45) ? away : -away;
        }
        const s = this.detour;
        const tries: Pt[] = [v, { x: v.x, y: 0 }, { x: 0, y: v.y }, ...(block && v.x ? [{ x: v.x * 0.5, y: s * 0.87 }, { x: 0, y: s }] : [])];
        const go = tries.find((t) => clear(t));
        if (!go) {
            if (block && v.x && !clear({ x: 0, y: s })) this.detour = -s;     // that side is shut too: try the other
            return this.bump(block);
        }
        wk.pos = { x: wk.pos.x + go.x * step, y: wk.pos.y + go.y * step };
        wk.dist += step;
        this.place(wk, this.walkPose(wk));
        this.checkArrival();
    }

    /** Walked into the cart (or a person): a jolt, the bag swings. */
    private bump(block: Box | null) {
        this.place(this.riyaz);
        if (!block || this.time.now - this.bumped < 600) return;
        if (this.cart.state !== 'rolling' || !this.hitsBox(this.riyaz.pos, R + 0.08, this.cartBox())) return;
        this.bumped = this.time.now;
        this.events.emit('sfx', 'bump');
        if (this.state.reducedMotion) return;
        this.cameras.main.shake(120, 0.003);
    }

    private checkArrival() {
        if (this.phase !== 'walk') return;
        const p = this.riyaz.pos;
        if (this.state.run === 1) {
            const b = this.w.litter;
            const dx = Math.max(b[0] - p.x, 0, p.x - b[1]), dy = Math.max(b[2] - p.y, 0, p.y - b[3]);
            if (Math.hypot(dx, dy) <= DUMP_REACH) this.reachEnd();
        } else if (p.x >= RUN2_END_X) this.reachEnd();
    }

    // ------------------------------------------------------------------ the handcart

    /** Whether Riyaz at `p` stands in the strip of pavement the cart rolls down (across the street). */
    private inCartPath(p: Pt) {
        return p.x + R > this.w.cart[0] && p.x - R < this.w.cart[1];
    }

    private cartBox(): Box {
        const b = this.w.cart, d = this.cart.dy;
        return [b[0], b[1], b[2] + d, b[3] + d];
    }

    /** Once Riyaz is part-way down the street it rolls straight down to the road, stopping for him. */
    private moveCart(dt: number) {
        const c = this.cart;
        if (c.state === 'parked' && this.riyaz.pos.x >= CART_START_X) c.state = 'rolling';
        if (c.state !== 'rolling') return;
        const step = CART_SPEED * dt;
        const next: Box = [this.w.cart[0], this.w.cart[1], this.cartBox()[2] - step, this.cartBox()[3] - step];
        if (!this.hitsBox(this.riyaz.pos, R, next)) c.dy -= step;
        const o = this.px({ x: 0, y: 0 }), d = this.px({ x: 0, y: c.dy });
        c.img.setPosition(c.home.x + d.x - o.x, c.home.y + d.y - o.y);
        c.shadow.setPosition(c.shadowHome.x + d.x - o.x, c.shadowHome.y + d.y - o.y);

        // ask Riyaz to let it pass while it is near him and still to cross his way
        const near = Math.abs((this.w.cart[0] + this.w.cart[1]) / 2 - this.riyaz.pos.x) < 2.6 && this.cartBox()[2] > BOUNDS.y0 - 0.3;
        if (this.phase === 'walk' && near !== this.waitShown) {
            this.waitShown = near;
            this.prompt.show(near ? this.prompts().wait : this.prompts().walk, near ? 'Wait' : 'Arrows');
        }
        if (c.dy <= CART_END_DY) {
            c.state = 'gone';
            this.tweens.add({ targets: [c.img, c.shadow], alpha: 0, duration: 400 });
            if (this.phase === 'walk' && this.waitShown) {
                this.waitShown = false;
                this.prompt.show(this.prompts().walk, 'Arrows');
            }
        }
    }

    // ------------------------------------------------------------------ camera, tag, flies, sorting

    /** Ease the plate so Riyaz's feet stay near FEET, never showing past the plate's edge. */
    private follow(dt: number) {
        if (this.left) return;
        const f = this.px(this.riyaz.pos);
        const tx = Math.min(0, Math.max(1920 - 3200, FEET.x - f.x));
        const ty = Math.min(0, Math.max(1080 - 1920, FEET.y - f.y));
        const k = dt >= 1 ? 1 : 1 - Math.exp(-dt * 5);
        this.world.setPosition(this.world.x + (tx - this.world.x) * k, this.world.y + (ty - this.world.y) * k);
    }

    /** The bag's knot on screen, for the facing Riyaz has. */
    private hand(): Pt {
        const h = this.anchor(`riyaz_hand_${this.riyaz.dir}`), a = this.px(this.riyaz.pos), b = this.px(this.riyaz.origin);
        return { x: h.x + a.x - b.x + this.world.x, y: h.y + a.y - b.y + this.world.y };
    }

    /** The tag hangs from the knot: in his hand, then on the pile (the −₹5 stays). */
    private hangTag() {
        const knot = this.anchor('kilo_knot');
        const h = this.carrying ? this.hand() : { x: this.bag.x - this.bagHome.x + knot.x + this.world.x, y: this.bag.y - this.bagHome.y + knot.y + this.world.y };
        this.tag.setPosition(h.x, h.y);
    }

    /** n flies: round a fixed point in the world (the pile), or following the bag. */
    private flies(n: number, r: number, inWorld: boolean, x = 0, y = 0): Fly[] {
        if (this.state.reducedMotion) return [];
        return Array.from({ length: n }, (_, i) => {
            const dot = this.add.circle(x, y, 2.6, 0x1c1714, 0.9).setDepth(inWorld ? 900 : 31);
            if (inWorld) this.world.add(dot);
            return { dot, phase: i * 2.1, r: r * (0.5 + (i % 3) * 0.25), speed: 0.004 + (i % 4) * 0.0012, home: { x, y } };
        });
    }

    private buzz(time: number) {
        for (const f of this.pileFlies) {
            f.dot.setPosition(f.home.x + Math.cos(time * f.speed + f.phase) * f.r, f.home.y + Math.sin(time * f.speed * 1.7 + f.phase) * f.r * 0.45);
        }
        if (!this.bagFlies.length) return;
        const h = this.carrying ? this.hand() : { x: this.bag.x + this.anchor('kilo_centre').x - this.bagHome.x + this.world.x, y: this.bag.y + this.anchor('kilo_centre').y - this.bagHome.y + this.world.y };
        for (const f of this.bagFlies) {
            f.dot.setPosition(h.x + Math.cos(time * f.speed + f.phase) * f.r, h.y + 20 + Math.sin(time * f.speed * 1.9 + f.phase) * f.r * 0.6);
        }
    }

    /**
     * Depth-sort everything that can overlap a walker, by ground footprints: A is behind B when it lies
     * wholly to B's -X (up the street) or +Y (toward the shops) side; overlapping or diagonal pairs go by
     * their centres. Only pairs whose sprites overlap on screen are compared (a topological sort), and
     * pairs of set pieces are skipped: both are cut from the same render, so either order is right.
     */
    private sort() {
        const live = this.items.map((it) => ({ it, img: it.img(), box: it.box() })).filter((n) => n.img && n.img.visible && n.img.alpha > 0);
        const n = live.length;
        const rects = live.map(({ img }) => img!.getBounds());
        const key = live.map(({ box }) => (box[0] + box[1]) / 2 - (box[2] + box[3]) / 2);
        const after: number[][] = live.map(() => []);
        const indeg = new Array(n).fill(0);
        for (let i = 0; i < n; i++) {
            for (let j = i + 1; j < n; j++) {
                if (live[i].it.occ && live[j].it.occ) continue;
                const a = rects[i], b = rects[j];
                if (a.right <= b.x || b.right <= a.x || a.bottom <= b.y || b.bottom <= a.y) continue;
                const A = live[i].box, B = live[j].box;
                const aBehind = A[1] <= B[0] + 1e-3 || A[2] >= B[3] - 1e-3;
                const bBehind = B[1] <= A[0] + 1e-3 || B[2] >= A[3] - 1e-3;
                const iFirst = aBehind !== bBehind ? aBehind : key[i] <= key[j];
                const [lo, hi] = iFirst ? [i, j] : [j, i];
                after[lo].push(hi);
                indeg[hi] += 1;
            }
        }
        const order: number[] = [];
        const ready = [...Array(n).keys()].filter((i) => !indeg[i]);
        while (order.length < n) {
            if (!ready.length) {                       // a cycle (rare): break it at the farthest-back node
                const rest = [...Array(n).keys()].filter((i) => !order.includes(i) && !ready.includes(i));
                rest.sort((a, b) => key[a] - key[b]);
                ready.push(rest[0]);
                indeg[rest[0]] = 0;
            }
            ready.sort((a, b) => key[a] - key[b]);
            const i = ready.shift()!;
            if (order.includes(i)) continue;
            order.push(i);
            for (const j of after[i]) if (--indeg[j] === 0) ready.push(j);
        }
        order.forEach((i, k) => live[i].img!.setDepth(10 + k));
        this.world.sort('depth');
    }

    // ------------------------------------------------------------------ the end of the walk

    private reachEnd() {
        this.arrivedAt = this.time.now;
        this.steer = undefined;
        this.holdForward = false;
        if (this.state.run !== 1) return this.toLeave();

        this.phase = 'dump';
        const pile = this.anchor('dump');
        const g = this.ground(pile);
        this.riyaz.dir = this.facing({ x: g.x - this.riyaz.pos.x, y: g.y - this.riyaz.pos.y });
        this.place(this.riyaz);
        this.prompt.show(this.prompts().dump, 'Space');
        this.ring = this.hint(pile.x, pile.y, 92).setDepth(950);
        this.world.add(this.ring);
        const zone = this.add.zone(pile.x, pile.y, 300, 220).setInteractive({ useHandCursor: true }).on('pointerup', () => this.dump());
        this.world.add(zone);
    }

    /** Run 1: the bag leaves Riyaz's hand and lands on the pile; the tag stays −₹5. */
    private dump() {
        if (this.phase !== 'dump') return;
        this.phase = 'leave';
        this.ring?.destroy();
        this.arrivedAt = this.time.now;

        // the kilo prop takes over from the bag in his hand, which empties
        const h = this.hand(), knot = this.anchor('kilo_knot');
        this.bag.setPosition(this.bagHome.x + h.x - this.world.x - knot.x, this.bagHome.y + h.y - this.world.y - knot.y).setVisible(true);
        this.carrying = false;
        this.place(this.riyaz);
        const lb = this.w.litter, mid = (lb[0] + lb[1]) / 2;                 // it lands on the front of the pile
        this.items.push({ box: () => [mid - 0.2, mid + 0.2, lb[2] - 0.5, lb[2] - 0.1], img: () => this.bag });

        const pile = this.anchor('dump'), centre = this.anchor('kilo_centre');
        const to = { x: this.bagHome.x + pile.x - centre.x, y: this.bagHome.y + pile.y - 20 - centre.y };
        if (this.state.reducedMotion) this.bag.setPosition(to.x, to.y);
        else this.tweens.add({ targets: this.bag, ...to, duration: 420, ease: 'Cubic.easeOut' });

        setState(this, { kilo: { carried: false, tag: this.state.kilo.tag } });
        this.toLeave();
    }

    private toLeave() {
        this.phase = 'leave';
        this.prompt.show(this.prompts().leave, 'Space');
    }

    /** The base `leave()` tweens world.x to -260, which would undo the follow. Slide on from here. */
    protected leave() {
        if (this.left) return;
        this.left = true;
        if (!this.state.reducedMotion) {
            this.tweens.add({ targets: this.world, x: this.world.x - 260, duration: motion.transition, ease: 'Sine.easeIn' });
        }
        goNext(this);
    }
}
