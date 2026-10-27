// The briefing: a deck card that says what a beat's minigame is and how to play it. A header with the
// station's number badge, title, place and time of day; the goal; one tile per step with its keys and
// mouse; the always-on controls; and a big button. Shown before each beat (StationCard) and over a
// paused beat on H (HowTo). Text from howto.json; the station's own title and place from its data.
import { GameObjects, Scene } from 'phaser';
import marketMap from '../../data/map.json';
import { hasStation, howTo, howToText, runs, station } from '../content';
import { getState, type Run } from '../state';
import { colour, css, font, FRAME, hud, motion } from '../theme';
import { drawCard, drawChip } from './card';
import { drawPhaseIcon, phaseLabel } from './Clock';
import { inputRow, keycap } from './keys';

const CARD = { w: 1440, h: 740 };

/** Number badge, title and place for a beat key ("s01", "s01:night", "map"). */
export function beatTitle(beat: string): { badge: string; title: string; place: string } {
    const [id, variant] = beat.split(':');
    if (id === 'map') return { badge: 'MAP', title: marketMap.title, place: 'Shivajinagar' };
    if (!hasStation(id)) return { badge: '?', title: id, place: '' };
    const s = station(id);
    return {
        badge: String(s.number).padStart(2, '0'),
        title: `${s.title}${s.label ? ` · ${s.label}` : ''}`,
        place: variant === 'night' ? `${s.place} · that night` : s.place,
    };
}

export function hasBriefing(run: Run, beat: string) {
    return !!howTo(run, beat);
}

/** The card, centred on the frame. `onGo` runs on the button (callers bind their own keys too). */
export function briefingCard(scene: Scene, run: Run, beat: string, cta: string, onGo: () => void): GameObjects.Container {
    const info = howTo(run, beat)!;
    const head = beatTitle(beat);
    const phase = runs[run].clock?.[beat];
    const left = -CARD.w / 2, top = -CARD.h / 2;
    const c = scene.add.container(FRAME.width / 2, FRAME.height / 2);
    const add = <T extends GameObjects.GameObject>(o: T) => (c.add(o), o);

    const g = add(scene.add.graphics());
    g.fillStyle(hud.shadow, 0.4).fillRoundedRect(left + 6, top + 12, CARD.w, CARD.h, 18);
    drawCard(g, left, top, CARD.w, CARD.h, run === 1 ? colour.cost : colour.income);

    // header: badge, title, place · phase, run chip
    const bx = left + 92, by = top + 104;
    g.fillStyle(colour.pay, 1).fillCircle(bx, by, 50).lineStyle(4, colour.ink, 1).strokeCircle(bx, by, 50);
    add(scene.add.text(bx, by + 2, head.badge, { fontFamily: font.display, fontSize: head.badge.length > 2 ? 30 : 46, fontStyle: '800', color: css.ink }).setOrigin(0.5));
    add(scene.add.text(left + 168, by - 22, head.title, { fontFamily: font.display, fontSize: 54, fontStyle: '800', color: css.ink }).setOrigin(0, 0.5));
    const place = add(scene.add.text(left + 170, by + 32, head.place, { fontFamily: font.body, fontSize: 26, color: css.muted }).setOrigin(0, 0.5));
    if (phase) {
        const px = place.x + place.width + 30;
        drawPhaseIcon(g, px + 16, by + 40, phase, 14, colour.ink, colour.card);
        add(scene.add.text(px + 42, by + 32, phaseLabel(phase), { fontFamily: font.body, fontSize: 26, color: css.muted }).setOrigin(0, 0.5));
    }
    const runText = add(scene.add.text(0, by - 22, runs[run].title, { fontFamily: font.display, fontSize: 24, fontStyle: '700', color: css.cream }).setOrigin(1, 0.5));
    const chipW = runText.width + 36, chipX = -left - 40 - chipW;
    drawChip(g, chipX, by - 42, chipW, 40, run === 1 ? colour.cost : colour.income);
    runText.setX(chipX + chipW - 18);
    if (runs[run].proposed) {
        const p = add(scene.add.text(-left - 58, by + 30, 'Proposed', { fontFamily: font.display, fontSize: 20, fontStyle: '700', color: css.cream }).setOrigin(1, 0.5));
        drawChip(g, p.x - p.width - 18, by + 14, p.width + 36, 32, colour.brown);
    }
    g.lineStyle(2, colour.ink, 0.15).lineBetween(left + 40, top + 182, -left - 40, top + 182);

    // goal
    const gy = top + 228;
    const goalLabel = add(scene.add.text(left + 60, gy, howToText.briefing.goal.toUpperCase(), { fontFamily: font.display, fontSize: 20, fontStyle: '800', color: css.cream }).setOrigin(0, 0.5).setLetterSpacing(2));
    drawChip(g, left + 40, gy - 18, goalLabel.width + 40, 36, colour.ink);
    add(scene.add.text(left + 40 + goalLabel.width + 60, gy, info.goal, { fontFamily: font.display, fontSize: 34, fontStyle: '700', color: css.ink }).setOrigin(0, 0.5));
    if (info.tip) add(scene.add.text(left + 40, gy + 42, info.tip, { fontFamily: font.body, fontSize: 22, color: css.muted }).setOrigin(0, 0.5));

    // step tiles
    const n = info.steps.length, gap = 24;
    const tw = (CARD.w - 80 - gap * (n - 1)) / n, ty = top + (info.tip ? 300 : 282), th = 300;
    info.steps.forEach((st, i) => {
        const tx = left + 40 + i * (tw + gap);
        g.fillStyle(colour.cream, 1).fillRoundedRect(tx, ty, tw, th, 14);
        g.lineStyle(2, colour.ink, 0.5).strokeRoundedRect(tx, ty, tw, th, 14);
        g.fillStyle(colour.ink, 1).fillCircle(tx + 34, ty + 36, 20);
        add(scene.add.text(tx + 34, ty + 37, String(i + 1), { fontFamily: font.display, fontSize: 24, fontStyle: '800', color: css.pay }).setOrigin(0.5));
        add(scene.add.text(tx + 66, ty + 37, st.label, { fontFamily: font.display, fontSize: 32, fontStyle: '800', color: css.ink }).setOrigin(0, 0.5));
        if (i < n - 1) add(scene.add.text(tx + tw + gap / 2, ty + th / 2, '›', { fontFamily: font.display, fontSize: 40, fontStyle: '800', color: css.brown }).setOrigin(0.5));
        const row = st.keys.length || st.mouse
            ? inputRow(scene, st.keys, st.mouse, 44, true)
            : add(scene.add.text(0, 0, 'Just watch', { fontFamily: font.display, fontSize: 24, fontStyle: '700', color: css.muted }).setOrigin(0.5));
        row.setPosition(tx + tw / 2, ty + 110);
        add(row);
        add(scene.add.text(tx + 24, ty + 156, st.text, { fontFamily: font.body, fontSize: 23, color: css.ink, wordWrap: { width: tw - 48 }, lineSpacing: 4 }));
    });

    // footer: the always-on controls, and the button
    const fy = -top - 64;
    let x = left + 48;
    const controls: [string, string][] = [['B', howToText.dock.blueprint], ['I', howToText.dock.evidence], ['H', howToText.dock.help], ['M', howToText.dock.menu]];
    for (const [k, label] of controls) {
        const cap = add(keycap(scene, k, 34));
        cap.setPosition(x + cap.width / 2, fy - 2);
        const t = add(scene.add.text(x + cap.width + 10, fy, label, { fontFamily: font.body, fontSize: 22, color: css.muted }).setOrigin(0, 0.5));
        x += cap.width + 10 + t.width + 30;
    }

    const bt = scene.add.text(0, 0, `${cta}  ▶`, { fontFamily: font.display, fontSize: 34, fontStyle: '800', color: css.cream }).setOrigin(0, 0.5);
    const cap = keycap(scene, 'Space', 34);
    const bw = bt.width + cap.width + 72, bh = 72;
    const btn = scene.add.container(-left - 40 - bw / 2, fy);
    const bg = scene.add.graphics();
    const draw = (hover: boolean) => {
        bg.clear().fillStyle(hud.shadow, 0.3).fillRoundedRect(-bw / 2, -bh / 2 + 5, bw, bh, bh / 2);
        bg.fillStyle(hover ? colour.brown : colour.ink, 1).fillRoundedRect(-bw / 2, -bh / 2, bw, bh, bh / 2);
        bg.lineStyle(3, colour.pay, hover ? 1 : 0.8).strokeRoundedRect(-bw / 2, -bh / 2, bw, bh, bh / 2);
    };
    draw(false);
    bt.setX(-bw / 2 + 30);
    cap.setPosition(bw / 2 - 30 - cap.width / 2, -2);
    btn.add([bg, bt, cap]).setSize(bw, bh);
    btn.setInteractive({ useHandCursor: true })
        .on('pointerover', () => draw(true)).on('pointerout', () => draw(false)).on('pointerup', onGo);
    add(btn);
    if (!getState(scene).reducedMotion) {
        scene.tweens.add({ targets: btn, scale: 1.04, duration: 700, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
        c.setAlpha(0).setY(c.y + 24);
        scene.tweens.add({ targets: c, alpha: 1, y: c.y - 24, duration: motion.normal + 80, ease: 'Cubic.easeOut' });
    }
    return c;
}
