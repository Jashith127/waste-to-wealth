// Boot: wait for the deck fonts, draw the void lattice and the skyline backdrop, start the first station.
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
        this.makeSkyline();
        this.makeHaze();
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

    /** The skyline beyond the diorama (V01, V05): a painted theatre backdrop in tones just above the
     * void, so the empty corners of every set open onto the neighbourhood. Rooftops of 4-6 storey
     * blocks with parapets and water tanks, wires between poles, and the white minaret with its dome. */
    private makeSkyline() {
        const W = 1920, H = 1080;
        const tex = this.textures.createCanvas('skyline', W, H)!;
        const c = tex.getContext();
        let seed = 11;
        const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
        const base = 560;                                   // the blocks rise from behind the sets
        const far = 'rgba(70, 58, 50, 0.55)', near = 'rgba(52, 43, 37, 0.9)', win = 'rgba(120, 96, 70, 0.35)';
        // a far row, lower and paler, then the near row
        for (const [fill, lo, hi, w0, w1] of [[far, 330, 430, 50, 110], [near, 150, 360, 80, 170]] as const) {
            let x = -20;
            while (x < W) {
                const w = w0 + rnd() * (w1 - w0), top = lo + rnd() * (hi - lo);
                c.fillStyle = fill;
                c.fillRect(x, top, w, base - top);
                c.fillRect(x - 3, top - 8, w + 6, 8);                       // parapet
                if (fill === near) {
                    if (rnd() < 0.55) c.fillRect(x + w * 0.55, top - 30, 26, 22);   // a water tank
                    c.fillStyle = win;
                    for (let wy = top + 24; wy < base - 30; wy += 46) {
                        for (let wx = x + 12; wx < x + w - 20; wx += 30) if (rnd() < 0.7) c.fillRect(wx, wy, 14, 20);
                    }
                }
                x += w + rnd() * 14;
            }
        }
        // the minaret and its dome (V05), a little right of centre
        const mx = 1460;
        c.fillStyle = 'rgba(96, 86, 76, 0.9)';
        c.fillRect(mx - 13, 40, 26, base - 40);
        for (const y of [150, 260, 70]) c.fillRect(mx - 22, y, 44, 8);
        c.beginPath();
        c.ellipse(mx, 40, 22, 28, 0, Math.PI, 0);
        c.fillStyle = 'rgba(62, 96, 72, 0.85)';
        c.fill();
        c.fillRect(mx - 2, -2, 4, 16);
        // wires sagging between poles across the roofline
        c.strokeStyle = 'rgba(30, 24, 21, 0.9)';
        c.lineWidth = 2;
        for (const [x0, x1, y0, sag] of [[0, 620, 300, 50], [560, 1240, 260, 60], [1180, 1920, 320, 45], [200, 980, 340, 70]]) {
            c.beginPath();
            c.moveTo(x0, y0);
            c.quadraticCurveTo((x0 + x1) / 2, y0 + sag * 2, x1, y0);
            c.stroke();
        }
        c.fillStyle = 'rgba(30, 24, 21, 0.9)';
        for (const x of [620, 1240]) c.fillRect(x - 3, 250, 6, base - 250);
        tex.refresh();
    }

    /** A faint warm haze for daytime scenes: the morning air over the street, strongest at the top. */
    private makeHaze() {
        const tex = this.textures.createCanvas('haze', 8, 540)!;
        const c = tex.getContext();
        const g = c.createLinearGradient(0, 0, 0, 540);
        g.addColorStop(0, 'rgba(255, 236, 205, 0.10)');
        g.addColorStop(0.55, 'rgba(255, 236, 205, 0.03)');
        g.addColorStop(1, 'rgba(255, 236, 205, 0)');
        c.fillStyle = g;
        c.fillRect(0, 0, 8, 540);
        tex.refresh();
    }
}
