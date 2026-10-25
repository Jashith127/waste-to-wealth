// Code-only grey boxes for stations whose Blender set is not built yet (tasks 05–07, no Blender).
// Same camera as art/scripts/lib/rig.py: 2:1 dimetric, 11 m across 1920 px, so a later Blender set
// with the same TARGET puts things in the same places.
import { GameObjects, Scene } from 'phaser';
import { hasStation, station, type Tag } from '../content';
import { getState, setState } from '../state';
import { colour, css, font, FRAME } from '../theme';
import { drawCard, drawChip } from './card';

const PPM = 1920 / 11;
const GREY = { top: 0xb4aea6, front: 0x9a958e, side: 0x6e6a65 };

export type V3 = [number, number, number];

export class GreyBox {
    constructor(private scene: Scene, private target: V3) {}

    /** World metres -> frame pixels (rig.to_screen). */
    point([x, y, z]: V3): { x: number; y: number } {
        const [tx, ty, tz] = this.target;
        const dx = x - tx, dy = y - ty, dz = z - tz;
        return {
            x: FRAME.width / 2 + (dx + dy) * 0.7071 * PPM,
            y: FRAME.height / 2 - (-dx * 0.3536 + dy * 0.3536 + dz * 0.866) * PPM,
        };
    }

    /** The street-slice plinth (x0..x1, y 0..depth) with its cut edge, as in Placeholder. */
    plinth(x0: number, x1: number, depth = 6) {
        const g = this.scene.add.graphics();
        this.quad(g, [[x0, 0, 0], [x1, 0, 0], [x1, depth, 0], [x0, depth, 0]], 0x8a8580);
        this.quad(g, [[x0, 0, 0], [x1, 0, 0], [x1, 0, -0.25], [x0, 0, -0.25]], 0x5a463a);
        this.quad(g, [[x1, 0, 0], [x1, depth, 0], [x1, depth, -0.25], [x1, 0, -0.25]], 0x3a322d);
        return g;
    }

    /** A box from corner lo to corner hi, faces shaded as lit from the top-left. The Graphics sits at
     * the projection of the box's bottom centre, so moving it moves the box. */
    box(lo: V3, hi: V3, tint: Partial<typeof GREY> = {}) {
        const c = { ...GREY, ...tint };
        const base = this.point([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]]);
        const g = this.scene.add.graphics().setPosition(base.x, base.y);
        const rel = (p: V3) => { const s = this.point(p); return { x: s.x - base.x, y: s.y - base.y }; };
        const face = (pts: V3[], fill: number) => {
            const s = pts.map(rel);
            g.fillStyle(fill, 1).beginPath().moveTo(s[0].x, s[0].y);
            s.slice(1).forEach((p) => g.lineTo(p.x, p.y));
            g.closePath().fillPath();
            g.lineStyle(2, colour.ink, 0.35).strokePath();
        };
        const [x0, y0, z0] = lo, [x1, y1, z1] = hi;
        face([[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]], c.front);     // faces -Y
        face([[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]], c.side);      // faces +X
        face([[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], c.top);
        return g;
    }

    private quad(g: GameObjects.Graphics, pts: V3[], fill: number) {
        const s = pts.map((p) => this.point(p));
        g.fillStyle(fill, 1).beginPath().moveTo(s[0].x, s[0].y);
        s.slice(1).forEach((p) => g.lineTo(p.x, p.y));
        g.closePath().fillPath();
    }
}

/** A deck card with a word on it, centred at (x, y); optional meaning band and Proposed chip. */
export function labelCard(scene: Scene, x: number, y: number, text: string, opts: { band?: number; proposed?: boolean; size?: number; color?: string } = {}) {
    const c = scene.add.container(x, y);
    const t = scene.add.text(0, 0, text, { fontFamily: font.display, fontSize: opts.size ?? 30, fontStyle: '700', color: opts.color ?? css.ink }).setOrigin(0.5);
    const chip = opts.proposed
        ? scene.add.text(0, 0, 'Proposed', { fontFamily: font.display, fontSize: 22, fontStyle: '700', color: css.cream }).setOrigin(0.5)
        : undefined;
    const chipW = chip ? chip.width + 20 : 0;
    const w = t.width + 48 + (chip ? chipW + 14 : 0), h = Math.max(t.height + 26, 60);
    const g = scene.add.graphics();
    drawCard(g, -w / 2, -h / 2, w, h, opts.band);
    t.setX(chip ? -w / 2 + 24 + t.width / 2 : 0);
    c.add([g, t]);
    if (chip) {
        const cx = w / 2 - 24 - chipW / 2;
        const cg = scene.add.graphics();
        drawChip(cg, cx - chipW / 2, -17, chipW, 34, colour.brown);
        chip.setX(cx);
        c.add([cg, chip]);
    }
    return c.setDepth(35);
}

/** The kilo's tag from s03 on: +₹[__]. A deep link straight into s04–s07 has no tag yet, and a run
 * through a grey-box s03 never flipped it, so default to s03's flipped tag (task 08). */
export function paidTag(scene: Scene): Tag {
    const current = getState(scene).kilo.tag;
    if (current?.meaning === 'income') return current;
    const fallback: Tag = { value: '+₹[__]', meaning: 'income', note: '₹[__]/kg, payout to be set' };
    const tag = (hasStation('s03') ? (station('s03').params?.tag_after as Tag | undefined) : undefined) ?? fallback;
    setState(scene, { kilo: { carried: false, tag } });
    return tag;
}
