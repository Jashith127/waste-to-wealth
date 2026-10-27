// Deck card style (art-bible §8): card fill, rounded, ink outline or a meaning-coloured one, hard shadow.
import type { GameObjects } from 'phaser';
import { cardStyle, colour, layout } from '../theme';

export function drawCard(g: GameObjects.Graphics, x: number, y: number, w: number, h: number, accent?: number) {
    const { outline, radius } = cardStyle;
    // a sticker: hard ink shadow, cream face, and the meaning colour as the outline (no top stripe)
    g.fillStyle(colour.ink, 0.28);
    g.fillRoundedRect(x + 2, y + 6, w, h, radius);
    g.fillStyle(colour.card, 1);
    g.fillRoundedRect(x, y, w, h, radius);
    g.lineStyle(accent !== undefined ? outline + 1 : outline, accent ?? colour.ink, 1);
    g.strokeRoundedRect(x, y, w, h, radius);
}

export function drawChip(g: GameObjects.Graphics, x: number, y: number, w: number, h: number, fill: number, stroke: number = colour.ink) {
    g.fillStyle(fill, 1);
    g.fillRoundedRect(x, y, w, h, 6);
    g.lineStyle(2, stroke, 1);
    g.strokeRoundedRect(x, y, w, h, 6);
}

// The HUD's own corners: the objective card along the top left, the docked tag at the top right.
// A card placed from an anchor must not land on them.
const HUD_BOTTOM = layout.hudBottom;
const DOCK = { left: 1520, bottom: 190 };

/** Nudge a card centred at (c.x, c.y), w × h, down out of the HUD band and clear of the docked tag. */
export function keepClear(c: { x: number; y: number; setY(y: number): unknown }, w: number, h: number) {
    let top = Math.max(c.y - h / 2, HUD_BOTTOM);
    if (c.x + w / 2 > DOCK.left) top = Math.max(top, DOCK.bottom);
    c.setY(top + h / 2);
}
