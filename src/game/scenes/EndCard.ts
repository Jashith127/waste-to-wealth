// End card (after Run 2): the kilo's ledger for both runs, then the four before → after beliefs one at a
// time, then "Play again". Framed as the deck's arch-shaped municipal signboard (deck p. 1, art-bible §8):
// saffron board, red edging, ink text. The one place the meaning colours are decoration.
import { GameObjects, Math as PMath, Scene } from 'phaser';
import endcard from '../../data/endcard.json';
import { parseBeat } from '../flow';
import { getState, setState } from '../state';
import { colour, css, font, FRAME, motion, type Meaning } from '../theme';
import { drawCard, drawChip } from '../ui/card';

type Column = { heading: string; proposed?: boolean; lines: { text: string; value: string; meaning: string }[] };

const PANEL = { x: 176, y: 268, w: 1568, h: 752 };
const BELIEF_Y = 640;
const BELIEF_STEP = 82;

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
        this.add.text(FRAME.width / 2, 566, endcard.payout_note, {
            fontFamily: font.body, fontSize: 29, color: css.muted, align: 'center', wordWrap: { width: PANEL.w - 96 },
        }).setOrigin(0.5);

        endcard.beliefs.forEach((b, i) => this.beliefs.push(this.beliefRow(b.before, b.after, BELIEF_Y + i * BELIEF_STEP)));
        this.nextHint = this.keyHint('Space');
        this.replay = this.button(endcard.replay, FRAME.width / 2, 965, () => this.playAgain());
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

    private beliefRow(before: string, after: string, y: number) {
        const cx = FRAME.width / 2, half = PANEL.w / 2 - 96;
        const row = this.add.container(0, y).setVisible(false);
        row.add([
            this.add.text(cx - 52, 0, before, { fontFamily: font.body, fontSize: 30, color: css.muted, align: 'right', wordWrap: { width: half } }).setOrigin(1, 0.5),
            this.add.text(cx, 0, '→', { fontFamily: font.display, fontSize: 44, fontStyle: '800', color: css.brown }).setOrigin(0.5, 0.55),
            this.add.text(cx + 52, 0, after, { fontFamily: font.display, fontSize: 32, fontStyle: '700', color: css.ink, wordWrap: { width: half } }).setOrigin(0, 0.5),
        ]);
        return row;
    }

    private keyHint(key: string) {
        const c = this.add.container(0, 0);
        const label = this.add.text(0, 0, key, { fontFamily: font.display, fontSize: 24, fontStyle: '700', color: css.cream }).setOrigin(0.5);
        const w = label.width + 32;
        const bg = this.add.graphics().fillStyle(colour.ink, 0.92).fillRoundedRect(-w / 2, -21, w, 42, 9);
        c.add([bg, label]);
        if (!getState(this).reducedMotion) this.tweens.add({ targets: c, alpha: 0.45, duration: 700, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
        return c;
    }

    private placeHint() {
        this.nextHint.setPosition(FRAME.width / 2, BELIEF_Y + this.shown * BELIEF_STEP).setVisible(this.shown < this.beliefs.length);
    }

    private button(text: string, x: number, y: number, onClick: () => void) {
        const label = this.add.text(0, 0, text, { fontFamily: font.display, fontSize: 34, fontStyle: '700', color: css.cream }).setOrigin(0.5);
        const w = label.width + 80, h = 68;
        const bg = this.add.graphics();
        const draw = (hover: boolean) => {
            bg.clear().fillStyle(hover ? colour.cost : colour.ink, 1).fillRoundedRect(-w / 2, -h / 2, w, h, h / 2);
            bg.lineStyle(4, colour.pay, 1).strokeRoundedRect(-w / 2, -h / 2, w, h, h / 2);
        };
        draw(false);
        const c = this.add.container(x, y, [bg, label]).setSize(w, h).setInteractive({ useHandCursor: true });
        c.on('pointerover', () => draw(true)).on('pointerout', () => draw(false)).on('pointerup', onClick);
        return c;
    }

    /** Space or a click shows the next belief; after the fourth, "Play again". */
    private advance(reducedMotion: boolean) {
        if (this.shown >= this.beliefs.length) return;
        const row = this.beliefs[this.shown++].setVisible(true);
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
