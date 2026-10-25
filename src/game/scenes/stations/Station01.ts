// Station 1 · The stall, Cockburn Road. Finish the morning cut, pick up the kilo, take it out.
// Run 1 ends here too, as "s01:night": the same stall in a power cut, a tray of leftovers spoiling.
import { GameObjects, Math as PMath } from 'phaser';
import { setState, type KiloTagState } from '../../state';
import { colour, css, font, motion } from '../../theme';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'cut' | 'pickup' | 'leave' | 'night' | 'night_leave';

export default class Station01 extends StationScene {
    private phase: Phase = 'cut';
    private chops = 0;
    private busy = false;
    private queued = false;      // one press buffered during a chop, so quick taps are never lost
    private riyaz!: Record<'idle' | 'up' | 'down', GameObjects.Image>;
    private kilo!: GameObjects.Image;
    private kiloShadow!: GameObjects.Image;
    private ring?: GameObjects.Arc;

    constructor() {
        super('s01');
    }

    preload() {
        this.loadLayers();
    }

    protected build() {
        this.phase = 'cut';
        this.chops = 0;
        this.busy = false;
        this.queued = false;

        if (this.variant === 'night') return this.buildNight();

        this.layer('bg');
        const glow = this.layer('fx_fridge_glow');
        this.flicker(glow);
        this.riyaz = { idle: this.layer('riyaz_idle'), up: this.layer('riyaz_up'), down: this.layer('riyaz_down') };
        this.pose('idle');
        this.kiloShadow = this.layer('kilo_shadow').setAlpha(0);
        this.kilo = this.layer('kilo').setAlpha(0);

        // the block: click it or press Space to chop
        const block = this.anchor('block');
        this.add.zone(block.x, block.y - 20, 190, 150).setInteractive({ useHandCursor: true }).on('pointerup', () => this.act());
        this.input.keyboard!.on('keydown-SPACE', () => this.act());
        this.input.keyboard!.on('keydown-ENTER', () => this.act());
        this.input.keyboard!.on('keydown-RIGHT', () => this.phase === 'leave' && this.leave());

        this.prompt.show(this.prompts().cut, 'Space');
        this.ring = this.hint(block.x, block.y - 10, 92);
    }

    /** Run 1's ending: the same stall at night, the grid down, a tray of leftovers on the counter. */
    private buildNight() {
        this.phase = 'night';
        this.layer('bg_night');
        this.layer('riyaz_idle_night');
        const tray = this.layer('leftovers_night');

        const kb = this.input.keyboard!;
        kb.on('keydown-RIGHT', () => { if (this.phase === 'night_leave') this.leave(); });
        kb.on('keydown-ENTER', () => { if (this.phase === 'night_leave') this.leave(); });

        this.prompt.show(this.prompts().night);
        const spoil = () => this.spoil(tray);
        if (this.state.reducedMotion) this.time.delayedCall(1200, spoil);
        else this.cameras.main.once('camerafadeincomplete', () => this.time.delayedCall(1200, spoil));
    }

    /** The leftovers dull and the "Lost" tag swings in: no power, so the meat spoils overnight. */
    private spoil(tray: GameObjects.Image) {
        this.phase = 'night_leave';
        tray.setTint(0xB8A89A);                                     // the spoiling cue; no gore
        if (this.state.reducedMotion) tray.setAlpha(0.85);
        else this.tweens.add({ targets: tray, alpha: 0.85, duration: 600, ease: 'Sine.easeOut' });

        const c = this.anchor('leftovers_centre');
        const tagData = this.params().leftovers.tag;
        const tag = new KiloTag(this, c.x, c.y, tagData, this.state.reducedMotion, { dx: -150, dy: 0 }).setDepth(30);
        if (this.state.reducedMotion) tag.setAlpha(1);
        else {
            tag.setAlpha(0);
            this.tweens.add({ targets: tag, alpha: 1, duration: motion.normal, onStart: () => tag.appear() });
        }

        this.prompt.show(this.prompts().night_leave, '→');
        const go = this.arrowButton();
        if (this.state.reducedMotion) go.setAlpha(1);
        else {
            go.setAlpha(0);
            this.tweens.add({ targets: go, alpha: 1, duration: motion.normal });
        }
    }

    /** The night's exit: a small → button, above the blueprint line. */
    private arrowButton() {
        const g = this.add.graphics();
        g.fillStyle(colour.ink, 0.92).fillRoundedRect(-36, -36, 72, 72, 18);
        const label = this.add.text(0, -2, '→', { fontFamily: font.display, fontSize: 36, fontStyle: '700', color: css.cream }).setOrigin(0.5);
        const b = this.add.container(1700, 600, [g, label]).setSize(72, 72).setDepth(45);
        b.setInteractive({ useHandCursor: true }).on('pointerup', () => this.leave());
        return b;
    }

    private act() {
        if (this.phase === 'cut') this.chop();
        else if (this.phase === 'pickup') this.pickUp();
    }

    private pose(p: 'idle' | 'up' | 'down') {
        for (const [k, img] of Object.entries(this.riyaz)) img.setVisible(k === p);
    }

    /** One stroke of the cleaver: up, down (thunk), back to rest. */
    private chop() {
        if (this.busy) {
            this.queued = true;
            return;
        }
        this.busy = true;
        this.pose('up');
        this.time.delayedCall(110, () => {
            this.pose('down');
            this.events.emit('sfx', 'cleaver');                     // sound hook: cleaver on the block (art-bible, Five senses)
            if (!this.state.reducedMotion) this.cameras.main.shake(90, 0.0018);
            this.time.delayedCall(150, () => {
                this.pose('idle');
                this.busy = false;
                if (++this.chops >= (this.params().cut.chops ?? 3)) {
                    this.queued = false;
                    this.kiloReady();
                } else if (this.queued) {
                    this.queued = false;
                    this.chop();
                }
            });
        });
    }

    /** The cut is done: the bone and offal are bagged on the counter. */
    private kiloReady() {
        this.phase = 'pickup';
        this.ring?.destroy();
        const y = this.kilo.y;
        this.kilo.setY(y - 36).setAlpha(0);
        this.tweens.add({ targets: this.kilo, y, alpha: 1, duration: 260, ease: 'Back.easeOut' });
        this.tweens.add({ targets: this.kiloShadow, alpha: 1, duration: 260, delay: 80 });
        const c = this.anchor('kilo_centre');
        this.add.zone(c.x, c.y, 150, 150).setInteractive({ useHandCursor: true }).on('pointerup', () => this.act());
        this.prompt.show(this.prompts().pickup, 'Space');
        this.ring = this.hint(c.x, c.y, 70);
    }

    /** Lift the kilo; its tag swings in: a ₹5 problem. */
    private pickUp() {
        this.phase = 'leave';
        this.ring?.destroy();
        const lift = 70;
        this.tweens.add({ targets: this.kilo, y: this.kilo.y - lift, duration: 380, ease: 'Cubic.easeOut' });
        this.tweens.add({ targets: this.kiloShadow, alpha: 0.35, duration: 380 });

        const tagData = this.stationData.kilo!.tag;
        const knot = this.anchor('kilo_knot');
        const tag = new KiloTag(this, knot.x, knot.y - lift, tagData, this.state.reducedMotion, { dx: -130, dy: 26 }).setDepth(30).setAlpha(0);
        this.tweens.add({ targets: tag, alpha: 1, duration: motion.normal, delay: 200, onStart: () => tag.appear() });
        setState(this, { kilo: { carried: true, tag: { ...tagData } } });

        this.prompt.show(this.prompts().leave, '→');
        this.makeExit();
    }

    private makeExit() {
        const exit = this.anchor('exit');
        const x = Math.min(exit.x + 360, 1720), y = 560;
        const g = this.add.graphics();
        g.fillStyle(colour.ink, 0.92).fillRoundedRect(-150, -36, 300, 72, 36);
        const label = this.add.text(0, 0, 'Walk on  →', {
            fontFamily: font.display, fontSize: 32, fontStyle: '700', color: css.cream,
        }).setOrigin(0.5);
        const b = this.add.container(x, y, [g, label]).setSize(300, 72).setDepth(45).setAlpha(0);
        b.setInteractive({ useHandCursor: true }).on('pointerup', () => this.leave());
        this.tweens.add({ targets: b, alpha: 1, x: { from: x - 20, to: x }, duration: motion.normal, delay: 350 });
        return b;
    }

    private params() {
        return this.stationData.params as {
            cut: { chops: number };
            fridge: { flicker: boolean };
            leftovers: { tag: KiloTagState };
        };
    }

    /** The cooler light stutters: mostly on, with bursts of drop-outs (unreliable power, deck p. 22). */
    private flicker(glow: GameObjects.Image) {
        if (this.state.reducedMotion || !this.params().fridge.flicker) return;
        const burst = () => {
            const blinks = PMath.Between(2, 4);
            for (let i = 0; i < blinks; i++) {
                this.time.delayedCall(i * 140, () => glow.setAlpha(0.08));
                this.time.delayedCall(i * 140 + PMath.Between(40, 90), () => glow.setAlpha(1));
            }
            this.time.delayedCall(PMath.Between(1600, 4200), burst);
        };
        this.time.delayedCall(900, burst);
    }
}
