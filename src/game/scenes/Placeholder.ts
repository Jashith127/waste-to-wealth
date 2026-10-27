// Grey-box stand-in for any beat whose scene is not built yet, so both runs can be walked end to end.
// A station task replaces it by adding src/game/scenes/stations/StationNN.ts.
import { Scene } from 'phaser';
import { hasStation, runData, station } from '../content';
import { goNext, type Beat } from '../flow';
import { getState } from '../state';
import { colour, css, font, FRAME, layout } from '../theme';
import { KiloTag } from '../ui/KiloTag';
import { Prompt } from '../ui/Prompt';

export class Placeholder extends Scene {
    constructor() {
        super('Placeholder');
    }

    create({ beat }: { beat: Beat }) {
        const state = getState(this);
        this.add.tileSprite(0, 0, FRAME.width, FRAME.height, 'lattice').setOrigin(0);
        const g = this.add.graphics();
        const iso = (x: number, y: number, z = 0) => ({ x: 960 + (x + y - 3) * 0.707 * 175, y: 540 - ((y - 3) - x) * 0.354 * 175 - (z - 1) * 0.866 * 175 });
        const quad = (pts: { x: number; y: number }[], fill: number) => {
            g.fillStyle(fill, 1).beginPath().moveTo(pts[0].x, pts[0].y);
            pts.slice(1).forEach((p) => g.lineTo(p.x, p.y));
            g.closePath().fillPath();
        };
        quad([iso(-5, 0), iso(5, 0), iso(5, 3), iso(-5, 3)], 0x8a8580);              // pavement
        quad([iso(-5, 3), iso(5, 3), iso(5, 3, 4.5), iso(-5, 3, 4.5)], 0xb4aea6);     // frontage

        const isEnd = beat.station === 'end';
        const s = isEnd || !hasStation(beat.station) ? null : station(beat.station);
        const run = s ? runData(s, state.run) : {};
        g.fillStyle(colour.ink, 0.9).fillRoundedRect(FRAME.width / 2 - 560, 760, 1120, 250, 18);
        this.add.text(FRAME.width / 2, 820, s ? `${s.number} · ${s.title}${beat.variant ? ` (${beat.variant})` : ''}` : isEnd ? 'End card' : beat.station, {
            fontFamily: font.display, fontSize: 52, fontStyle: '800', color: css.cream,
        }).setOrigin(0.5);
        this.add.text(FRAME.width / 2, 890, `${run.summary ?? ''}${run.proposed ? '  · Proposed' : ''}`, {
            fontFamily: font.body, fontSize: 28, color: css.cream, align: 'center', wordWrap: { width: 1040 },
        }).setOrigin(0.5, 0);
        this.add.text(FRAME.width / 2, 975, 'Grey box · see tasks/', { fontFamily: font.body, fontSize: 22, color: '#8F877C' }).setOrigin(0.5);

        if (state.kilo.tag) new KiloTag(this, FRAME.width - 260, 20, state.kilo.tag, state.reducedMotion).setDepth(30);
        new Prompt(this, layout.prompt.x, layout.prompt.y, s ? { badge: String(s.number).padStart(2, '0'), title: s.title } : {}).show(isEnd ? 'The end card is a grey box for now' : 'Walk on', isEnd ? undefined : '→');
        if (!isEnd) this.input.keyboard!.once('keydown-RIGHT', () => goNext(this));
        (window as unknown as { __ready?: string }).__ready = beat.station;
        this.cameras.main.fadeIn(300, 28, 23, 20);
    }
}
