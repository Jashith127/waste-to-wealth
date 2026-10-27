// HUD overlay: runs above every scene (last in main.ts) and draws the control dock at the bottom left:
// Blueprint (B) and Evidence (I) at a station, How to play (H) wherever the beat has a how-to, and
// Menu (M) everywhere but the cards. Each is a button as well as a key, lit while its panel is open.
// On a phone the key caps go away, the buttons grow, and a stick plus a Tap button stand in for the keys.
// It rises above the blueprint panel while that is open. (The objective card is each scene's Prompt.)
import { GameObjects, Geom, Scene } from 'phaser';
import { howToText } from '../content';
import { currentControl } from '../controls';
import { isPhone } from '../device';
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
    private dock!: GameObjects.Container;
    private buttons = {} as Record<Action, Button>;
    private shown = '';
    private y: number = layout.dock.y;
    private readonly phone = isPhone();
    private readonly dockH = isPhone() ? 120 : layout.dock.h;
    private stick?: GameObjects.Container;
    private knob?: GameObjects.Arc;
    private stickId: number | null = null;
    private swipe = false;
    private action?: GameObjects.Container;
    private actionId: number | null = null;
    private virtual: Record<Arrow, boolean> = { LEFT: false, RIGHT: false, UP: false, DOWN: false };
    private lastScene?: Scene;

    constructor() {
        super({ key: 'Hud', active: true });
    }

    create() {
        const restY = this.phone ? 1080 - 80 - this.dockH / 2 : layout.dock.y;
        this.y = restY;
        this.dock = this.add.container(this.phone ? 300 : layout.dock.x, restY).setVisible(false);
        for (const a of Object.keys(KEYS) as Action[]) this.buttons[a] = this.button(a);
        if (this.phone) {
            this.input.addPointer(2);
            this.buildStick(restY);
            this.buildAction(restY);
        }
    }

    private button(a: Action): Button {
        const h = this.dockH;
        const cap = this.phone ? undefined : keycap(this, KEYS[a], 32);
        const t = this.add.text(0, 0, howToText.dock[a], {
            fontFamily: font.display, fontSize: this.phone ? 40 : 23, fontStyle: '700', color: css.cream,
        }).setOrigin(0, 0.5);
        const w = this.phone ? t.width + 64 : 14 + cap!.width + 12 + t.width + 20;
        if (cap) cap.setPosition(14 + cap.width / 2, -2);
        t.setX(this.phone ? 32 : 14 + cap!.width + 12);
        const bg = this.add.graphics();
        const c = this.add.container(0, 0, cap ? [bg, cap, t] : [bg, t]);
        c.setInteractive({ hitArea: new Geom.Rectangle(0, -h / 2, w, h), hitAreaCallback: Geom.Rectangle.Contains, useHandCursor: true });
        const b: Button = { c, bg, w, hover: false, lit: false };
        c.on('pointerover', () => { b.hover = true; this.paint(b); })
            .on('pointerout', () => { b.hover = false; this.paint(b); })
            .on('pointerdown', () => this.input.stopPropagation())
            .on('pointerup', () => { this.input.stopPropagation(); this.act(a); });
        this.paint(b);
        this.dock.add(c);
        return b;
    }

    private paint(b: Button) {
        const h = this.dockH, r = h / 2;
        b.bg.clear().fillStyle(hud.shadow, 0.3).fillRoundedRect(0, -h / 2 + 4, b.w, h, r);
        b.bg.fillStyle(b.lit ? colour.brown : hud.panel, b.lit ? 1 : hud.panelAlpha).fillRoundedRect(0, -h / 2, b.w, h, r);
        b.bg.lineStyle(this.phone ? 4 : 2.5, b.hover || b.lit ? colour.pay : colour.cream, b.hover || b.lit ? 1 : 0.18).strokeRoundedRect(0, -h / 2, b.w, h, r);
        if (!getState(this).reducedMotion) b.c.setScale(b.hover ? 1.04 : 1);
    }

    private buildStick(y: number) {
        const g = this.add.graphics();
        g.fillStyle(hud.shadow, 0.35).fillCircle(4, 8, 120);
        g.fillStyle(hud.panel, 0.9).fillCircle(0, 0, 120);
        g.lineStyle(5, colour.cream, 0.35).strokeCircle(0, 0, 120);
        g.lineStyle(4, colour.cream, 0.2).strokeCircle(0, 0, 46);
        this.knob = this.add.circle(0, 0, 48, colour.pay, 1).setStrokeStyle(5, colour.ink, 1);
        this.stick = this.add.container(210, y, [g, this.knob]).setVisible(false);
        this.stick.setInteractive(new Geom.Circle(0, 0, 140), Geom.Circle.Contains);
        this.stick.on('pointerdown', (p: Phaser.Input.Pointer) => {
            this.input.stopPropagation();
            this.stickId = p.id;
            this.placeKnob(p);
        });
        this.input.on('pointermove', (p: Phaser.Input.Pointer) => {
            if (p.id !== this.stickId) return;
            this.input.stopPropagation();
            this.placeKnob(p);
        });
        this.input.on('pointerup', (p: Phaser.Input.Pointer) => {
            if (p.id !== this.stickId) return;
            this.input.stopPropagation();
            this.releaseStick(p);
        });
    }

    private placeKnob(p: Phaser.Input.Pointer) {
        if (!this.stick || !this.knob) return;
        const dx = p.x - this.stick.x, dy = p.y - this.stick.y;
        const dist = Math.hypot(dx, dy) || 1;
        const cl = Math.min(dist, 78);
        this.knob.setPosition((dx / dist) * cl, (dy / dist) * cl);
        if (this.swipe) return;
        const nx = dx / dist, ny = dy / dist;
        const live = dist > 28;
        this.virtual.RIGHT = live && nx > 0.4;
        this.virtual.LEFT = live && nx < -0.4;
        this.virtual.UP = live && ny < -0.4;
        this.virtual.DOWN = live && ny > 0.4;
    }

    private releaseStick(p: Phaser.Input.Pointer) {
        if (this.swipe && this.stick) {
            const dx = p.x - this.stick.x, dy = p.y - this.stick.y;
            if (Math.abs(dx) > 36 && Math.abs(dx) > Math.abs(dy)) this.tapKey(dx > 0 ? 'RIGHT' : 'LEFT');
        }
        this.stickId = null;
        this.knob?.setPosition(0, 0);
        this.virtual = { LEFT: false, RIGHT: false, UP: false, DOWN: false };
    }

    private buildAction(y: number) {
        const g = this.add.graphics();
        const draw = (down: boolean) => {
            g.clear();
            g.fillStyle(hud.shadow, 0.35).fillCircle(4, 8, 100);
            g.fillStyle(down ? colour.brown : colour.pay, 1).fillCircle(0, 0, 100);
            g.lineStyle(5, colour.ink, 1).strokeCircle(0, 0, 100);
        };
        draw(false);
        const label = this.add.text(0, 2, 'Tap', { fontFamily: font.display, fontSize: 44, fontStyle: '800', color: css.ink }).setOrigin(0.5);
        this.action = this.add.container(1920 - 180, y, [g, label]).setVisible(false);
        this.action.setInteractive(new Geom.Circle(0, 0, 110), Geom.Circle.Contains);
        this.action.on('pointerdown', (p: Phaser.Input.Pointer) => {
            this.input.stopPropagation();
            this.actionId = p.id;
            draw(true);
            const key = currentControl().tapKey;
            if (key) this.tapKey(key);
        });
        this.action.on('pointerup', () => { this.actionId = null; draw(false); this.input.stopPropagation(); });
        this.action.on('pointerout', () => { if (this.actionId === null) draw(false); });
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

    update(_t: number, delta: number) {
        const scene = this.playing();
        if (!scene) {
            this.dock.setVisible(false);
            this.stick?.setVisible(false);
            this.action?.setVisible(false);
            this.virtual = { LEFT: false, RIGHT: false, UP: false, DOWN: false };
            this.syncArrows(undefined);
            return;
        }
        const station = scene instanceof StationScene ? scene : undefined;
        const want: Action[] = [];
        if (station) want.push('blueprint', 'evidence');
        if ((this.scene.get('HowTo') as HowTo).available()) want.push('help');
        want.push('menu');

        const mode = this.phone ? currentControl() : { stick: null as null, tapKey: undefined as string | undefined };
        const stickOn = !!mode.stick;
        const tapOn = !!mode.tapKey;
        const key = want.join() + (stickOn ? ':s' : '') + (tapOn ? ':t' : '');
        if (key !== this.shown) {
            this.shown = key;
            let x = this.phone && stickOn ? 360 : layout.dock.x;
            for (const a of Object.keys(KEYS) as Action[]) {
                const b = this.buttons[a], on = want.includes(a);
                b.c.setVisible(on).setX(x);
                if (on) x += b.w + (this.phone ? 18 : layout.dock.gap);
            }
        }
        for (const a of ['blueprint', 'evidence'] as const) {
            const lit = !!station?.panelOpen(a);
            if (lit !== this.buttons[a].lit) {
                this.buttons[a].lit = lit;
                this.paint(this.buttons[a]);
            }
        }

        const restY = this.phone ? 1080 - 80 - this.dockH / 2 : layout.dock.y;
        const target = getState(this).blueprintOpen && station ? layout.blueprintTop - 16 - this.dockH / 2 : restY;
        this.y += (target - this.y) * Math.min(1, delta / 70);
        const fade = (scene.cameras.main as unknown as { fadeEffect?: { alpha: number } }).fadeEffect;
        const alpha = 1 - (fade?.alpha ?? 0);
        const y = Math.round(this.y);
        this.dock.setVisible(true).setY(y).setAlpha(alpha);
        if (this.phone) {
            this.swipe = mode.stick === 'swipe';
            this.stick?.setVisible(stickOn).setY(y).setAlpha(alpha);
            this.action?.setVisible(tapOn).setY(y).setAlpha(alpha);
            if (!stickOn && this.stickId !== null) this.releaseStick({ x: this.stick?.x ?? 0, y: this.stick?.y ?? 0 } as Phaser.Input.Pointer);
            this.syncArrows(scene);
        }
    }
}
