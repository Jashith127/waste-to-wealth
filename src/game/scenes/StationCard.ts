// Between beats: "Run 2 · With the hub" when the run changes, then "2 · The walk", then the beat.
import { Scene } from 'phaser';
import { hasStation, runs, station } from '../content';
import { sceneFor, type Beat } from '../flow';
import { css, font, FRAME, motion } from '../theme';

export class StationCard extends Scene {
    constructor() {
        super('StationCard');
    }

    create({ beat, runChanged }: { beat: Beat; runChanged?: boolean }) {
        this.add.tileSprite(0, 0, FRAME.width, FRAME.height, 'lattice').setOrigin(0);
        const cards: [string, string][] = [];
        if (runChanged) cards.push([runs[beat.run].title, runs[beat.run].subtitle]);
        if (beat.station !== 'end' && hasStation(beat.station)) {
            const s = station(beat.station);
            cards.push([`${s.number} · ${s.title}${s.label ? ` · ${s.label}` : ''}`, beat.variant === 'night' ? `${s.place} · that night` : s.place]);
        }
        const show = (i: number) => {
            if (i >= cards.length) return this.scene.start(sceneFor(this, beat), { beat });
            const [t, sub] = cards[i];
            const title = this.add.text(FRAME.width / 2, FRAME.height / 2 - 10, t, {
                fontFamily: font.display, fontSize: 72, fontStyle: '800', color: css.cream,
            }).setOrigin(0.5).setAlpha(0);
            const place = this.add.text(FRAME.width / 2, FRAME.height / 2 + 62, sub, {
                fontFamily: font.body, fontSize: 30, color: '#B8AE9C', align: 'center', wordWrap: { width: 1300 },
            }).setOrigin(0.5, 0).setAlpha(0);
            this.tweens.add({
                targets: [title, place], alpha: 1, duration: motion.normal, hold: 900, yoyo: true,
                onComplete: () => { title.destroy(); place.destroy(); show(i + 1); },
            });
        };
        show(0);
    }
}
