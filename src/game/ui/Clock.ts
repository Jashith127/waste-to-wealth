// The time of day, drawn small in the objective card's header and on briefings: a sun on a horizon
// arc (morning low left, evening low right) or a crescent moon at night, and the phase word from
// hud.json. Never a clock time: no times are evidenced except vendor hours.
import type { GameObjects } from 'phaser';
import hud from '../../data/hud.json';
import type { ClockPhase } from '../content';
import { colour } from '../theme';

// Where the sun sits on the dial's arc, in degrees (180 = left horizon, 90 = top, 0 = right horizon).
const SUN_ANGLE: Record<Exclude<ClockPhase, 'night'>, number> = { morning: 145, evening: 28 };

export function phaseLabel(phase: ClockPhase) {
    return hud.clock.phases[phase].label;
}

/** A horizon arc `r` px in radius centred at (cx, cy), with the sun on it or the moon above it. */
export function drawPhaseIcon(g: GameObjects.Graphics, cx: number, cy: number, phase: ClockPhase, r = 14, line: number = colour.cream, bg: number = colour.ink) {
    g.lineStyle(2.5, line, 0.5).beginPath().arc(cx, cy, r, Math.PI, 0).strokePath();
    g.lineStyle(2.5, line, 0.5).lineBetween(cx - r - 4, cy, cx + r + 4, cy);
    if (phase === 'night') {
        g.fillStyle(colour.cream, 1).fillCircle(cx, cy - r * 0.62, r * 0.5);
        g.fillStyle(bg, 1).fillCircle(cx + r * 0.28, cy - r * 0.82, r * 0.46);
        return;
    }
    const a = (SUN_ANGLE[phase] * Math.PI) / 180;
    g.fillStyle(phase === 'evening' ? colour.cost : colour.pay, 1).fillCircle(cx + Math.cos(a) * r, cy - Math.sin(a) * r, r * 0.38);
}
