// Station 7 · Farm → back to the stall, "How it could close" (Run 2). Set from art/scripts/s07_build.py.
// The camera pans across the plate through three beats, about 1.5 s each, with a caption at each. No supply chain back to the stall was found, so the label, the Kannur precedent and
// that caveat stay on screen for the whole station.
import type { GameObjects, Time } from 'phaser';
import { colour, css, font, FRAME, layout, motion } from '../../theme';
import { drawCard } from '../../ui/card';
import { labelCard, paidTag } from '../../ui/greybox';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'watch' | 'leave';
interface Params { beats: { caption: string; anchor: string }[]; precedent: string; caveat: string; handfuls: number }

const BEAT_MS = 1500;

export default class Station07 extends StationScene {
    private phase: Phase = 'watch';
    private beat = -1;
    private caption?: GameObjects.Container;
    private timer?: Time.TimerEvent;
    private p!: Params;

    constructor() {
        super('s07');
    }

    preload() {
        this.loadLayers();
    }

    protected build() {
        this.phase = 'watch';
        this.beat = -1;
        this.caption = undefined;
        this.p = this.stationData.params as unknown as Params;
        this.layer('bg');                                   // a 3200x1920 plate (as s02); the scene pans it

        // the label, the precedent and the caveat: fixed on screen, never behind a click
        const label = labelCard(this, 0, 0, this.stationData.label ?? '', { band: colour.brown, size: 30 });
        label.setPosition(layout.prompt.x + label.getBounds().width / 2, 150);
        this.noteCard(layout.prompt.x, 196);
        new KiloTag(this, FRAME.width - 260, 20, paidTag(this), this.state.reducedMotion).setDepth(30);

        const kb = this.input.keyboard!;
        kb.on('keydown-SPACE', () => this.press());
        kb.on('keydown-ENTER', () => this.press());
        this.input.on('pointerup', (_p: unknown, over: GameObjects.GameObject[]) => over.length === 0 && this.press());
        kb.on('keydown-RIGHT', () => this.phase === 'leave' && this.leave());
        this.prompt.show(this.prompts().watch, 'Space');
        this.advance();
    }

    private noteCard(x: number, y: number) {
        const g = this.add.graphics();                       // first, so the text draws over it
        const pre = this.add.text(x + 24, y + 18, this.p.precedent, { fontFamily: font.body, fontSize: 28, color: css.ink });
        const cav = this.add.text(x + 24, y + 56, this.p.caveat, { fontFamily: font.body, fontSize: 28, color: css.muted });
        drawCard(g, x, y, Math.max(pre.width, cav.width) + 48, 104);
        for (const o of [g, pre, cav]) o.setDepth(35);
    }

    /** Pan to the next beat and caption it; after the last, leave for the end card. */
    private advance() {
        if (this.phase === 'leave') return this.leave();
        this.timer?.remove();
        this.beat++;
        this.caption?.destroy();
        if (this.beat >= this.p.beats.length) {
            this.phase = 'leave';
            this.prompt.show(this.prompts().leave, '→');
            return;
        }
        const b = this.p.beats[this.beat];
        const at = this.anchor(b.anchor);
        const plate = this.layers!.layers['bg'];
        // bring the anchor right of centre (clear of the note card), keeping the frame on the plate
        const to = {
            x: Math.min(0, Math.max(FRAME.width - plate.w, FRAME.width * 0.62 - at.x)),
            y: Math.min(0, Math.max(FRAME.height - plate.h, FRAME.height * 0.55 - at.y)),
        };
        if (this.state.reducedMotion) this.world.setPosition(to.x, to.y);
        else this.tweens.add({ targets: this.world, ...to, duration: motion.transition, ease: 'Sine.easeInOut' });
        this.caption = labelCard(this, at.x, at.y - 110, b.caption, { proposed: true, size: 30 });
        this.world.add(this.caption);
        if (b.anchor === 'feed') return this.startFeeding(at);
        this.timer = this.time.delayedCall(BEAT_MS, () => this.advance());
    }

    // --- feed the flock (mini-game) --------------------------------------------------------------

    private feeding = false;
    private handfuls = 0;
    private trough?: GameObjects.Graphics;
    private feedAt = { x: 0, y: 0 };

    private press() {
        if (this.feeding) this.scatter();
        else this.advance();
    }

    /** The farm beat waits for the player: each press throws a handful of meal into the feeder. */
    private startFeeding(at: { x: number; y: number }) {
        this.feeding = true;
        this.handfuls = 0;
        this.feedAt = at;
        this.prompt.show(this.prompts().feed, 'Space');
        this.trough = this.add.graphics();
        this.world.add(this.trough);
        this.ring?.destroy();
        this.ring = this.hint(at.x, at.y, 70);
        this.world.add(this.ring);                         // pans with the farm
    }

    private ring?: GameObjects.Arc;

    private scatter() {
        const from = { x: this.feedAt.x + 247, y: this.feedAt.y - 78 };      // the farmer's hand, behind the feeder
        this.events.emit('sfx', 'scatter_feed');
        for (let i = 0; i < 14; i++) {
            const grain = this.add.circle(from.x, from.y, 3, 0x9c8160, 1);
            this.world.add(grain);
            const tx = this.feedAt.x + (Math.random() - 0.5) * 120, ty = this.feedAt.y + (Math.random() - 0.5) * 30;
            const k = { t: 0 };
            this.tweens.add({
                targets: k, t: 1, duration: this.state.reducedMotion ? 1 : 420 + i * 18, ease: 'Linear',
                onUpdate: () => grain.setPosition(from.x + (tx - from.x) * k.t, from.y + (ty - from.y) * k.t - Math.sin(Math.PI * k.t) * 70),
                onComplete: () => grain.destroy(),
            });
        }
        this.handfuls++;
        const fill = this.handfuls / this.p.handfuls;
        this.time.delayedCall(this.state.reducedMotion ? 1 : 480, () => {
            this.trough?.clear().fillStyle(0x9c8160, 0.85).fillEllipse(this.feedAt.x, this.feedAt.y + 6, 150 * fill, 22 * fill);
        });
        if (this.handfuls >= this.p.handfuls) {
            this.feeding = false;
            this.ring?.destroy();
            this.prompt.show(this.prompts().watch, 'Space');
            this.timer = this.time.delayedCall(1200, () => this.advance());
        }
    }
}
