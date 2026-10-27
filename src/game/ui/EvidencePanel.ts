// Evidence (I, or the dock's button): which field photos, interviews and reports this station rests on.
import { GameObjects, Scene } from 'phaser';
import { source, type StationData } from '../content';
import { colour, css, font, layout, motion } from '../theme';
import { drawCard, drawChip } from './card';

const KIND_LABEL: Record<string, string> = {
    'field-photo': 'Our photo',
    deck: 'Our field deck',
    'external-photo': 'Open-licence photo',
    map: 'Map data',
    report: 'News report',
    proposal: 'Our proposal',
};

export class EvidencePanel extends GameObjects.Container {
    private open = false;

    constructor(scene: Scene, station: StationData, private reducedMotion = false) {
        // the card opens above the control dock, over its Evidence button (Hud)
        const w = 720;
        const rows = station.evidence.map((id) => ({ id, src: source(id) }));
        const rowH = 58, h = 92 + rows.length * rowH;
        super(scene, layout.dock.x, layout.dock.y - layout.dock.h / 2 - 16 - h);
        const g = scene.add.graphics();
        drawCard(g, 0, 0, w, h, colour.ink);
        this.add(g);
        this.add(scene.add.text(28, 34, `Evidence · ${station.number} ${station.title}`, {
            fontFamily: font.display, fontSize: 28, fontStyle: '700', color: css.ink,
        }));
        rows.forEach(({ id, src }, k) => {
            const y = 88 + k * rowH;
            const chip = scene.add.graphics();
            drawChip(chip, 28, y, 190, 36, src.proposed ? colour.cream : colour.card, src.proposed ? colour.brown : colour.ink);
            this.add(chip);
            this.add(scene.add.text(123, y + 18, id, { fontFamily: font.display, fontSize: 17, fontStyle: '700', color: src.proposed ? css.brown : css.ink }).setOrigin(0.5));
            const kind = src.proposed ? 'Proposed · ' + KIND_LABEL[src.kind] : KIND_LABEL[src.kind] ?? src.kind;
            const extra = src.licence ? ` · ${src.licence}${src.credit ? ', ' + src.credit : ''}` : src.deck_page ? ` · p. ${src.deck_page}` : '';
            this.add(scene.add.text(234, y + 2, src.title ?? src.file ?? id, {
                fontFamily: font.body, fontSize: 21, color: css.ink, wordWrap: { width: w - 258 }, maxLines: 1,
            }));
            this.add(scene.add.text(234, y + 28, kind + extra, { fontFamily: font.body, fontSize: 17, color: css.muted }));
        });
        this.setDepth(70).setVisible(false).setAlpha(0);
        scene.add.existing(this);
    }

    get isOpen() {
        return this.open;
    }

    toggle(force?: boolean) {
        this.open = force ?? !this.open;
        if (this.open) this.setVisible(true);
        this.scene.tweens.add({
            targets: this, alpha: this.open ? 1 : 0, duration: this.reducedMotion ? 1 : motion.fast,
            onComplete: () => this.setVisible(this.open),
        });
        return this.open;
    }
}
