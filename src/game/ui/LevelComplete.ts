// "Level complete!": when a beat's last step comes up, a saffron ribbon slams in at the bottom centre
// with every step ticked off, a burst of confetti, and one Continue button (with its key) that takes
// the player on. Replaces the stations' own "Walk on →" buttons. The last beat of a run says so.
import { GameObjects, Math as PMath, Scene } from 'phaser';
import { howTo, runs } from '../content';
import { getState, type Run } from '../state';
import { isPhone } from '../device';
import { colour, css, font, FRAME, hud } from '../theme';
import { drawPanel, keycap, touchChip } from './keys';

export interface LevelInfo {
    level: number;          // the beat's place in its run, from 1
    runEnd?: string;        // e.g. "Run 1": the heading becomes "Run 1 complete!"
    title: string;          // the station's title, under the ribbon
    steps: string[];        // step labels, all ticked
    cta: string;            // the button's word, e.g. "Walk on"
    key: string;            // the key that does the same, e.g. "→"
}

/** The card's content for beat `index` of `run`, from howto.json; undefined if the beat has none. */
export function levelInfo(run: Run, index: number, title: string): LevelInfo | undefined {
    const beats = runs[run].beats;
    const how = howTo(run, beats[index]);
    if (!how) return undefined;
    const last = how.steps[how.steps.length - 1];
    return {
        level: index + 1,
        runEnd: index === beats.length - 1 ? runs[run].title.split(' · ')[0] : undefined,
        title,
        steps: how.steps.slice(0, -1).map((st) => st.label),
        cta: last.label,
        key: last.keys[0] ?? '→',
    };
}

const Y = 852;             // centre of the panel: above the control dock, below the action
const CONFETTI = [colour.pay, colour.cost, colour.income, colour.offsite, colour.cream];

export class LevelComplete extends GameObjects.Container {
    constructor(scene: Scene, info: LevelInfo, onGo: () => void) {
        super(scene, FRAME.width / 2, Y);
        const still = getState(scene).reducedMotion;
        if (isPhone()) this.setScale(1.45);      // FIT shrinks the frame to a third on a phone

        // the panel: the station's title, the ticked steps, the button
        const title = scene.add.text(0, -18, info.title, { fontFamily: font.body, fontSize: 24, color: hud.dim }).setOrigin(0.5);
        const chips = info.steps.map((label) => {
            const t = scene.add.text(20, 0, label, { fontFamily: font.display, fontSize: 26, fontStyle: '700', color: css.cream }).setOrigin(0, 0.5);
            const g = scene.add.graphics();
            g.fillStyle(colour.pay, 1).fillCircle(0, 0, 14);
            const tick = scene.add.text(0, 1, '✓', { fontFamily: font.display, fontSize: 18, fontStyle: '800', color: css.ink }).setOrigin(0.5);
            const c = scene.add.container(0, 26, [g, tick, t]);
            return { c, w: 20 + t.width };
        });
        const chipsW = chips.reduce((a, ch) => a + ch.w + 36, -36) + 14;
        let x = -chipsW / 2 + 14;
        chips.forEach((ch) => { ch.c.setX(x); x += ch.w + 36; });

        const button = this.button(info.cta, info.key, onGo);
        const w = Math.max(760, chipsW + 120, title.width + 120), h = 230;
        const bg = scene.add.graphics();
        drawPanel(bg, -w / 2, -h / 2 + 18, w, h, 22, 0.94);
        bg.lineStyle(3, colour.pay, 0.9).strokeRoundedRect(-w / 2, -h / 2 + 18, w, h, 22);
        button.setY(h / 2 - 34);

        // the ribbon across the top edge, its tails folded behind
        const heading = (info.runEnd ? `${info.runEnd} complete!` : `Level ${info.level} complete!`).toUpperCase();
        const ht = scene.add.text(0, -h / 2 + 4, heading, { fontFamily: font.display, fontSize: 52, fontStyle: '800', color: css.ink })
            .setOrigin(0.5).setLetterSpacing(2);
        const rw = ht.width + 120, rh = 78, ry = -h / 2 + 4;
        const ribbon = scene.add.graphics();
        for (const s of [-1, 1]) {
            const tx = s * (rw / 2 - 10);
            const tail = [[tx, ry - rh / 2 + 14], [tx + s * 70, ry - rh / 2 + 14], [tx + s * 46, ry + 10], [tx + s * 70, ry + rh / 2 + 14], [tx, ry + rh / 2 + 14]];
            ribbon.fillStyle(0xb8761a, 1).fillPoints(tail.map(([px, py]) => new PMath.Vector2(px, py)), true);
        }
        ribbon.fillStyle(hud.shadow, 0.3).fillRoundedRect(-rw / 2, ry - rh / 2 + 6, rw, rh, 12);
        ribbon.fillStyle(colour.pay, 1).fillRoundedRect(-rw / 2, ry - rh / 2, rw, rh, 12);
        ribbon.lineStyle(4, colour.ink, 1).strokeRoundedRect(-rw / 2, ry - rh / 2, rw, rh, 12);
        const banner = scene.add.container(0, 0, [ribbon, ht]);

        this.add([bg, title, ...chips.map((ch) => ch.c), button, banner]);
        this.setDepth(70);
        scene.add.existing(this);
        if (still) return;

        // slam in: the panel rises, the ribbon bounces down onto it, the ticks pop one by one
        this.setAlpha(0).setY(Y + 40);
        scene.tweens.add({ targets: this, alpha: 1, y: Y, duration: 260, ease: 'Cubic.easeOut' });
        banner.setScale(2.2).setAlpha(0);
        scene.tweens.add({ targets: banner, scale: 1, alpha: 1, duration: 420, delay: 120, ease: 'Back.easeOut', onComplete: () => this.confetti(ry) });
        chips.forEach((ch, i) => {
            ch.c.setScale(0);
            scene.tweens.add({ targets: ch.c, scale: 1, duration: 260, delay: 420 + i * 130, ease: 'Back.easeOut' });
        });
        scene.tweens.add({ targets: button, scale: { from: 1, to: 1.05 }, duration: 650, yoyo: true, repeat: -1, delay: 900, ease: 'Sine.easeInOut' });
    }

    private button(cta: string, key: string, onGo: () => void) {
        const s = this.scene;
        const phone = isPhone();
        const t = s.add.text(0, 0, `${cta}  ▶`, { fontFamily: font.display, fontSize: 34, fontStyle: '800', color: css.ink }).setOrigin(0, 0.5);
        const cap = phone ? touchChip(s, 'tap', 44) : keycap(s, key, 36);
        const bw = t.width + cap.width + 76, bh = 68;
        const bg = s.add.graphics();
        const draw = (hover: boolean) => {
            bg.clear().fillStyle(0xb8761a, 1).fillRoundedRect(-bw / 2, -bh / 2 + 6, bw, bh, bh / 2);
            bg.fillStyle(hover ? 0xffbe45 : colour.pay, 1).fillRoundedRect(-bw / 2, -bh / 2, bw, bh, bh / 2);
            bg.lineStyle(3, colour.ink, 1).strokeRoundedRect(-bw / 2, -bh / 2, bw, bh, bh / 2);
        };
        draw(false);
        t.setX(-bw / 2 + 32);
        cap.setPosition(bw / 2 - 30 - cap.width / 2, -2);
        const b = s.add.container(0, 0, [bg, t, cap]).setSize(bw, bh);
        let gone = false;
        b.setInteractive({ useHandCursor: true })
            .on('pointerover', () => draw(true)).on('pointerout', () => draw(false))
            .on('pointerup', () => { if (!gone) { gone = true; onGo(); } });
        return b;
    }

    /** A burst of paper from the ribbon, falling under gravity, gone in a second and a half. */
    private confetti(y: number) {
        const s = this.scene;
        for (let i = 0; i < 46; i++) {
            const bit = s.add.rectangle(this.x + PMath.Between(-120, 120), this.y + y * this.scaleY, PMath.Between(8, 14), PMath.Between(5, 9), CONFETTI[i % CONFETTI.length])
                .setDepth(71).setAngle(PMath.Between(0, 180));
            const vx = PMath.FloatBetween(-620, 620), vy = PMath.FloatBetween(-760, -260), spin = PMath.Between(-540, 540);
            const x0 = bit.x, y0 = bit.y, p = { t: 0 };
            s.tweens.add({
                targets: p, t: 1.5, duration: 1500, ease: 'Linear',
                onUpdate: () => bit.setPosition(x0 + vx * p.t * 0.6, y0 + vy * p.t + 900 * p.t * p.t).setAngle(spin * p.t).setAlpha(Math.min(1, 1.6 - p.t)),
                onComplete: () => bit.destroy(),
            });
        }
    }
}
