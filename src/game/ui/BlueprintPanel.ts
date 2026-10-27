// Blueprint toggle (B): the station's row of the service blueprint, five lanes, synced to the station.
// Items that are our proposal carry a "Proposed" chip (truth rules).
import { GameObjects, Scene } from 'phaser';
import { LANE_LABELS, type BlueprintItem, type Lane, type StationData } from '../content';
import type { Run } from '../state';
import { isPhone } from '../device';
import { colour, css, font, FRAME, layout, motion } from '../theme';
import { drawCard, drawChip } from './card';

const LANES: Lane[] = ['vendor', 'frontstage', 'backstage', 'support', 'evidence'];
const LANE_ACCENT: Partial<Record<Lane, number>> = { backstage: colour.offsite };

export class BlueprintPanel extends GameObjects.Container {
    private open = false;

    constructor(scene: Scene, station: StationData, run: Run, items: BlueprintItem[], private reducedMotion = false) {
        super(scene, 0, FRAME.height);
        const x = layout.gutter, w = FRAME.width - layout.gutter * 2, h = layout.blueprintHeight + 24;
        const g = scene.add.graphics();
        drawCard(g, x, 0, w, h);
        this.add(g);

        const runLabel = run === 1 ? 'Run 1 · Today' : 'Run 2 · With the hub';
        this.add(scene.add.text(x + 32, 26, `Service blueprint · ${station.number} ${station.title}`, {
            fontFamily: font.display, fontSize: 30, fontStyle: '700', color: css.ink,
        }));
        this.add(scene.add.text(x + w - 32, 30, `${runLabel}   ·   ${isPhone() ? 'Tap Blueprint to close' : 'B to close'}`, {
            fontFamily: font.body, fontSize: 22, color: css.muted,
        }).setOrigin(1, 0));

        const top = 82, rowH = 64, labelW = 250;
        LANES.forEach((lane, i) => {
            const y = top + i * rowH;
            const rule = scene.add.graphics();
            rule.lineStyle(1, colour.ink, 0.18).lineBetween(x + 24, y, x + w - 24, y);
            if (LANE_ACCENT[lane]) rule.fillStyle(LANE_ACCENT[lane]!, 1).fillRect(x + 24, y + 14, 6, rowH - 28);
            this.add(rule);
            this.add(scene.add.text(x + 44, y + rowH / 2, LANE_LABELS[lane], {
                fontFamily: font.display, fontSize: 24, fontStyle: '700', color: css.ink,
            }).setOrigin(0, 0.5));
            const item = items.find((it) => it.lane === lane);
            let tx = x + 44 + labelW;
            if (item?.proposed) {
                const chip = scene.add.graphics();
                drawChip(chip, tx, y + rowH / 2 - 16, 118, 32, colour.cream, colour.brown);
                this.add(chip);
                this.add(scene.add.text(tx + 59, y + rowH / 2, 'Proposed', {
                    fontFamily: font.display, fontSize: 19, fontStyle: '700', color: css.brown,
                }).setOrigin(0.5));
                tx += 134;
            }
            this.add(scene.add.text(tx, y + rowH / 2, item?.text ?? '—', {
                fontFamily: font.body, fontSize: 26, color: item ? css.ink : css.muted,
                wordWrap: { width: x + w - 330 - tx },
            }).setOrigin(0, 0.5));
            if (item?.evidence.length) {
                this.add(scene.add.text(x + w - 32, y + rowH / 2, item.evidence.join(' · '), {
                    fontFamily: font.body, fontSize: 16, color: css.muted, align: 'right', wordWrap: { width: 290 },
                }).setOrigin(1, 0.5));
            }
        });
        this.setDepth(80);
        scene.add.existing(this);
    }

    get isOpen() {
        return this.open;
    }

    toggle(force?: boolean) {
        this.open = force ?? !this.open;
        const y = this.open ? layout.blueprintTop : FRAME.height;
        if (this.reducedMotion) this.setY(y);
        else this.scene.tweens.add({ targets: this, y, duration: motion.normal + 60, ease: this.open ? 'Cubic.easeOut' : 'Cubic.easeIn' });
        return this.open;
    }
}
