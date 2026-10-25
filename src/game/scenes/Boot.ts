// Boot: wait for the deck fonts, draw the void lattice texture, start the first station.
import { Scene } from 'phaser';
import { parseBeat, sceneFor } from '../flow';
import { getState } from '../state';

export class Boot extends Scene {
    constructor() {
        super('Boot');
    }

    async create() {
        await Promise.all([
            document.fonts.load('800 56px "Baloo 2"'),
            document.fonts.load('700 40px "Baloo 2"'),
            document.fonts.load('600 32px "Baloo 2"'),
            document.fonts.load('400 28px Hind'),
        ]).catch(() => undefined);
        this.makeLattice();
        const { run, beat } = getState(this);
        const first = parseBeat(run, beat);
        this.scene.start(sceneFor(this, first), { beat: first });
    }

    /** The deck's diamond lattice at 5% on the charcoal void (art-bible §6.1). */
    private makeLattice() {
        const s = 96;
        const tex = this.textures.createCanvas('lattice', s, s)!;
        const ctx = tex.getContext();
        ctx.fillStyle = '#1C1714';
        ctx.fillRect(0, 0, s, s);
        ctx.strokeStyle = 'rgba(244, 236, 222, 0.05)';
        ctx.lineWidth = 2;
        for (const r of [40, 26, 12]) {
            ctx.beginPath();
            ctx.moveTo(s / 2, s / 2 - r);
            ctx.lineTo(s / 2 + r, s / 2);
            ctx.lineTo(s / 2, s / 2 + r);
            ctx.lineTo(s / 2 - r, s / 2);
            ctx.closePath();
            ctx.stroke();
        }
        ctx.beginPath();
        ctx.arc(0, 0, 5, 0, Math.PI * 2);
        ctx.stroke();
        tex.refresh();
    }
}
