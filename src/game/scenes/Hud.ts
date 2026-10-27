// HUD overlay: runs above every scene (last in main.ts) and draws the control dock at the bottom left:
// Blueprint (B) and Evidence (I) at a station, How to play (H) wherever the beat has a how-to, and
// Menu (M) everywhere but the cards. Each is a button as well as a key, lit while its panel is open.
// It rises above the blueprint panel while that is open. (The objective card is each scene's Prompt.)
import { GameObjects, Geom, Scene } from 'phaser';
import { howToText } from '../content';
import { getState } from '../state';
import { colour, css, font, hud, layout } from '../theme';
import { keycap } from '../ui/keys';
import type { HowTo } from './HowTo';
import { StationScene } from './StationScene';
import type { SkipMenu } from '../menu/SkipMenu';

const NO_HUD = new Set(['Hud', 'Boot', 'StationCard', 'HowTo', 'SkipMenu']);
type Action = 'blueprint' | 'evidence' | 'help' | 'menu';
const KEYS: Record<Action, string> = { blueprint: 'B', evidence: 'I', help: 'H', menu: 'M' };

interface Button { c: GameObjects.Container; bg: GameObjects.Graphics; w: number; hover: boolean; lit: boolean }

export class Hud extends Scene {
    private dock!: GameObjects.Container;
    private buttons = {} as Record<Action, Button>;
    private shown = '';
    private y: number = layout.dock.y;

    constructor() {
        super({ key: 'Hud', active: true });
    }

    create() {
        this.dock = this.add.container(layout.dock.x, layout.dock.y).setVisible(false);
        for (const a of Object.keys(KEYS) as Action[]) this.buttons[a] = this.button(a);
    }

    private button(a: Action): Button {
        const h = layout.dock.h;
        const cap = keycap(this, KEYS[a], 32);
        const t = this.add.text(0, 0, howToText.dock[a], { fontFamily: font.display, fontSize: 23, fontStyle: '700', color: css.cream }).setOrigin(0, 0.5);
        const w = 14 + cap.width + 12 + t.width + 20;
        cap.setPosition(14 + cap.width / 2, -2);
        t.setX(14 + cap.width + 12);
        const bg = this.add.graphics();
        const c = this.add.container(0, 0, [bg, cap, t]);
        c.setInteractive({ hitArea: new Geom.Rectangle(0, -h / 2, w, h), hitAreaCallback: Geom.Rectangle.Contains, useHandCursor: true });
        const b: Button = { c, bg, w, hover: false, lit: false };
        c.on('pointerover', () => { b.hover = true; this.paint(b); })
            .on('pointerout', () => { b.hover = false; this.paint(b); })
            .on('pointerup', () => this.act(a));
        this.paint(b);
        this.dock.add(c);
        return b;
    }

    private paint(b: Button) {
        const h = layout.dock.h, r = h / 2;
        b.bg.clear().fillStyle(hud.shadow, 0.3).fillRoundedRect(0, -h / 2 + 4, b.w, h, r);
        b.bg.fillStyle(b.lit ? colour.brown : hud.panel, b.lit ? 1 : hud.panelAlpha).fillRoundedRect(0, -h / 2, b.w, h, r);
        b.bg.lineStyle(2.5, b.hover || b.lit ? colour.pay : colour.cream, b.hover || b.lit ? 1 : 0.18).strokeRoundedRect(0, -h / 2, b.w, h, r);
        if (!getState(this).reducedMotion) b.c.setScale(b.hover ? 1.04 : 1);
    }

    private act(a: Action) {
        const scene = this.playing();
        if (a === 'menu') return (this.scene.get('SkipMenu') as SkipMenu).open();
        if (a === 'help') return (this.scene.get('HowTo') as HowTo).open();
        if (scene instanceof StationScene) scene.togglePanel(a);
    }

    private playing(): Scene | undefined {
        return this.game.scene.getScenes(true).find((s) => !NO_HUD.has(s.sys.settings.key));
    }

    update(_t: number, delta: number) {
        const scene = this.playing();
        if (!scene) {
            this.dock.setVisible(false);
            return;
        }
        const station = scene instanceof StationScene ? scene : undefined;
        const want: Action[] = [];
        if (station) want.push('blueprint', 'evidence');
        if ((this.scene.get('HowTo') as HowTo).available()) want.push('help');
        want.push('menu');

        const key = want.join();
        if (key !== this.shown) {
            this.shown = key;
            let x = 0;
            for (const a of Object.keys(KEYS) as Action[]) {
                const b = this.buttons[a], on = want.includes(a);
                b.c.setVisible(on).setX(x);
                if (on) x += b.w + layout.dock.gap;
            }
        }
        for (const a of ['blueprint', 'evidence'] as const) {
            const lit = !!station?.panelOpen(a);
            if (lit !== this.buttons[a].lit) {
                this.buttons[a].lit = lit;
                this.paint(this.buttons[a]);
            }
        }

        // above the blueprint panel while it is open; fade with the playing scene's camera
        const target = getState(this).blueprintOpen && station ? layout.blueprintTop - 16 - layout.dock.h / 2 : layout.dock.y;
        this.y += (target - this.y) * Math.min(1, delta / 70);
        const fade = (scene.cameras.main as unknown as { fadeEffect?: { alpha: number } }).fadeEffect;
        this.dock.setVisible(true).setY(Math.round(this.y)).setAlpha(1 - (fade?.alpha ?? 0));
    }
}
