// The kilo's value tag: a small deck card on a string (art-bible §8). The one thing the player tracks.
import { GameObjects, Math as PMath, Scene } from 'phaser';
import type { KiloTagState } from '../state';
import { colour, css, font, motion } from '../theme';
import { drawCard } from './card';

const MIN_W = 168;
const H = 92;

/** Where the card hangs relative to the knot. Beside the kilo, never over it (art-bible §6.3 "kilo first"). */
export interface Hang { dx: number; dy: number }
export const HANG_DOCKED: Hang = { dx: 0, dy: 46 };

export class KiloTag extends GameObjects.Container {
    private card: GameObjects.Graphics;
    private value: GameObjects.Text;
    private note: GameObjects.Text;
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
        this.face = scene.add.container(hang.dx, hang.dy);
        this.card = scene.add.graphics();
        this.value = scene.add.text(0, 30, '', { fontFamily: font.display, fontSize: 44, fontStyle: '700', color: css.ink }).setOrigin(0.5, 0.5);
        this.note = scene.add.text(0, 68, '', { fontFamily: font.body, fontSize: 18, color: css.muted }).setOrigin(0.5, 0.5);
        this.face.add([this.card, this.value, this.note]);
        this.add([this.string, this.face]);
        this.render(tag);
        scene.add.existing(this);
    }

    /** The card grows to fit its note ("₹[__]/kg, payout to be set" ran past a fixed-width card). */
    private render(tag: KiloTagState) {
        this.value.setText(tag.value).setColor(css[tag.meaning]);
        this.note.setText(tag.note ?? '');
        const w = Math.max(MIN_W, this.value.width + 32, this.note.width + 28);
        this.card.clear();
        drawCard(this.card, -w / 2, 0, w, H, colour[tag.meaning]);
    }

    /** Half the card's width, so a docked tag can keep its right edge clear of the HUD buttons. */
    get halfWidth() {
        return Math.max(MIN_W, this.value.width + 32, this.note.width + 28) / 2;
    }

    /** Swing in from the knot. */
    appear() {
        if (this.reducedMotion) return;
        this.setAngle(-14);
        this.scene.tweens.add({ targets: this, angle: 0, duration: 900, ease: 'Elastic.easeOut', easeParams: [1, 0.45] });
    }

    /** −₹5 → +₹[__]: flip on the vertical axis (300 ms). */
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
