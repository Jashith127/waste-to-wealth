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
