// The objective card, top left: which station this is (number badge, title, time of day), what to do
// now in big type with its keys (and the mouse, when the step takes one), and one dot per step of the
// beat's how-to (howto.json) so the player sees how far through the minigame they are. Stations call
// show(text, key) as before; the dots move on when the text is one of a later step's prompts.
import { GameObjects, Scene } from 'phaser';
import type { ClockPhase, MouseHint } from '../content';
import { getState } from '../state';
import { colour, css, font, hud, motion } from '../theme';
import { drawPhaseIcon, phaseLabel } from './Clock';
import { drawPanel, inputRow } from './keys';

export interface PromptStep { label: string; match: string[]; mouse?: MouseHint }
export interface PromptInfo { badge?: string; title?: string; phase?: ClockPhase; steps?: PromptStep[] }

const PAD = 22;
const HEAD_Y = 30;          // header row centre
const ROW_Y = 88;           // objective row centre (with a header)
const KEY_H = 38;

/** "Arrows" → the four arrow keys, "← →" → two keys, "Space" → one. */
function keysFor(hint?: string): string[] {
    if (!hint) return [];
    if (hint === 'Arrows') return ['←', '↑', '↓', '→'];
    return hint.split(' ').filter(Boolean);
}

export class Prompt extends GameObjects.Container {
    private bg: GameObjects.Graphics;
    private headerW = 0;
    private chevron: GameObjects.Text;
    private label: GameObjects.Text;
    private keys?: GameObjects.Container;
    private dots: GameObjects.Arc[] = [];
    private ticks: GameObjects.Text[] = [];
    private stepCount?: GameObjects.Text;
    private step = -1;
    private keyHint?: string;
    /** Called when the step dots move on: (step, of n). The owner shows "Level complete" on the last. */
    onStep?: (step: number, n: number) => void;
    private readonly rowY: number;
    private readonly h: number;

    constructor(scene: Scene, x: number, y: number, private info: PromptInfo = {}) {
        super(scene, x, y);
        this.bg = scene.add.graphics();
        this.add(this.bg);
        this.rowY = info.title ? ROW_Y : 33;
        this.h = info.title ? 122 : 66;
        if (info.title) this.buildHeader();
        this.chevron = scene.add.text(PAD, this.rowY, '▶', { fontFamily: font.display, fontSize: 22, color: css.pay }).setOrigin(0, 0.5);
        this.label = scene.add.text(PAD + 30, this.rowY, '', { fontFamily: font.display, fontSize: 34, fontStyle: '700', color: css.cream }).setOrigin(0, 0.5);
        this.add([this.chevron, this.label]);
        this.setDepth(50);
        scene.add.existing(this);
    }

    /** The key(s) the current objective asks for, as passed to show(). */
    get key() {
        return this.keyHint;
    }

    private buildHeader() {
        const s = this.scene, { badge, title, phase, steps } = this.info;
        const head = s.add.container(0, 0);
        const g = s.add.graphics();
        let x = PAD;
        if (badge) {
            g.fillStyle(colour.pay, 1).fillCircle(x + 19, HEAD_Y, 19).lineStyle(2.5, colour.ink, 1).strokeCircle(x + 19, HEAD_Y, 19);
            head.add(g);
            head.add(s.add.text(x + 19, HEAD_Y + 1, badge, { fontFamily: font.display, fontSize: badge.length > 2 ? 15 : 21, fontStyle: '800', color: css.ink }).setOrigin(0.5));
            x += 50;
        } else head.add(g);
        const t = s.add.text(x, HEAD_Y + 1, title!.toUpperCase(), { fontFamily: font.display, fontSize: 21, fontStyle: '700', color: css.cream })
            .setOrigin(0, 0.5).setLetterSpacing(1.5);
        head.add(t);
        x += t.width;
        if (phase) {
            x += 22;
            drawPhaseIcon(g, x + 16, HEAD_Y + 7, phase, 12, colour.cream, hud.panel);
            const pl = s.add.text(x + 38, HEAD_Y + 1, phaseLabel(phase), { fontFamily: font.body, fontSize: 20, color: hud.dim }).setOrigin(0, 0.5);
            head.add(pl);
            x += 38 + pl.width;
        }
        if (steps?.length) {
            x += 30;
            this.stepCount = s.add.text(x, HEAD_Y + 1, '', { fontFamily: font.display, fontSize: 18, fontStyle: '700', color: hud.dim }).setOrigin(0, 0.5).setLetterSpacing(1);
            head.add(this.stepCount);
            x += 84;
            steps.forEach((_, i) => {
                const d = s.add.circle(x + 10 + i * 26, HEAD_Y, 8).setStrokeStyle(2.5, colour.cream, 0.35);
                const tick = s.add.text(d.x, HEAD_Y, '✓', { fontFamily: font.display, fontSize: 13, fontStyle: '800', color: css.ink }).setOrigin(0.5).setVisible(false);
                this.dots.push(d);
                this.ticks.push(tick);
                head.add([d, tick]);
            });
            x += steps.length * 26;
        }
        g.lineStyle(1.5, colour.cream, 0.12).lineBetween(PAD, HEAD_Y + 26, x, HEAD_Y + 26);
        this.headerW = x;
        this.add(head);
    }

    show(text: string, keyHint?: string) {
        const changed = text !== this.label.text;
        this.keyHint = keyHint;
        this.label.setText(text);
        const steps = this.info.steps ?? [];
        const at = steps.findIndex((st) => st.match.includes(text));
        if (at >= 0) this.setStep(at);
        const mouse = steps[this.step]?.mouse;

        this.keys?.destroy();
        // "Wait" (s02, the handcart) is not a key: the objective says it all
        const keys = keysFor(keyHint);
        this.keys = keyHint !== 'Wait' && (keys.length || mouse) ? inputRow(this.scene, keys, mouse, KEY_H) : undefined;
        let right = this.label.x + this.label.width;
        if (this.keys) {
            this.keys.setPosition(right + 28 + this.keys.width / 2, this.rowY - 2);
            this.add(this.keys);
            right += 28 + this.keys.width;
        }
        const w = Math.max(right, this.headerW) + PAD;
        this.bg.clear();
        drawPanel(this.bg, 0, 0, w, this.h);
        this.bg.fillStyle(colour.pay, 1).fillRoundedRect(0, this.rowY - 22, 6, 44, { tl: 0, bl: 0, tr: 3, br: 3 });

        if (!changed || getState(this.scene).reducedMotion) return;
        const row = [this.chevron, this.label, ...(this.keys ? [this.keys] : [])];
        row.forEach((o) => {
            const x = o.x;
            o.setAlpha(0).setX(x - 16);
            this.scene.tweens.add({ targets: o, alpha: 1, x, duration: motion.normal, ease: 'Cubic.easeOut' });
        });
        this.scene.tweens.add({ targets: this.chevron, scale: { from: 1.6, to: 1 }, duration: motion.normal + 120, ease: 'Back.easeOut' });
    }

    private setStep(i: number) {
        if (i === this.step) return;
        const prev = this.step;
        this.step = i;
        const n = this.dots.length;
        this.stepCount?.setText(`STEP ${i + 1}/${n}`);
        this.onStep?.(i, n);
        this.dots.forEach((d, k) => {
            const done = k < i, now = k === i;
            d.setFillStyle(done ? colour.pay : now ? colour.cream : colour.ink, done || now ? 1 : 0)
                .setStrokeStyle(2.5, done ? colour.pay : colour.cream, done || now ? 1 : 0.35);
            this.ticks[k].setVisible(done);
            const popped = prev >= 0 && k >= prev && k <= i;      // the steps just finished, and the new one
            if (popped && !getState(this.scene).reducedMotion) {
                this.scene.tweens.add({ targets: [d, this.ticks[k]], scale: { from: 1.7, to: 1 }, duration: 320, ease: 'Back.easeOut' });
            }
        });
    }
}
