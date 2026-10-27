// End card (after Run 2): the kilo's ledger for both runs, then the four before → after beliefs one at a
// time, then "Play again". Framed as the deck's arch-shaped municipal signboard (deck p. 1, art-bible §8):
// saffron board, red edging, ink text. The one place the meaning colours are decoration.
import { GameObjects, Math as PMath, Scene } from 'phaser';
import endcard from '../../data/endcard.json';
import { parseBeat } from '../flow';
import { getState, setState } from '../state';
import { colour, css, font, FRAME, motion, type Meaning } from '../theme';
import { drawCard, drawChip } from '../ui/card';
import { keycap } from '../ui/keys';

type Column = { heading: string; proposed?: boolean; lines: { text: string; value: string; meaning: string }[] };

const PANEL = { x: 176, y: 268, w: 1568, h: 752 };
const BELIEF_Y = 710;
const BELIEF_STEP = 66;
const NOTE_Y = 576;           // the estimate strip, between the ledger and the beliefs

export class EndCard extends Scene {
    private beliefs: GameObjects.Container[] = [];
    private shown = 0;
    private nextHint!: GameObjects.Container;
    private replay!: GameObjects.Container;
    private leaving = false;

    constructor() {
        super('EndCard');
    }

    create() {
        const { reducedMotion } = getState(this);
        this.beliefs = [];
        this.shown = 0;
        this.leaving = false;
        this.add.tileSprite(0, 0, FRAME.width, FRAME.height, 'lattice').setOrigin(0);
        this.drawSignboard();

        this.add.text(FRAME.width / 2, 184, endcard.title, {
            fontFamily: font.display, fontSize: 64, fontStyle: '800', color: css.ink,
        }).setOrigin(0.5);

        this.ledgerColumn(PANEL.x + 32, endcard.ledger['1'], colour.cost);
        this.ledgerColumn(PANEL.x + PANEL.w / 2 + 16, endcard.ledger['2'], colour.income);
        this.versus();
        this.estimateNote();
        this.add.text(FRAME.width / 2, BELIEF_Y - 52, endcard.beliefs_heading.toUpperCase(), {
            fontFamily: font.display, fontSize: 22, fontStyle: '800', color: css.brown,
        }).setOrigin(0.5).setLetterSpacing(3);

        endcard.beliefs.forEach((b, i) => this.beliefs.push(this.beliefRow(i + 1, b.before, b.after, BELIEF_Y + i * BELIEF_STEP)));
        this.nextHint = this.keyHint('Space');
        this.replay = this.button(endcard.replay, FRAME.width / 2, 985, () => this.playAgain());
        this.replay.setVisible(false);
        this.placeHint();

        this.input.keyboard!.on('keydown-SPACE', () => this.advance(reducedMotion));
        this.input.keyboard!.on('keydown-ENTER', () => this.replay.visible && this.playAgain());
        // A click on the board (not the button) advances too.
        this.input.on('pointerdown', (p: { x: number; y: number }, over: GameObjects.GameObject[]) => {
            if (over.length === 0 && p.x > 128 && p.x < 1792 && p.y > 236) this.advance(reducedMotion);
        });

        (window as unknown as { __ready?: string }).__ready = 'end';
        if (!reducedMotion) this.cameras.main.fadeIn(motion.transition, 28, 23, 20);
    }

    /** Arch signboard after deck p. 1: two posts, a stepped crest and the main board with red edging. */
    private drawSignboard() {
        const g = this.add.graphics();
        const ink = (w: number) => g.lineStyle(w, colour.ink, 1);
        // Posts
        for (const x of [72, 1768]) {
            g.fillStyle(colour.pay, 1).fillRect(x, 150, 80, 900);
            ink(4).strokeRect(x, 150, 80, 900);
            ink(4).lineBetween(x, 184, x + 80, 184);
            g.fillStyle(colour.cost, 1).fillRoundedRect(x + 26, 300, 28, 220, 8);
        }
        // Crest: a stepped gable rising to a peak, red edge inside an ink outline.
        const crest = [
            [470, 250], [500, 196], [540, 186], [790, 104], [850, 100], [960, 40],
            [1070, 100], [1130, 104], [1380, 186], [1420, 196], [1450, 250],
        ].map(([x, y]) => new PMath.Vector2(x, y));
        ink(22).strokePoints(crest, true);
        g.lineStyle(12, colour.cost, 1).strokePoints(crest, true);
        g.fillStyle(colour.pay, 1).fillPoints(crest, true);
        // Sun disc at the peak, as on the board's emblem.
        g.fillStyle(colour.cost, 1).slice(960, 92, 30, Math.PI, 0, false).fillPath();
        // Main board
        g.fillStyle(colour.pay, 1).fillRoundedRect(128, 236, 1664, 816, 18);
        g.lineStyle(12, colour.cost, 1).strokeRoundedRect(140, 248, 1640, 792, 14);
        ink(5).strokeRoundedRect(128, 236, 1664, 816, 18);
        // Cream panel the text sits on
        drawCard(g, PANEL.x, PANEL.y, PANEL.w, PANEL.h);
    }

    private ledgerColumn(x: number, col: Column, band: number) {
        const w = PANEL.w / 2 - 48, y = PANEL.y + 28, h = 224;
        const g = this.add.graphics();
        drawCard(g, x, y, w, h, band);
        this.add.text(x + 28, y + 52, col.heading, { fontFamily: font.display, fontSize: 38, fontStyle: '700', color: css.ink }).setOrigin(0, 0.5);
        if (col.proposed) {
            const t = this.add.text(0, y + 52, 'Proposed', { fontFamily: font.display, fontSize: 26, fontStyle: '700', color: css.cream }).setOrigin(0, 0.5);
            const cw = t.width + 28;
            t.setX(x + w - 28 - cw + 14);
            drawChip(g, x + w - 28 - cw, y + 32, cw, 40, colour.brown);
            t.setDepth(1);
        }
        col.lines.forEach((line, i) => {
            const ly = y + 124 + i * 64;
            this.add.text(x + 28, ly, line.text, { fontFamily: font.body, fontSize: 30, color: css.ink }).setOrigin(0, 0.5);
            this.add.text(x + w - 28, ly, line.value, {
                fontFamily: font.display, fontSize: 42, fontStyle: '800', color: css[line.meaning as Meaning],
            }).setOrigin(1, 0.5);
            if (i > 0) g.lineStyle(2, colour.ink, 0.15).lineBetween(x + 28, ly - 32, x + w - 28, ly - 32);
        });
    }

    /** "VS" between the two ledgers: the same kilo, two endings. */
    private versus() {
        const x = FRAME.width / 2, y = PANEL.y + 28 + 112;
        const g = this.add.graphics();
        g.fillStyle(colour.ink, 0.28).fillCircle(x + 2, y + 5, 34);
        g.fillStyle(colour.pay, 1).fillCircle(x, y, 34).lineStyle(4, colour.ink, 1).strokeCircle(x, y, 34);
        this.add.text(x, y + 1, 'VS', { fontFamily: font.display, fontSize: 28, fontStyle: '800', color: css.ink }).setOrigin(0.5);
    }

    /** How the payout was estimated: its own strip with an "Estimate" chip, never mistaken for a quote. */
    private estimateNote() {
        const w = PANEL.w - 64, x = PANEL.x + 32;
        const chip = this.add.text(0, 0, endcard.estimate_label.toUpperCase(), { fontFamily: font.display, fontSize: 18, fontStyle: '800', color: css.cream })
            .setLetterSpacing(1.5).setOrigin(0, 0.5);
        const t = this.add.text(x + chip.width + 64, NOTE_Y, endcard.payout_note, {
            fontFamily: font.body, fontSize: 22, color: css.ink, wordWrap: { width: w - chip.width - 88 }, lineSpacing: 2,
        }).setOrigin(0, 0.5);
        const h = Math.max(64, t.height + 22);
        const g = this.add.graphics();
        g.fillStyle(colour.cream, 1).fillRoundedRect(x, NOTE_Y - h / 2, w, h, 12);
        g.lineStyle(2, colour.brown, 0.5).strokeRoundedRect(x, NOTE_Y - h / 2, w, h, 12);
        drawChip(g, x + 16, NOTE_Y - 16, chip.width + 28, 32, colour.brown, colour.brown);
        chip.setPosition(x + 30, NOTE_Y).setDepth(1);
        t.setDepth(1);
    }

    /** One belief: a numbered pill, the old belief (struck through as it shows) → the new one. */
    private beliefRow(n: number, before: string, after: string, y: number) {
        const cx = FRAME.width / 2, half = PANEL.w / 2 - 120, w = PANEL.w - 64;
        const row = this.add.container(0, y).setVisible(false);
        const g = this.add.graphics();
        g.fillStyle(colour.cream, 1).fillRoundedRect(PANEL.x + 32, -27, w, 54, 27);
        g.fillStyle(colour.ink, 1).fillCircle(PANEL.x + 62, 0, 18);
        const num = this.add.text(PANEL.x + 62, 1, String(n), { fontFamily: font.display, fontSize: 22, fontStyle: '800', color: css.pay }).setOrigin(0.5);
        const was = this.add.text(cx - 56, 0, before, { fontFamily: font.body, fontSize: 26, color: css.muted, align: 'right', wordWrap: { width: half } }).setOrigin(1, 0.5);
        const strike = this.add.graphics();
        const arrow = this.add.text(cx, 0, '→', { fontFamily: font.display, fontSize: 40, fontStyle: '800', color: css.brown }).setOrigin(0.5, 0.55);
        const now = this.add.text(cx + 56, 0, after, { fontFamily: font.display, fontSize: 28, fontStyle: '700', color: css.income, wordWrap: { width: half } }).setOrigin(0, 0.5);
        row.add([g, num, was, strike, arrow, now]);
        row.setData('strike', () => {
            const x0 = was.x - was.width, x1 = was.x;
            const p = { t: 0 };
            const draw = () => strike.clear().lineStyle(3, colour.cost, 0.85).lineBetween(x0, 2, x0 + (x1 - x0) * p.t, 2);
            if (getState(this).reducedMotion) { p.t = 1; draw(); return; }
            this.tweens.add({ targets: p, t: 1, duration: 360, delay: 200, ease: 'Sine.easeOut', onUpdate: draw });
        });
        return row;
    }

    private keyHint(key: string) {
        const c = keycap(this, key, 40);
        if (!getState(this).reducedMotion) this.tweens.add({ targets: c, alpha: 0.45, duration: 700, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
        return c;
    }

    private placeHint() {
        this.nextHint.setPosition(FRAME.width / 2, BELIEF_Y + this.shown * BELIEF_STEP).setVisible(this.shown < this.beliefs.length);
    }

    /** The saffron game button, with its key. */
    private button(text: string, x: number, y: number, onClick: () => void) {
        const label = this.add.text(0, 0, `${text}  ▶`, { fontFamily: font.display, fontSize: 34, fontStyle: '800', color: css.ink }).setOrigin(0, 0.5);
        const cap = keycap(this, 'Enter', 36);
        const w = label.width + cap.width + 76, h = 70;
        const bg = this.add.graphics();
        const draw = (hover: boolean) => {
            bg.clear().fillStyle(0xb8761a, 1).fillRoundedRect(-w / 2, -h / 2 + 6, w, h, h / 2);
            bg.fillStyle(hover ? 0xffbe45 : colour.pay, 1).fillRoundedRect(-w / 2, -h / 2, w, h, h / 2);
            bg.lineStyle(3, colour.ink, 1).strokeRoundedRect(-w / 2, -h / 2, w, h, h / 2);
        };
        draw(false);
        label.setX(-w / 2 + 32);
        cap.setPosition(w / 2 - 30 - cap.width / 2, -2);
        const c = this.add.container(x, y, [bg, label, cap]).setSize(w, h).setInteractive({ useHandCursor: true });
        c.on('pointerover', () => draw(true)).on('pointerout', () => draw(false)).on('pointerup', onClick);
        if (!getState(this).reducedMotion) this.tweens.add({ targets: c, scale: 1.04, duration: 650, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
        return c;
    }

    /** Space or a click shows the next belief; after the fourth, "Play again". */
    private advance(reducedMotion: boolean) {
        if (this.shown >= this.beliefs.length) return;
        const row = this.beliefs[this.shown++].setVisible(true);
        (row.getData('strike') as () => void)();
        if (!reducedMotion) {
            row.setAlpha(0).setX(-24);
            this.tweens.add({ targets: row, alpha: 1, x: 0, duration: motion.normal, ease: 'Sine.easeOut' });
        }
        this.placeHint();
        if (this.shown === this.beliefs.length) this.replay.setVisible(true);
    }

    /** A clean Run 1 from beat 0: tag cleared, blueprint closed. */
    private playAgain() {
        if (this.leaving) return;
        this.leaving = true;
        const beat = parseBeat(1, 0);
        setState(this, { run: 1, beat: 0, station: beat.station, kilo: { carried: false, tag: null }, blueprintOpen: false });
        this.cameras.main.fadeOut(motion.transition, 28, 23, 20);
        this.cameras.main.once('camerafadeoutcomplete', () => this.scene.start('StationCard', { beat, runChanged: true }));
    }
}
