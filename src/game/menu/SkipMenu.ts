// Skip menu (task 12): M or the dock's Menu button (Hud) opens it; Esc or M closes it. Jump to any beat
// of either run, restart, or toggle reduced motion. Runs above every scene (active: true, last in main.ts)
// and pauses the playing scene while it is open.
import { GameObjects, Scene } from 'phaser';
import endcard from '../../data/endcard.json';
import hud from '../../data/hud.json';
import marketMap from '../../data/map.json';
import { hasStation, runs, station, type Tag } from '../content';
import { parseBeat, type Beat } from '../flow';
import { LOCALES, locale, setLocale } from '../i18n';
import { getState, setState, type KiloTagState, type Run } from '../state';
import { colour, css, font, FRAME } from '../theme';
import { drawCard } from '../ui/card';

const NOT_PLAYING = new Set(['SkipMenu', 'Hud', 'Boot', 'HowTo']);
const PANEL = { x: 260, y: 110, w: 1400, h: 860 };
const ROW_H = 62;

// The tag after s03's flip, when s03's own data is not in yet (task 03 params.tag_after).
const PAID_FALLBACK: Tag = { label: 'Hub payout', value: '+₹3', meaning: 'income', note: 'Estimate: ₹3/kg sorted' };

interface Item { col: number; row: number; label: string; choose: () => void; text?: GameObjects.Text; y: number; x: number; w: number }

function beatLabel(beat: Beat): string {
    if (beat.station === 'end') return endcard.title;
    if (beat.station === 'map') return `${marketMap.title} (${beat.run === 1 ? 'Run 1' : 'Run 2'})`;
    if (!hasStation(beat.station)) return beat.station;
    const s = station(beat.station);
    return `${s.number} · ${s.title}${beat.variant ? ` (${beat.variant})` : ''}`;
}

/** The kilo's tag at the start of a beat: none before s01, −₹5 until s03, the estimated payout (+₹3) from s03 on in Run 2. */
function tagAt(beat: Beat): KiloTagState | null {
    if (beat.run === 1 && beat.index === 0) return null;
    if (beat.run === 2 && beat.index === 0) return null;
    const paidFrom = runs[2].beats.indexOf('s03');
    if (beat.run === 2 && (beat.station === 'end' || (paidFrom >= 0 && beat.index >= paidFrom))) {
        const after = hasStation('s03') ? (station('s03').params?.tag_after as Tag | undefined) : undefined;
        return after ?? PAID_FALLBACK;
    }
    return station('s01').kilo?.tag ?? null;
}

export class SkipMenu extends Scene {
    private panel!: GameObjects.Container;
    private focus!: GameObjects.Graphics;
    private items: Item[] = [];
    private cursor = 0;
    private paused: string[] = [];
    private motionText!: GameObjects.Text;

    constructor() {
        super({ key: 'SkipMenu', active: true });
    }

    create() {
        this.panel = this.add.container(0, 0).setVisible(false);
        this.buildPanel();
        const kb = this.input.keyboard!;
        kb.on('keydown-M', () => (this.panel.visible ? this.close() : this.open()));   // not over How to play: HowTo has paused the beat
        kb.on('keydown-ESC', () => this.panel.visible && this.close());
        kb.on('keydown-UP', () => this.move(-1));
        kb.on('keydown-DOWN', () => this.move(1));
        kb.on('keydown-LEFT', () => this.side(0));
        kb.on('keydown-RIGHT', () => this.side(1));
        kb.on('keydown-ENTER', () => this.panel.visible && this.items[this.cursor].choose());
    }

    private buildPanel() {
        const blocker = this.add.rectangle(0, 0, FRAME.width, FRAME.height, colour.void, 0.72).setOrigin(0).setInteractive();
        const g = this.add.graphics();
        drawCard(g, PANEL.x, PANEL.y, PANEL.w, PANEL.h, colour.pay);
        this.focus = this.add.graphics();
        this.panel.add([blocker, g, this.focus]);
        this.panel.add(this.add.text(PANEL.x + 48, PANEL.y + 66, hud.menu.title, { fontFamily: font.display, fontSize: 48, fontStyle: '800', color: css.ink }).setOrigin(0, 0.5));

        const colW = (PANEL.w - 144) / 2;
        ([1, 2] as Run[]).forEach((run, col) => {
            const x = PANEL.x + 48 + col * (colW + 48);
            this.panel.add(this.add.text(x, PANEL.y + 150, runs[run].title, { fontFamily: font.display, fontSize: 34, fontStyle: '700', color: css.muted }).setOrigin(0, 0.5));
            const beats = runs[run].beats.map((_, i) => parseBeat(run, i));
            beats.forEach((beat, row) => this.addItem(col, row, x, PANEL.y + 214 + row * ROW_H, colW, beatLabel(beat), () => this.jump(beat)));
        });

        const by = PANEL.y + PANEL.h - 70;
        this.addItem(2, 0, PANEL.x + 48, by, 440, hud.menu.restart, () => this.jump(parseBeat(1, 0), true));
        this.motionText = this.addItem(2, 1, PANEL.x + 508, by, 340, '', () => this.toggleMotion()).text!;
        // the language, named in its own script; choosing the next one reloads in it
        const name = LOCALES.find((l) => l.id === locale)!.name;
        this.addItem(2, 2, PANEL.x + 868, by, 300, `Language: ${name}`, () => {
            const i = LOCALES.findIndex((l) => l.id === locale);
            setLocale(LOCALES[(i + 1) % LOCALES.length].id);
        });
        this.addItem(2, 3, PANEL.x + PANEL.w - 228, by, 180, hud.menu.close, () => this.close());
        this.panel.add(this.add.graphics().lineStyle(2, colour.ink, 0.15).lineBetween(PANEL.x + 48, by - 52, PANEL.x + PANEL.w - 48, by - 52));
    }

    private addItem(col: number, row: number, x: number, y: number, w: number, label: string, choose: () => void): Item {
        const text = this.add.text(x + 20, y, label, { fontFamily: font.body, fontSize: 30, color: css.ink }).setOrigin(0, 0.5);
        const hit = this.add.rectangle(x, y, w, ROW_H - 8, 0, 0).setOrigin(0, 0.5).setInteractive({ useHandCursor: true });
        const item: Item = { col, row, label, choose, text, x, y, w };
        const index = this.items.push(item) - 1;
        hit.on('pointerover', () => this.setCursor(index)).on('pointerup', () => choose());
        this.panel.add([hit, text]);
        return item;
    }

    get isOpen() {
        return this.panel.visible;
    }

    open() {
        if (this.panel.visible || (this.scene.get('HowTo') as unknown as { isOpen?: boolean }).isOpen) return;
        this.paused = this.game.scene.getScenes(true).map((s) => s.sys.settings.key).filter((k) => !NOT_PLAYING.has(k));
        this.paused.forEach((k) => this.game.scene.pause(k));
        this.motionText.setText(`${hud.menu.reduced_motion}: ${getState(this).reducedMotion ? 'on' : 'off'}`);
        const { run, beat } = getState(this);
        this.setCursor(Math.max(0, this.items.findIndex((it) => it.col === run - 1 && it.row === beat)));
        this.panel.setVisible(true);
        this.scene.bringToTop();
        (window as unknown as { __menu?: string }).__menu = 'open';
    }

    private close() {
        this.panel.setVisible(false);
        this.paused.forEach((k) => this.game.scene.resume(k));
        this.paused = [];
        (window as unknown as { __menu?: string }).__menu = 'closed';
    }

    private setCursor(i: number) {
        this.cursor = i;
        const it = this.items[i];
        this.focus.clear().fillStyle(colour.pay, 0.28).fillRoundedRect(it.x, it.y - (ROW_H - 8) / 2, it.w, ROW_H - 8, 10);
        this.focus.lineStyle(3, colour.ink, 1).strokeRoundedRect(it.x, it.y - (ROW_H - 8) / 2, it.w, ROW_H - 8, 10);
    }

    private move(d: number) {
        if (this.panel.visible) this.setCursor((this.cursor + d + this.items.length) % this.items.length);
    }

    /** Left/Right: the same row in the other run's column (or the neighbour in the bottom row). */
    private side(col: number) {
        if (!this.panel.visible) return;
        const cur = this.items[this.cursor];
        if (cur.col === 2) return this.move(col === 0 ? -1 : 1);
        const same = this.items.filter((it) => it.col === col);
        this.setCursor(this.items.indexOf(same[Math.min(cur.row, same.length - 1)]));
    }

    private toggleMotion() {
        const reducedMotion = !getState(this).reducedMotion;
        setState(this, { reducedMotion });
        this.motionText.setText(`${hud.menu.reduced_motion}: ${reducedMotion ? 'on' : 'off'}`);
    }

    /** Stop what is playing and start the beat through its station card, with the tag that beat expects. */
    private jump(beat: Beat, restart = false) {
        this.panel.setVisible(false);
        [...this.paused, ...this.game.scene.getScenes(true).map((s) => s.sys.settings.key).filter((k) => !NOT_PLAYING.has(k))]
            .forEach((k) => this.game.scene.stop(k));
        this.paused = [];
        setState(this, {
            run: beat.run, beat: beat.index, station: beat.station,
            kilo: { carried: false, tag: restart ? null : tagAt(beat) }, ...(restart ? { blueprintOpen: false } : {}),
        });
        this.game.scene.start('StationCard', { beat, runChanged: true });
        (window as unknown as { __menu?: string }).__menu = 'closed';
    }
}
