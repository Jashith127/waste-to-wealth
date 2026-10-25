// Station 1 · The stall, Cockburn Road. Finish the morning cut, pick up the kilo, take it out.
import { GameObjects, Math as PMath } from 'phaser';
import { runData } from '../content';
import { setState } from '../state';
import { colour, css, font, motion } from '../theme';
import { KiloTag } from '../ui/KiloTag';
import { StationScene } from './StationScene';

type Phase = 'cut' | 'pickup' | 'leave';

export class Station01 extends StationScene {
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
        this.input.keyboard!.on('keydown-RIGHT', () => this.phase === 'leave' && this.leave(this.next()));

        this.prompt.show(this.prompts().cut, 'Space');
        this.ring = this.hint(block.x, block.y - 10, 92);
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
                if (++this.chops >= ((this.stationData.cut as { chops: number }).chops ?? 3)) {
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
        const label = this.add.text(0, 0, `${runData(this.stationData, this.state.run).next === 's02' ? 'Walk on' : 'Next'}  →`, {
            fontFamily: font.display, fontSize: 32, fontStyle: '700', color: css.cream,
        }).setOrigin(0.5);
        const b = this.add.container(x, y, [g, label]).setSize(300, 72).setDepth(45).setAlpha(0);
        b.setInteractive({ useHandCursor: true }).on('pointerup', () => this.leave(this.next()));
        this.tweens.add({ targets: b, alpha: 1, x: { from: x - 20, to: x }, duration: motion.normal, delay: 350 });
        return b;
    }

    private next() {
        return runData(this.stationData, this.state.run).next ?? 's02';
    }

    /** The cooler light stutters: mostly on, with bursts of drop-outs (unreliable power, deck p. 22). */
    private flicker(glow: GameObjects.Image) {
        if (this.state.reducedMotion) return;
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
