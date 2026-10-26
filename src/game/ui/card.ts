// Deck card style (art-bible §8): card fill, ink outline, rounded, optional meaning-coloured top band.
import type { GameObjects } from 'phaser';
import { cardStyle, colour } from '../theme';

export function drawCard(g: GameObjects.Graphics, x: number, y: number, w: number, h: number, band?: number) {
    const { outline, radius } = cardStyle;
    g.fillStyle(colour.card, 1);
    g.fillRoundedRect(x, y, w, h, radius);
    if (band !== undefined) {
        g.fillStyle(band, 1);
        g.fillRoundedRect(x, y, w, cardStyle.band + radius, { tl: radius, tr: radius, bl: 0, br: 0 });
        g.fillStyle(colour.card, 1);
        g.fillRect(x + outline / 2, y + cardStyle.band, w - outline, radius);
    }
    g.lineStyle(outline, colour.ink, 1);
    g.strokeRoundedRect(x, y, w, h, radius);
}

export function drawChip(g: GameObjects.Graphics, x: number, y: number, w: number, h: number, fill: number, stroke: number = colour.ink) {
    g.fillStyle(fill, 1);
    g.fillRoundedRect(x, y, w, h, 6);
    g.lineStyle(2, stroke, 1);
    g.strokeRoundedRect(x, y, w, h, 6);
}

// The HUD's own corners: the clock and prompt band along the top, the docked tag and the i/menu
// buttons at the top right. A card placed from an anchor must not land on them.
const HUD_BOTTOM = 104;
const DOCK = { left: 1520, bottom: 176 };

/** Nudge a card centred at (c.x, c.y), w × h, down out of the HUD band and clear of the docked tag. */
export function keepClear(c: { x: number; y: number; setY(y: number): unknown }, w: number, h: number) {
    let top = Math.max(c.y - h / 2, HUD_BOTTOM);
    if (c.x + w / 2 > DOCK.left) top = Math.max(top, DOCK.bottom);
    c.setY(top + h / 2);
}
