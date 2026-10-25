// Between stations: "2 · The walk" on the void, then the next station.
import { Scene } from 'phaser';
import { station } from '../content';
import { css, font, FRAME, motion } from '../theme';

export class StationCard extends Scene {
    constructor() {
        super('StationCard');
    }

    create({ next }: { next: string }) {
        const s = station(next);
        this.add.tileSprite(0, 0, FRAME.width, FRAME.height, 'lattice').setOrigin(0);
        const title = this.add.text(FRAME.width / 2, FRAME.height / 2 - 10, `${s.number} · ${s.title}`, {
            fontFamily: font.display, fontSize: 72, fontStyle: '800', color: css.cream,
        }).setOrigin(0.5).setAlpha(0);
        const place = this.add.text(FRAME.width / 2, FRAME.height / 2 + 62, s.place, {
            fontFamily: font.body, fontSize: 30, color: '#B8AE9C',
        }).setOrigin(0.5).setAlpha(0);
        this.tweens.add({
            targets: [title, place], alpha: 1, duration: motion.normal, hold: 750, yoyo: true,
            onComplete: () => this.scene.start(next),
        });
    }
}
