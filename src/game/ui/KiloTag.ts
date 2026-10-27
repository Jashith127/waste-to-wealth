// The kilo's value tag: a hanging price tag on a string (art-bible §8), clipped corners and a punched
// hole, a small caption ("Disposal fee"), the value in its meaning colour, and a note. The one thing
// the player tracks.
import { GameObjects, Math as PMath, Scene } from 'phaser';
import type { KiloTagState } from '../state';
import { colour, css, font, motion } from '../theme';

const MIN_W = 176;
const H = 116;
const CLIP = 20;           // the clipped top corners
const HOLE_Y = 14;         // the punched hole the string ties through

/** Where the card hangs relative to the knot. Beside the kilo, never over it (art-bible §6.3 "kilo first"). */
export interface Hang { dx: number; dy: number }
export const HANG_DOCKED: Hang = { dx: 0, dy: 46 };

export class KiloTag extends GameObjects.Container {
    private card: GameObjects.Graphics;
    private value: GameObjects.Text;
    private note: GameObjects.Text;
    private label: GameObjects.Text;
    private string: GameObjects.Graphics;
    private face: GameObjects.Container;

    constructor(scene: Scene, x: number, y: number, tag: KiloTagState, private reducedMotion = false, hang: Hang = HANG_DOCKED) {
        super(scene, x, y);
        this.string = scene.add.graphics();
        const sag = Math.abs(hang.dx) * 0.35 + 12;
        const pts = Array.from({ length: 17 }, (_, i) => {
            const t = i / 16;   // quadratic curve from the knot, sagging, to the top of the card
            const cx = hang.dx / 2, cy = Math.max(hang.dy, 0) / 2 + sag;
            return new PMath.Vector2(2 * (1 - t) * t * cx + t * t * hang.dx, 2 * (1 - t) * t * cy + t * t * hang.dy);
        });
        this.string.lineStyle(3, colour.ink, 1).strokePoints(pts);
        this.face = scene.add.container(hang.dx, hang.dy - HOLE_Y);      // the string ends in the hole
        this.card = scene.add.graphics();
        this.label = scene.add.text(0, 38, '', { fontFamily: font.display, fontSize: 15, fontStyle: '800', color: css.muted }).setOrigin(0.5).setLetterSpacing(1.5);
        this.value = scene.add.text(0, 68, '', { fontFamily: font.display, fontSize: 42, fontStyle: '800', color: css.ink }).setOrigin(0.5, 0.5);
        this.note = scene.add.text(0, 99, '', { fontFamily: font.body, fontSize: 17, color: css.muted }).setOrigin(0.5, 0.5);
        this.face.add([this.card, this.label, this.value, this.note]);
        this.add([this.string, this.face]);
        this.render(tag);
        scene.add.existing(this);
    }

    /** The card grows to fit its note (a long note ran past a fixed-width card). */
    private render(tag: KiloTagState) {
        this.label.setText((tag.label ?? '').toUpperCase());
        this.value.setText(tag.value).setColor(css[tag.meaning]);
        this.note.setText(tag.note ?? '');
        const w = this.halfWidth * 2;
        const shape = (dx: number, dy: number) => [[-w / 2 + CLIP, 0], [w / 2 - CLIP, 0], [w / 2, CLIP], [w / 2, H], [-w / 2, H], [-w / 2, CLIP]]
            .map(([x, y]) => new PMath.Vector2(x + dx, y + dy));
        const g = this.card.clear();
        g.fillStyle(colour.ink, 0.3).fillPoints(shape(2, 6), true);
        g.fillStyle(colour.card, 1).fillPoints(shape(0, 0), true);
        g.lineStyle(3, colour.ink, 1).strokePoints(shape(0, 0), true);
        g.fillStyle(colour[tag.meaning], 1).fillCircle(0, HOLE_Y, 8);   // a meaning-coloured eyelet
        g.fillStyle(colour.ink, 1).fillCircle(0, HOLE_Y, 4);
    }

    /** Half the card's width, so a docked tag can keep its right edge clear of the HUD buttons. */
    get halfWidth() {
        return Math.max(MIN_W, this.value.width + 40, this.note.width + 32, this.label.width + 40) / 2;
    }

    /** Swing in from the knot. */
    appear() {
        if (this.reducedMotion) return;
        this.setAngle(-14);
        this.scene.tweens.add({ targets: this, angle: 0, duration: 900, ease: 'Elastic.easeOut', easeParams: [1, 0.45] });
    }

    /** −₹5 → +₹3: flip on the vertical axis (300 ms). */
    flipTo(tag: KiloTagState) {
        if (this.reducedMotion) return this.render(tag);
        this.scene.tweens.add({
            targets: this.face, scaleX: 0, duration: motion.tagFlip / 2, ease: 'Sine.easeIn',
            onComplete: () => {
                this.render(tag);
                this.scene.tweens.add({ targets: this.face, scaleX: 1, duration: motion.tagFlip / 2, ease: 'Sine.easeOut' });
            },
        });
    }
}
