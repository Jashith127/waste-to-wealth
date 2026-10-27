// A story card in the world: what just happened and why, as a headline, a sentence, and a chain of
// cause → effect links, each with a small drawn icon, popping in one after another. Used where a tag
// alone would leave the player guessing (s01: why the kilo costs money, why the leftovers are lost).
// Text from the station's data; the icons are drawn here, no emoji.
import { GameObjects, Scene } from 'phaser';
import { getState } from '../state';
import { colour, css, font } from '../theme';
import { drawCard } from './card';

export type StoryIcon = 'power_off' | 'cold_off' | 'rot' | 'loss' | 'bone' | 'no_sale' | 'fee';
export interface Story { title: string; body: string; chain?: { icon: StoryIcon; text: string }[] }

const W = 640;
const LINK_W = 150;

export class StoryCard extends GameObjects.Container {
    constructor(scene: Scene, x: number, y: number, story: Story, accent: number = colour.cost) {
        super(scene, x, y);
        const still = getState(scene).reducedMotion;
        const pad = 32;
        const title = scene.add.text(-W / 2 + pad, 0, story.title, { fontFamily: font.display, fontSize: 36, fontStyle: '800', color: css.ink });
        const body = scene.add.text(-W / 2 + pad, 0, story.body, { fontFamily: font.body, fontSize: 24, color: css.ink, wordWrap: { width: W - pad * 2 }, lineSpacing: 4 });
        const chain = story.chain ?? [];
        const chainH = chain.length ? 150 : 0;
        const h = pad + title.height + 8 + body.height + (chainH ? 22 + chainH : 0) + pad - 6;
        const top = -h / 2;
        title.setY(top + pad - 6);
        body.setY(title.y + title.height + 6);

        const g = scene.add.graphics();
        drawCard(g, -W / 2, top, W, h, accent);
        this.add([g, title, body]);

        // the chain: icon tiles joined by arrows
        const cy = body.y + body.height + 22 + 54;
        const step = chain.length > 1 ? (W - pad * 2 - LINK_W) / (chain.length - 1) : 0;
        chain.forEach((link, i) => {
            const lx = -W / 2 + pad + LINK_W / 2 + i * step;
            const tile = scene.add.container(lx, cy);
            const tg = scene.add.graphics();
            tg.fillStyle(colour.cream, 1).fillRoundedRect(-44, -44, 88, 88, 18);
            tg.lineStyle(2.5, i === chain.length - 1 ? accent : colour.ink, 1).strokeRoundedRect(-44, -44, 88, 88, 18);
            drawIcon(tg, link.icon);
            const t = scene.add.text(0, 58, link.text, {
                fontFamily: font.display, fontSize: 19, fontStyle: '700', color: i === chain.length - 1 ? css.cost : css.ink, align: 'center', wordWrap: { width: LINK_W },
            }).setOrigin(0.5, 0);
            tile.add([tg, t]);
            this.add(tile);
            if (i < chain.length - 1) {
                const ax = lx + 52, bx = lx + step - 52;
                const arrow = scene.add.graphics();
                arrow.lineStyle(3, colour.ink, 0.7).lineBetween(ax, cy, bx - 8, cy);
                arrow.fillStyle(colour.ink, 0.7).fillTriangle(bx, cy, bx - 10, cy - 7, bx - 10, cy + 7);
                this.add(arrow);
                if (!still) { arrow.setAlpha(0); scene.tweens.add({ targets: arrow, alpha: 1, duration: 200, delay: 500 + i * 450 + 250 }); }
            }
            if (!still) {
                tile.setScale(0);
                scene.tweens.add({ targets: tile, scale: 1, duration: 320, delay: 500 + i * 450, ease: 'Back.easeOut' });
            }
        });

        this.setDepth(36);
        scene.add.existing(this);
        if (!still) {
            this.setAlpha(0).setScale(0.92);
            scene.tweens.add({ targets: this, alpha: 1, scale: 1, duration: 280, ease: 'Back.easeOut' });
        }
    }
}

/** A 60 px icon centred on (0, 0), in ink with one meaning colour where it helps. */
function drawIcon(g: GameObjects.Graphics, icon: StoryIcon) {
    const ink = colour.ink;
    const slash = () => g.lineStyle(6, colour.cost, 1).lineBetween(-24, -24, 24, 24);
    switch (icon) {
        case 'power_off':   // a lightning bolt, struck through
            g.fillStyle(colour.pay, 1).lineStyle(2.5, ink, 1);
            g.beginPath().moveTo(6, -28).lineTo(-14, 4).lineTo(0, 4).lineTo(-6, 28).lineTo(14, -6).lineTo(0, -6).lineTo(6, -28).closePath().fillPath().strokePath();
            slash();
            break;
        case 'cold_off':    // a snowflake, struck through
            g.lineStyle(4, colour.offsite, 1);
            for (let a = 0; a < 3; a++) {
                const r = (a * Math.PI) / 3, dx = Math.cos(r) * 24, dy = Math.sin(r) * 24;
                g.lineBetween(-dx, -dy, dx, dy);
            }
            g.fillStyle(colour.offsite, 1).fillCircle(0, 0, 5);
            slash();
            break;
        case 'rot':         // a cut of meat gone grey, with stink lines
            g.fillStyle(0x9a8f84, 1).lineStyle(2.5, ink, 1);
            g.fillEllipse(0, 12, 50, 30).strokeEllipse(0, 12, 50, 30);
            g.fillStyle(0x6f8a4e, 1).fillCircle(-8, 10, 5).fillCircle(9, 15, 4);
            g.lineStyle(3, 0x6f8a4e, 1);
            for (const x of [-12, 0, 12]) {
                g.beginPath().moveTo(x, -6).lineTo(x - 4, -14).lineTo(x + 4, -22).lineTo(x, -30).strokePath();
            }
            break;
        case 'loss':        // a rupee coin with a minus
            g.fillStyle(colour.cost, 1).fillCircle(0, 0, 26).lineStyle(2.5, ink, 1).strokeCircle(0, 0, 26);
            g.lineStyle(5, colour.cream, 1).lineBetween(-13, 0, 13, 0);
            break;
        case 'bone':        // a bone
            g.fillStyle(0xf1e6d2, 1).lineStyle(2.5, ink, 1);
            g.fillRect(-18, -6, 36, 12);
            for (const [x, y] of [[-20, -8], [-20, 8], [20, -8], [20, 8]]) g.fillCircle(x, y, 9).strokeCircle(x, y, 9);
            g.fillRect(-18, -6, 36, 12);
            g.lineBetween(-16, -6, 16, -6).lineBetween(-16, 6, 16, 6);
            break;
        case 'no_sale':     // a price tag with a cross
            g.fillStyle(colour.card, 1).lineStyle(2.5, ink, 1);
            g.beginPath().moveTo(-22, -14).lineTo(10, -14).lineTo(24, 0).lineTo(10, 14).lineTo(-22, 14).closePath().fillPath().strokePath();
            g.fillStyle(ink, 1).fillCircle(10, 0, 3);
            g.lineStyle(4, colour.cost, 1).lineBetween(-14, -8, 0, 8).lineBetween(0, -8, -14, 8);
            break;
        case 'fee':         // money going out: a note with an arrow leaving
            g.fillStyle(0xcfe0c4, 1).lineStyle(2.5, ink, 1).fillRect(-26, -14, 36, 28).strokeRect(-26, -14, 36, 28);
            g.strokeCircle(-8, 0, 7);
            g.lineStyle(4, colour.cost, 1).lineBetween(14, 0, 26, 0);
            g.fillStyle(colour.cost, 1).fillTriangle(30, 0, 22, -7, 22, 7);
            break;
    }
}
