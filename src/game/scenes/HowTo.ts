// How to play (H, or the dock's button): the playing beat's briefing over the paused scene. H, Esc,
// Space or the button resume. Runs above every scene, like SkipMenu, and pauses what is playing.
import { GameObjects, Scene } from 'phaser';
import { howToText, runs } from '../content';
import { getState } from '../state';
import { colour, FRAME } from '../theme';
import { briefingCard, hasBriefing } from '../ui/Briefing';

const NOT_PLAYING = new Set(['HowTo', 'SkipMenu', 'Hud', 'Boot', 'StationCard']);

export class HowTo extends Scene {
    private layer?: GameObjects.Container;
    private paused: string[] = [];

    constructor() {
        super({ key: 'HowTo', active: true });
    }

    create() {
        const kb = this.input.keyboard!;
        kb.on('keydown-H', () => (this.layer ? this.close() : this.open()));
        for (const k of ['ESC', 'SPACE', 'ENTER']) kb.on(`keydown-${k}`, () => this.layer && this.close());
    }

    get isOpen() {
        return !!this.layer;
    }

    /** True when a beat is playing (not paused under the menu) and it has a how-to to show. */
    available() {
        if (!this.playing().length) return false;
        const { run, beat } = getState(this);
        const key = runs[run].beats[beat];
        return key !== undefined && hasBriefing(run, key);
    }

    open() {
        if (this.layer || !this.available()) return;
        const { run, beat } = getState(this);
        this.paused = this.playing();
        this.paused.forEach((k) => this.game.scene.pause(k));
        const dim = this.add.rectangle(0, 0, FRAME.width, FRAME.height, colour.void, 0.72).setOrigin(0).setInteractive();
        const card = briefingCard(this, run, runs[run].beats[beat], howToText.briefing.resume, () => this.close());
        this.layer = this.add.container(0, 0, [dim, card]);
        this.scene.bringToTop();
    }

    close() {
        const layer = this.layer;
        if (!layer) return;
        this.layer = undefined;
        layer.destroy();
        // resume a moment later, so the key that closed this does not also reach the scene
        const paused = this.paused;
        this.paused = [];
        this.time.delayedCall(60, () => paused.forEach((k) => this.game.scene.isPaused(k) && this.game.scene.resume(k)));
    }

    private playing() {
        return this.game.scene.getScenes(true).map((s) => s.sys.settings.key).filter((k) => !NOT_PLAYING.has(k));
    }
}
