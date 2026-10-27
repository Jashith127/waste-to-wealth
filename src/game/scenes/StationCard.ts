// Between beats. On first load, the title screen; when the run changes, "Run 2 · With the hub"; then the
// beat's briefing (how to play, waits for Space or a click). Without a briefing (the end card, or
// ?noBrief), the old title card: "2 · The walk" and the place, faded in and out.
import { GameObjects, Scene } from 'phaser';
import { howToText, runs } from '../content';
import { sceneFor, type Beat } from '../flow';
import { LOCALES, locale, setLocale, tr } from '../i18n';
import { getState } from '../state';
import { colour, css, font, FRAME, motion } from '../theme';
import { beatTitle, briefingCard, hasBriefing } from '../ui/Briefing';
import { keycap } from '../ui/keys';

export class StationCard extends Scene {
    private waiting?: () => void;

    constructor() {
        super('StationCard');
    }

    create({ beat, runChanged, intro }: { beat: Beat; runChanged?: boolean; intro?: boolean }) {
        this.waiting = undefined;
        this.add.tileSprite(0, 0, FRAME.width, FRAME.height, 'lattice').setOrigin(0);
        const { briefings, reducedMotion } = getState(this);
        const key = runs[beat.run].beats[beat.index];
        const brief = beat.station !== 'end' && briefings && key !== undefined && hasBriefing(beat.run, key);
        const start = () => this.scene.start(sceneFor(this, beat), { beat });

        const kb = this.input.keyboard!;
        const go = (e?: KeyboardEvent) => { if (!e?.repeat && this.waiting) { const w = this.waiting; this.waiting = undefined; w(); } };
        kb.on('keydown-SPACE', go);
        kb.on('keydown-ENTER', go);
        kb.on('keydown-RIGHT', go);

        const steps: ((next: () => void) => void)[] = [];
        if (intro && briefings) steps.push((next) => this.titleScreen(next));
        if (runChanged) steps.push((next) => this.fadeCard(runs[beat.run].title, runs[beat.run].subtitle, next));
        if (brief) {
            steps.push(() => {
                this.add.image(0, 0, 'skyline').setOrigin(0).setAlpha(0.6);
                this.add.rectangle(0, 0, FRAME.width, FRAME.height, colour.void, 0.35).setOrigin(0);
                this.waiting = start;
                briefingCard(this, beat.run, key, howToText.briefing.start, () => go());
            });
        } else if (key !== undefined && /^s\d/.test(key)) {
            const t = beatTitle(key);
            steps.push((next) => this.fadeCard(`${t.badge.replace(/^0/, '')} · ${t.title}`, t.place, next));
        }
        steps.push(start);
        const run = (i: number) => steps[i]?.(() => run(i + 1));
        if (!reducedMotion) this.cameras.main.fadeIn(motion.normal, 28, 23, 20);
        run(0);
    }

    /** "Waste to Wealth": the game's name over the skyline, until Space or a click. */
    private titleScreen(next: () => void) {
        const t = howToText.briefing;
        const parts: GameObjects.GameObject[] = [
            this.add.image(0, 0, 'skyline').setOrigin(0),
            this.add.text(FRAME.width / 2, 400, t.title, { fontFamily: font.display, fontSize: 132, fontStyle: '800', color: css.cream }).setOrigin(0.5).setShadow(0, 8, '#000000', 0, false, true),
            this.add.text(FRAME.width / 2, 500, t.tagline, { fontFamily: font.body, fontSize: 36, color: '#D8CCB8' }).setOrigin(0.5),
        ];
        const g = this.add.graphics();
        g.fillStyle(colour.pay, 1).fillRect(FRAME.width / 2 - 180, 560, 360, 6);
        const press = this.add.container(FRAME.width / 2, 700);
        // "Press [Space] to begin": the cap sits where the word was
        const [before, after = ''] = tr(t.press).split('Space');     // every translation keeps the key's name
        const style = { fontFamily: font.display, fontSize: 38, fontStyle: '700', color: css.cream };
        const label = this.add.text(0, 0, before.trim(), style).setOrigin(0, 0.5);
        const cap = keycap(this, 'Space', 48);
        const tail = this.add.text(0, 0, after.trim(), style).setOrigin(0, 0.5);
        const w = label.width + 16 + cap.width + 16 + tail.width;
        label.setX(-w / 2);
        cap.setPosition(-w / 2 + label.width + 16 + cap.width / 2, -2);
        tail.setX(-w / 2 + label.width + 32 + cap.width);
        press.add([label, cap, tail]);
        if (!getState(this).reducedMotion) this.tweens.add({ targets: press, alpha: 0.45, duration: 800, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
        const hit = this.add.zone(0, 0, FRAME.width, FRAME.height).setOrigin(0).setInteractive({ useHandCursor: true });
        const done = () => {
            hit.destroy();
            [...parts, g, press].forEach((o) => o.destroy());
            next();
        };
        hit.once('pointerup', () => { if (this.waiting === done) { this.waiting = undefined; done(); } });
        const langs = this.languages();
        this.input.keyboard!.on('keydown-L', () => {
            if (this.waiting !== done) return;
            const i = LOCALES.findIndex((l) => l.id === locale);
            setLocale(LOCALES[(i + 1) % LOCALES.length].id);
        });
        parts.push(...langs);
        this.waiting = done;
    }

    /** The language row under the title: each language named in its own script; L cycles. */
    private languages() {
        const w = 200, gap = 20, y = 860;
        const x0 = FRAME.width / 2 - (LOCALES.length * w + (LOCALES.length - 1) * gap) / 2 + w / 2;
        const out: GameObjects.GameObject[] = [];
        LOCALES.forEach((l, i) => {
            const on = l.id === locale;
            const g = this.add.graphics();
            const draw = (hover: boolean) => {
                g.clear().fillStyle(on ? colour.pay : colour.ink, on ? 1 : 0.85).fillRoundedRect(-w / 2, -32, w, 64, 32);
                g.lineStyle(2.5, on || hover ? colour.pay : colour.cream, on || hover ? 1 : 0.3).strokeRoundedRect(-w / 2, -32, w, 64, 32);
            };
            draw(false);
            const t = this.add.text(0, 0, l.name, { fontFamily: font.display, fontSize: 30, fontStyle: '700', color: on ? css.ink : css.cream }).setOrigin(0.5);
            const b = this.add.container(x0 + i * (w + gap), y, [g, t]).setSize(w, 64);
            b.setInteractive({ useHandCursor: true }).on('pointerover', () => draw(true)).on('pointerout', () => draw(false))
                .on('pointerup', () => { if (!on) setLocale(l.id); });
            out.push(b);
        });
        const hint = this.add.container(FRAME.width / 2, y + 62);
        const cap = keycap(this, 'L', 30);
        const label = this.add.text(0, 0, 'Language', { fontFamily: font.body, fontSize: 22, color: '#B8AE9C' }).setOrigin(0, 0.5);
        cap.setX(-(cap.width + 10 + label.width) / 2 + cap.width / 2);
        label.setX(cap.x + cap.width / 2 + 10);
        hint.add([cap, label]);
        out.push(hint);
        return out;
    }

    private fadeCard(t: string, sub: string, next: () => void) {
        const title = this.add.text(FRAME.width / 2, FRAME.height / 2 - 10, t, {
            fontFamily: font.display, fontSize: 72, fontStyle: '800', color: css.cream,
        }).setOrigin(0.5).setAlpha(0);
        const place = this.add.text(FRAME.width / 2, FRAME.height / 2 + 62, sub, {
            fontFamily: font.body, fontSize: 30, color: '#B8AE9C', align: 'center', wordWrap: { width: 1300 },
        }).setOrigin(0.5, 0).setAlpha(0);
        this.tweens.add({
            targets: [title, place], alpha: 1, duration: motion.normal, hold: 900, yoyo: true,
            onComplete: () => { title.destroy(); place.destroy(); next(); },
        });
    }
}
