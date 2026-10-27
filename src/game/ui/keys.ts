// Input glyphs for the HUD and briefings: a key cap (a cream key with a lip, so it reads as a key you
// press), a mouse with its left button lit, and a row of both. Each is a Container centred on (0, 0)
// whose width is set, so callers can lay them out.
import { GameObjects, Scene } from 'phaser';
import type { MouseHint } from '../content';
import { colour, css, font, hud } from '../theme';

export function keycap(scene: Scene, label: string, h = 40): GameObjects.Container {
    // Baloo's arrows are hairlines: arrow keys take a system font, larger
    const arrow = /^[←↑↓→]$/.test(label);
    const t = scene.add.text(0, arrow ? -3 : -2, label, {
        fontFamily: arrow ? 'Arial, system-ui, sans-serif' : font.display, fontSize: Math.round(h * (arrow ? 0.62 : 0.5)), fontStyle: arrow ? '900' : '700', color: css.ink,
    }).setOrigin(0.5);
    const w = Math.max(h, t.width + h * 0.7);
    const g = scene.add.graphics();
    const r = Math.min(9, h / 4);
    g.fillStyle(hud.keyLip, 1).fillRoundedRect(-w / 2, -h / 2 + 4, w, h, r);
    g.fillStyle(colour.cream, 1).fillRoundedRect(-w / 2, -h / 2, w, h - 4, r);
    g.lineStyle(2.5, colour.ink, 1).strokeRoundedRect(-w / 2, -h / 2, w, h + 4, r);
    return scene.add.container(0, 0, [g, t]).setSize(w, h);
}

/** A mouse, left button lit in saffron; "drag" adds a motion arrow, "hold" a press ring. */
export function mouseGlyph(scene: Scene, kind: MouseHint, h = 40): GameObjects.Container {
    const w = h * 0.68;
    const g = scene.add.graphics();
    g.fillStyle(colour.cream, 1).fillRoundedRect(-w / 2, -h / 2, w, h, w / 2);
    g.fillStyle(colour.pay, 1).fillRoundedRect(-w / 2, -h / 2, w / 2, h * 0.42, { tl: w / 2, tr: 0, bl: 0, br: 0 });
    g.lineStyle(2.5, colour.ink, 1).strokeRoundedRect(-w / 2, -h / 2, w, h, w / 2);
    g.lineStyle(2, colour.ink, 1).lineBetween(0, -h / 2, 0, -h / 2 + h * 0.42).lineBetween(-w / 2, -h / 2 + h * 0.42, w / 2, -h / 2 + h * 0.42);
    const parts: GameObjects.GameObject[] = [g];
    let width = w;
    if (kind === 'drag') {
        const a = scene.add.graphics();
        const x0 = w / 2 + 6, x1 = x0 + h * 0.5;
        a.lineStyle(3, colour.cream, 1).lineBetween(x0, 0, x1, 0);
        a.fillStyle(colour.cream, 1).fillTriangle(x1 + 6, 0, x1 - 2, -6, x1 - 2, 6);
        a.setX(-(x1 + 6 - w / 2) / 2);
        g.setX(-(x1 + 6 - w / 2) / 2);
        parts.push(a);
        width = x1 + 6 + w / 2;
    } else if (kind === 'hold') {
        g.lineStyle(2, colour.pay, 0.9).strokeCircle(-w / 4, -h / 2 + h * 0.21, h * 0.32);
    }
    return scene.add.container(0, 0, parts).setSize(width, h);
}

/** Keys joined by thin gaps, then "or" and the mouse, on one line; arrows are grouped as one cluster.
 * `light` sets the "or" for a cream card instead of a dark panel. */
export function inputRow(scene: Scene, keys: string[], mouse?: MouseHint, h = 40, light = false): GameObjects.Container {
    const items: GameObjects.Container[] = keys.map((k) => keycap(scene, k, h));
    const row = scene.add.container(0, 0);
    let x = 0;
    const place = (o: GameObjects.Container | GameObjects.Text, w: number, gap: number) => {
        o.setX(x + w / 2);
        row.add(o);
        x += w + gap;
    };
    items.forEach((k) => place(k, k.width, 6));
    if (mouse) {
        if (items.length) {
            x += 4;
            const or = scene.add.text(0, 0, 'or', { fontFamily: font.body, fontSize: Math.round(h * 0.48), color: light ? css.muted : hud.dim }).setOrigin(0.5);
            place(or, or.width, 10);
        }
        const m = mouseGlyph(scene, mouse, h);
        place(m, m.width, 0);
    } else if (items.length) x -= 6;
    row.list.forEach((o) => (o as GameObjects.Container).setX((o as GameObjects.Container).x - x / 2));
    return row.setSize(Math.max(x, 0), h);
}

/** A dark HUD panel with a soft drop shadow. */
export function drawPanel(g: GameObjects.Graphics, x: number, y: number, w: number, h: number, r = 16, alpha: number = hud.panelAlpha) {
    g.fillStyle(hud.shadow, 0.3).fillRoundedRect(x, y + 5, w, h, r);
    g.fillStyle(hud.panel, alpha).fillRoundedRect(x, y, w, h, r);
    g.lineStyle(2, colour.cream, 0.14).strokeRoundedRect(x + 1, y + 1, w - 2, h - 2, r - 1);
}
