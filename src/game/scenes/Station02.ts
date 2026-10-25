// Station 2 · The walk. GREY BOX: placeholder until tasks/ builds it. Shows the carried tag.
import { runData } from '../content';
import { colour, css, font, FRAME } from '../theme';
import { KiloTag } from '../ui/KiloTag';
import { StationScene } from './StationScene';

export class Station02 extends StationScene {
    constructor() {
        super('s02');
    }

    protected build() {
        const g = this.add.graphics();
        // grey-box street slice in the same 2:1 projection as the Blender camera
        const iso = (x: number, y: number, z = 0) => ({ x: 960 + (x + y) * 0.707 * 175, y: 640 - (y - x) * 0.354 * 175 - z * 0.866 * 175 });
        const quad = (pts: { x: number; y: number }[], fill: number) => {
            g.fillStyle(fill, 1).beginPath().moveTo(pts[0].x, pts[0].y);
            pts.slice(1).forEach((p) => g.lineTo(p.x, p.y));
            g.closePath().fillPath();
        };
        quad([iso(-6, -3), iso(6, -3), iso(6, 0), iso(-6, 0)], 0x8a8580);        // pavement
        quad([iso(-6, 0), iso(6, 0), iso(6, 0, 4), iso(-6, 0, 4)], 0xb4aea6);    // frontage
        this.world.add(g);

        const run = runData(this.stationData, this.state.run);
        this.add.graphics().fillStyle(colour.ink, 0.9).fillRoundedRect(FRAME.width / 2 - 520, 800, 1040, 230, 18);
        this.add.text(FRAME.width / 2, 860, `${this.stationData.number} · ${this.stationData.title}`, {
            fontFamily: font.display, fontSize: 56, fontStyle: '800', color: css.cream,
        }).setOrigin(0.5);
        this.add.text(FRAME.width / 2, 930, `${run.summary ?? ''}${run.proposed ? '  (Proposed)' : ''}`, {
            fontFamily: font.body, fontSize: 28, color: css.cream,
        }).setOrigin(0.5);
        this.add.text(FRAME.width / 2, 990, 'Grey box · built in tasks/', {
            fontFamily: font.body, fontSize: 22, color: '#8F877C',
        }).setOrigin(0.5);

        const tag = this.state.kilo.tag;
        if (tag) new KiloTag(this, FRAME.width - 260, 20, tag, this.state.reducedMotion).setDepth(30);   // HUD dock, left of the "i"
        this.prompt.show('Station 2 is a grey box for now', undefined);
        this.cameras.main.setBackgroundColor(colour.void);
    }
}
