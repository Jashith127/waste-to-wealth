// HUD overlay: runs above every scene (last in main.ts) and shows the time-of-day clock for the beat
// the playing scene was started with. Hidden on the station cards and the end card.
import { Scene } from 'phaser';
import { runs } from '../content';
import type { Beat } from '../flow';
import { getState } from '../state';
import { Clock } from '../ui/Clock';

const NO_HUD = new Set(['Hud', 'Boot', 'StationCard', 'EndCard']);

export class Hud extends Scene {
    private clock!: Clock;

    constructor() {
        super({ key: 'Hud', active: true });
    }

    create() {
        this.clock = new Clock(this, getState(this).reducedMotion).setVisible(false);
    }

    update() {
        const playing = this.game.scene.getScenes(true).filter((s) => !NO_HUD.has(s.sys.settings.key));
        const showsCard = this.scene.isActive('StationCard') || this.scene.isActive('EndCard');
        const scene = playing[0];
        const beat = scene?.sys.settings.data && (scene.sys.settings.data as { beat?: Beat }).beat;
        const phase = beat && beat.station !== 'end' ? runs[beat.run].clock?.[runs[beat.run].beats[beat.index]] : undefined;
        if (showsCard || !scene || !phase) {
            this.clock.setVisible(false);
            return;
        }
        this.clock.set(phase);
        // Fade with the playing scene's camera, so the clock leaves with the station.
        const fade = (scene.cameras.main as unknown as { fadeEffect?: { alpha: number } }).fadeEffect;
        this.clock.setVisible(true).setAlpha(1 - (fade?.alpha ?? 0));
    }
}
