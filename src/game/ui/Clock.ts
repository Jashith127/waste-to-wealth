// The HUD time-of-day clock (top-left, left of the prompt pill): a sun or moon on a small arc and the
// phase word from hud.json. Never a clock time: no times are evidenced except vendor hours.
import { GameObjects, Scene } from 'phaser';
import hud from '../../data/hud.json';
import type { ClockPhase } from '../content';
import { colour, css, font, layout, motion } from '../theme';

// Where the sun sits on the dial's arc, in degrees (180 = left horizon, 90 = top, 0 = right horizon).
const SUN_ANGLE: Record<Exclude<ClockPhase, 'night'>, number> = { morning: 145, evening: 28 };

export class Clock extends GameObjects.Container {
    private bg: GameObjects.Graphics;
    private dial: GameObjects.Graphics;
    private label: GameObjects.Text;
    private phase?: ClockPhase;

    constructor(scene: Scene, private reducedMotion = false) {
        const { x, y, w, h } = layout.clock;
        super(scene, x, y);
        this.bg = scene.add.graphics();
        this.bg.fillStyle(colour.ink, 0.92).fillRoundedRect(0, -h / 2, w, h, h / 2);
        this.dial = scene.add.graphics();
        this.label = scene.add.text(80, 1, '', { fontFamily: font.display, fontSize: 28, fontStyle: '600', color: css.cream }).setOrigin(0, 0.5);
        this.add([this.bg, this.dial, this.label]);
        scene.add.existing(this);
    }

    set(phase: ClockPhase) {
        if (phase === this.phase) return;
        this.phase = phase;
        this.label.setText(hud.clock.phases[phase].label);
        this.drawDial(phase);
        if (this.reducedMotion) return;
        this.label.setAlpha(0);
        this.scene.tweens.add({ targets: this.label, alpha: 1, duration: motion.normal, ease: 'Sine.easeOut' });
    }

    /** A horizon arc 44 px wide, with the sun on it, or a crescent moon above it at night. */
    private drawDial(phase: ClockPhase) {
        const cx = 44, cy = 12, r = 22;
        const g = this.dial.clear();
        g.lineStyle(3, colour.cream, 0.45).beginPath().arc(cx, cy, r, Math.PI, 0).strokePath();
        g.lineStyle(3, colour.cream, 0.45).lineBetween(cx - r - 6, cy, cx + r + 6, cy);
        if (phase === 'night') {
            g.fillStyle(colour.cream, 1).fillCircle(cx, cy - 14, 11);
            g.fillStyle(colour.ink, 1).fillCircle(cx + 6, cy - 18, 10);
            return;
        }
        const a = (SUN_ANGLE[phase] * Math.PI) / 180;
        const sx = cx + Math.cos(a) * r, sy = cy - Math.sin(a) * r;
        g.fillStyle(phase === 'evening' ? colour.cost : colour.pay, 1).fillCircle(sx, sy, 8);
    }
}
