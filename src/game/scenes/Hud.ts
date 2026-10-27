// HUD overlay: runs above every scene and draws the control dock at the bottom left:
// Blueprint (B) and Evidence (I) at a station, How to play (H) wherever the beat has a how-to, and
// Menu (M) everywhere but the cards. Each is a button as well as a key, lit while its panel is open.
// On a phone those buttons, the stick and the tap button live in the side rails beside the scene,
// so they don't cover the picture. (The objective card is each scene's Prompt.)
import { GameObjects, Geom, Scene } from 'phaser';
import { howToText } from '../content';
import { currentControl } from '../controls';
import { isPhone } from '../device';
import { mountRails } from '../rails';
import { getState } from '../state';
import { colour, css, font, hud, layout } from '../theme';
import { keycap } from '../ui/keys';
import type { HowTo } from './HowTo';
import { StationScene } from './StationScene';
import type { SkipMenu } from '../menu/SkipMenu';

const NO_HUD = new Set(['Hud', 'Boot', 'StationCard', 'HowTo', 'SkipMenu']);
type Action = 'blueprint' | 'evidence' | 'help' | 'menu';
const KEYS: Record<Action, string> = { blueprint: 'B', evidence: 'I', help: 'H', menu: 'M' };
const ARROWS = ['LEFT', 'RIGHT', 'UP', 'DOWN'] as const;
type Arrow = typeof ARROWS[number];

interface Button { c: GameObjects.Container; bg: GameObjects.Graphics; w: number; hover: boolean; lit: boolean }

export class Hud extends Scene {
    private dock?: GameObjects.Container;
    private buttons = {} as Record<Action, Button>;
    private shown = '';
    private y: number = layout.dock.y;
    private readonly phone = isPhone();
    private rails?: ReturnType<typeof mountRails>;
    private virtual: Record<Arrow, boolean> = { LEFT: false, RIGHT: false, UP: false, DOWN: false };
    private lastScene?: Scene;

    constructor() {
        super({ key: 'Hud', active: true });
    }

    create() {
        if (this.phone) {
            this.rails = mountRails(this.game, {
                onStick: (held) => { this.virtual = held; },
                onSwipe: (code) => this.tapKey(code),
                onTap: () => { const key = currentControl().tapKey; if (key) this.tapKey(key); },
                onAction: (a) => this.act(a),
            });
            return;
        }
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
        this.dock!.add(c);
        return b;
    }

    private paint(b: Button) {
        const h = layout.dock.h, r = h / 2;
        b.bg.clear().fillStyle(hud.shadow, 0.3).fillRoundedRect(0, -h / 2 + 4, b.w, h, r);
        b.bg.fillStyle(b.lit ? colour.brown : hud.panel, b.lit ? 1 : hud.panelAlpha).fillRoundedRect(0, -h / 2, b.w, h, r);
        b.bg.lineStyle(2.5, b.hover || b.lit ? colour.pay : colour.cream, b.hover || b.lit ? 1 : 0.18).strokeRoundedRect(0, -h / 2, b.w, h, r);
        if (!getState(this).reducedMotion) b.c.setScale(b.hover ? 1.04 : 1);
    }

    /** Fire one key on the scene that is actually playing, the same way a physical key would. */
    private tapKey(code: string) {
        const kb = this.playing()?.input.keyboard;
        if (!kb) return;
        kb.emit(`keydown-${code}`, { repeat: false });
        kb.emit(`keyup-${code}`, {});
    }

    private syncArrows(scene: Scene | undefined) {
        const target = scene ?? this.lastScene;
        if (scene) this.lastScene = scene;
        const kb = target?.input.keyboard;
        if (!kb || !target?.sys.isActive()) return;
        for (const code of ARROWS) {
            const key = kb.addKey(code);
            const down = !!scene && this.virtual[code];
            if (key.isDown === down) continue;
            key.isDown = down;
            key.isUp = !down;
            if (down) kb.emit(`keydown-${code}`, { repeat: false });
            else kb.emit(`keyup-${code}`, {});
        }
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

    private wanted(scene: Scene | undefined): Action[] {
        const station = scene instanceof StationScene ? scene : undefined;
        const want: Action[] = [];
        if (station) want.push('blueprint', 'evidence');
        if ((this.scene.get('HowTo') as HowTo).available()) want.push('help');
        if (scene) want.push('menu');
        return want;
    }

    update(_t: number, delta: number) {
        const scene = this.playing();
        if (this.phone) {
            if (!scene) {
                this.virtual = { LEFT: false, RIGHT: false, UP: false, DOWN: false };
                this.syncArrows(undefined);
                this.rails?.update(null);
                return;
            }
            const station = scene instanceof StationScene ? scene : undefined;
            this.rails?.update({
                actions: this.wanted(scene),
                lit: { blueprint: !!station?.panelOpen('blueprint'), evidence: !!station?.panelOpen('evidence') },
            });
            this.syncArrows(scene);
            return;
        }

        const dock = this.dock!;
        if (!scene) {
            dock.setVisible(false);
            return;
        }
        const station = scene instanceof StationScene ? scene : undefined;
        const want = this.wanted(scene);
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

        const target = getState(this).blueprintOpen && station ? layout.blueprintTop - 16 - layout.dock.h / 2 : layout.dock.y;
        this.y += (target - this.y) * Math.min(1, delta / 70);
        const fade = (scene.cameras.main as unknown as { fadeEffect?: { alpha: number } }).fadeEffect;
        dock.setVisible(true).setY(Math.round(this.y)).setAlpha(1 - (fade?.alpha ?? 0));
    }
}
