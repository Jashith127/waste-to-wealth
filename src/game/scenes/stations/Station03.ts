// Station 3 · Weigh-in and payment, the hub's front counter (Run 2).
// Drag the crate onto the platform scale, say the number, watch the attendant type it, then the
// UPI ping flips the tag from −₹5 to +₹[__]. Every rate is ₹[__]/kg: no payout is invented.
//
// Layers and anchors come from the lead's final s03 art (lead/s03-art): bg, crate + crate_shadow,
// riyaz_idle, attendant_idle, attendant_type, and the scale_pan / scale_display / rate_board /
// attendant_phone / door_a / door_b anchors.
import { GameObjects } from 'phaser';
import { station } from '../../content';
import { setState, type KiloTagState } from '../../state';
import { colour, css, font, layout, motion } from '../../theme';
import { drawCard, drawChip } from '../../ui/card';
import { KiloTag } from '../../ui/KiloTag';
import { StationScene } from '../StationScene';

type Phase = 'drag' | 'number' | 'wait' | 'paid' | 'leave';

interface S03Params {
    weight_label: string;
    rate_board: { line: string; rate: string }[];
    rate_note: string;
    speech: string;
    number_masked: string;
    slip: { title: string; lines: string[] };
    tag_after: KiloTagState;
}

// The crate's 3D centre sits half its height (0.15 m) above the scale pan: 22.7 px at 151.6 px/m.
const CRATE_HALF_PX = 22.7;
const SNAP_PX = 90;

export default class Station03 extends StationScene {
    private phase: Phase = 'drag';
    private crate!: GameObjects.Image;
    private shadow!: GameObjects.Image;
    private attendantIdle!: GameObjects.Image;
    private attendantType!: GameObjects.Image;
    private tag!: KiloTag;
    private ring?: GameObjects.Arc;

    private dragging = false;
    private grab = { x: 0, y: 0 };
    private crateStart = { x: 0, y: 0 };
    private centreOffset = { x: 0, y: 0 };
    private shadowOffset = { x: 0, y: 0 };

    private speechCard?: GameObjects.Container;
    private numberCard?: GameObjects.Container;
    private exitButton?: GameObjects.Container;
    private left = false;

    constructor() {
        super('s03');
    }

    preload() {
        this.loadLayers();
    }

    protected build() {
        this.phase = 'drag';
        this.dragging = false;
        this.left = false;

        this.layer('bg');
        this.shadow = this.layer('crate_shadow');
        this.layer('riyaz_idle');
        this.attendantIdle = this.layer('attendant_idle');
        this.attendantType = this.layer('attendant_type').setVisible(false);
        this.crate = this.layer('crate');           // last in the world, so it drags above Riyaz

        this.crateStart = { x: this.crate.x, y: this.crate.y };
        const centre = this.anchor('crate_centre');
        this.centreOffset = { x: centre.x - this.crate.x, y: centre.y - this.crate.y };
        this.shadowOffset = { x: this.shadow.x - this.crate.x, y: this.shadow.y - this.crate.y };

        // The value tag is docked in the HUD band by now: the kilo is in the crate, not in his hand.
        const tagData = this.state.kilo.tag ?? station('s01').kilo!.tag;
        this.tag = new KiloTag(this, 1660, 20, tagData, this.state.reducedMotion).setDepth(30);

        this.drawChambers();
        this.drawRateBoard();

        const kb = this.input.keyboard!;
        const once = (fn: () => void) => (e: KeyboardEvent) => { if (!e.repeat) fn(); };
        kb.on('keydown-SPACE', once(() => this.press()));
        kb.on('keydown-ENTER', once(() => this.press()));
        kb.on('keydown-RIGHT', once(() => this.press()));

        this.input.on('pointerdown', (p: Phaser.Input.Pointer) => this.grabCrate(p));
        this.input.on('pointermove', (p: Phaser.Input.Pointer) => {
            if (!this.dragging) return;
            this.crate.setPosition(p.x - this.grab.x, p.y - this.grab.y);
        });
        this.input.on('pointerup', () => this.release());

        this.prompt.show(this.prompts().drag, 'Space');
        const c = this.crateCentre();
        this.ring = this.hint(c.x, c.y, 78);
    }

    /** Space/Enter/→ walks the beat forward; the pointer handles the drag and the spoken number. */
    private press() {
        if (this.phase === 'drag') this.snap();
        else if (this.phase === 'number') this.sayNumber();
        else if (this.phase === 'leave') this.leave();
    }

    private crateCentre() {
        return { x: this.crate.x + this.centreOffset.x, y: this.crate.y + this.centreOffset.y };
    }

    private grabCrate(p: Phaser.Input.Pointer) {
        if (this.phase !== 'drag' || this.dragging) return;
        if (!this.crate.getBounds().contains(p.x, p.y)) return;
        this.dragging = true;
        this.grab = { x: p.x - this.crate.x, y: p.y - this.crate.y };
        this.ring?.destroy();
        this.ring = undefined;
        if (!this.state.reducedMotion) this.tweens.add({ targets: this.shadow, alpha: 0, duration: motion.fast });
        else this.shadow.setAlpha(0);
    }

    /** Drop: within 90 px of the pan it snaps and weighs; otherwise the crate springs back. */
    private release() {
        if (this.phase === 'drag' && this.dragging) {
            this.dragging = false;
            const c = this.crateCentre();
            const pan = this.anchor('scale_pan');
            if (Math.hypot(c.x - pan.x, c.y - pan.y) <= SNAP_PX) this.snap();
            else this.springBack();
            return;
        }
        if (this.phase === 'number') this.sayNumber();
    }

    private springBack() {
        const to = { x: this.crateStart.x, y: this.crateStart.y };
        if (this.state.reducedMotion) {
            this.crate.setPosition(to.x, to.y);
            this.shadow.setPosition(to.x + this.shadowOffset.x, to.y + this.shadowOffset.y).setAlpha(1);
        } else {
            this.tweens.add({ targets: this.crate, ...to, duration: 260, ease: 'Back.easeOut' });
            this.tweens.add({
                targets: this.shadow, x: to.x + this.shadowOffset.x, y: to.y + this.shadowOffset.y,
                alpha: 1, duration: 260, delay: 60,
            });
        }
        const c = this.crateCentre();
        this.ring = this.hint(c.x, c.y, 78);
    }

    /** Place the crate on the scale, show 1.0 kg, and hand the beat to the spoken number. */
    private snap() {
        this.dragging = false;
        this.ring?.destroy();
        this.ring = undefined;
        this.phase = 'number';

        const pan = this.anchor('scale_pan');
        const to = {
            x: pan.x - this.centreOffset.x,
            y: pan.y - CRATE_HALF_PX - this.centreOffset.y,
        };
        const shadowTo = { x: to.x + this.shadowOffset.x, y: to.y + this.shadowOffset.y };
        if (this.state.reducedMotion) {
            this.crate.setPosition(to.x, to.y);
            this.shadow.setPosition(shadowTo.x, shadowTo.y).setAlpha(1);
        } else {
            this.tweens.add({ targets: this.crate, ...to, duration: 240, ease: 'Cubic.easeOut' });
            this.tweens.add({ targets: this.shadow, ...shadowTo, alpha: 0.85, duration: motion.normal, delay: 120 });
        }

        setState(this, { kilo: { carried: false, tag: this.state.kilo.tag } });
        this.popCard(this.scaleDisplayCard(), this.state.reducedMotion);
        this.prompt.show(this.prompts().number, 'Space');
    }

    /** Riyaz says the number; the attendant switches to the phone and masks it. */
    private sayNumber() {
        if (this.phase !== 'number') return;
        this.phase = 'wait';
        this.prompt.show(this.prompts().wait);

        this.speechCard = this.popCard(this.speechBubble(), this.state.reducedMotion);
        this.attendantIdle.setVisible(false);
        this.attendantType.setVisible(true);

        this.time.delayedCall(220, () => {
            this.numberCard = this.popCard(this.maskedNumberCard(), this.state.reducedMotion);
        });
        this.time.delayedCall(1000, () => this.paid());
    }

    /** UPI confirms by sound; the tag flips and the slip lands. */
    private paid() {
        if (this.phase !== 'wait') return;
        this.phase = 'paid';
        const p = this.params();

        this.events.emit('sfx', 'upi_ping');
        this.tag.flipTo({ ...p.tag_after });
        setState(this, { kilo: { carried: false, tag: { ...p.tag_after } } });

        this.prompt.show(this.prompts().paid);
        this.fadeOut(this.speechCard);
        this.fadeOut(this.numberCard);
        this.popCard(this.slip(), this.state.reducedMotion);

        this.time.delayedCall(this.state.reducedMotion ? 900 : 1800, () => this.toLeave());
    }

    private toLeave() {
        this.phase = 'leave';
        this.prompt.show(this.prompts().leave, 'Space');
        if (!this.exitButton) this.exitButton = this.makeExit();
    }

    // --- cards ---------------------------------------------------------------------------------

    /** The wall board is too small for readable rates, so the rates live on a card at the anchor. */
    private drawRateBoard() {
        const p = this.params();
        const a = this.anchor('rate_board');
        const w = 400, h = 246;
        const x = a.x - w / 2;
        const y = layout.blueprintTop - h - 10;

        const g = this.add.graphics();
        drawCard(g, 0, 0, w, h);
        const rows: GameObjects.Text[] = [];
        p.rate_board.forEach((row, i) => {
            const ty = 20 + i * 44;
            rows.push(this.add.text(20, ty, row.line, {
                fontFamily: font.body, fontSize: 28, color: css.ink,
            }).setOrigin(0, 0));
            rows.push(this.add.text(w - 20, ty, row.rate, {
                fontFamily: font.body, fontSize: 28, fontStyle: '600', color: css.brown,
            }).setOrigin(1, 0));
        });

        g.lineStyle(1, colour.ink, 0.25).lineBetween(18, 154, w - 18, 154);
        const note = this.add.text(20, 164, p.rate_note, {
            fontFamily: font.body, fontSize: 26, color: css.muted,
        }).setOrigin(0, 0);

        const chipW = 120, chipH = 32, chipY = h - 44;
        drawChip(g, 20, chipY, chipW, chipH, colour.brown, colour.brown);
        const chip = this.add.text(20 + chipW / 2, chipY + chipH / 2, 'Proposed', {
            fontFamily: font.display, fontSize: 22, fontStyle: '700', color: css.cream,
        }).setOrigin(0.5);

        this.add.container(x, y, [g, ...rows, note, chip]).setDepth(16);
    }

    /** The cold-room door bands get their words here: no words are baked into the render. */
    private drawChambers() {
        this.doorLabel('door_a', 'Chamber A', colour.income);
        this.doorLabel('door_b', 'Chamber B', colour.offsite);
    }

    private doorLabel(anchor: string, text: string, accent: number) {
        const a = this.anchor(anchor);
        const w = 148, h = 34;
        const g = this.add.graphics();
        g.fillStyle(colour.card, 0.96).fillRoundedRect(-w / 2, -h / 2, w, h, 8);
        g.lineStyle(2, accent, 1).strokeRoundedRect(-w / 2, -h / 2, w, h, 8);
        const label = this.add.text(0, 0, text, {
            fontFamily: font.display, fontSize: 21, fontStyle: '700', color: accent === colour.income ? css.income : css.offsite,
        }).setOrigin(0.5);
        this.add.container(a.x, a.y, [g, label]).setDepth(15);
    }

    private scaleDisplayCard() {
        const a = this.anchor('scale_display');
        const w = 150, h = 58;
        const g = this.add.graphics();
        drawCard(g, 0, 0, w, h);
        const t = this.add.text(w / 2, h / 2, this.params().weight_label, {
            fontFamily: font.display, fontSize: 30, fontStyle: '700', color: css.ink,
        }).setOrigin(0.5);
        return this.add.container(a.x - w / 2, a.y - h / 2, [g, t]).setDepth(18);
    }

    /** Riyaz speaks; his hands stay wet and empty (task 03: he never touches a phone). */
    private speechBubble() {
        const head = this.anchor('riyaz_head');
        const w = 300, h = 80;
        const x = head.x - w / 2, y = head.y - 150;
        const g = this.add.graphics();
        g.fillStyle(colour.card, 1);
        g.beginPath().moveTo(w / 2 - 14, h - 1).lineTo(w / 2, h + 24).lineTo(w / 2 + 14, h - 1).closePath().fillPath();
        g.lineStyle(3, colour.ink, 1);
        g.beginPath().moveTo(w / 2 - 14, h - 1).lineTo(w / 2, h + 24).lineTo(w / 2 + 14, h - 1).strokePath();
        drawCard(g, 0, 0, w, h);
        const t = this.add.text(w / 2, h / 2, this.params().speech, {
            fontFamily: font.body, fontSize: 28, color: css.ink,
        }).setOrigin(0.5);
        return this.add.container(x, y, [g, t]).setDepth(20);
    }

    /** The attendant's screen, beside the phone: the number is masked, never read out. */
    private maskedNumberCard() {
        const phone = this.anchor('attendant_phone');
        const w = 240, h = 64;
        const g = this.add.graphics();
        drawCard(g, 0, 0, w, h);
        const t = this.add.text(w / 2, h / 2, this.params().number_masked, {
            fontFamily: font.display, fontSize: 26, fontStyle: '600', color: css.ink,
        }).setOrigin(0.5);
        return this.add.container(850, phone.y - 148, [g, t]).setDepth(21);
    }

    /** The payment slip: the same two lines the WhatsApp message carries, and the proposal chip. */
    private slip() {
        const p = this.params();
        const w = 360, h = 236;
        const g = this.add.graphics();
        drawCard(g, 0, 0, w, h, colour.income);
        const title = this.add.text(24, 34, p.slip.title, {
            fontFamily: font.display, fontSize: 34, fontStyle: '700', color: css.ink,
        }).setOrigin(0, 0);
        g.lineStyle(1, colour.ink, 0.2).lineBetween(22, 92, w - 22, 92);
        const lines = p.slip.lines.map((line, i) => this.add.text(24, 108 + i * 42, line, {
            fontFamily: font.body, fontSize: 28, color: i === 1 ? css.income : css.ink,
        }).setOrigin(0, 0));
        const done = this.add.text(w - 26, 34, '✓', {
            fontFamily: font.display, fontSize: 34, fontStyle: '700', color: css.income,
        }).setOrigin(1, 0);

        const chipW = 120, chipH = 32, chipY = h - 48;
        drawChip(g, 20, chipY, chipW, chipH, colour.brown, colour.brown);
        const chip = this.add.text(20 + chipW / 2, chipY + chipH / 2, 'Proposed', {
            fontFamily: font.display, fontSize: 22, fontStyle: '700', color: css.cream,
        }).setOrigin(0.5);

        // Left of the docked tag: its long payout note hangs past the card and must stay readable.
        return this.add.container(1120, 110, [g, title, ...lines, done, chip]).setDepth(22);
    }

    /** A card that rises in. Reduced motion shows it already in place. */
    private popCard(card: GameObjects.Container, reduced: boolean) {
        if (reduced) return card.setAlpha(1);
        card.setAlpha(0);
        this.tweens.add({ targets: card, alpha: 1, y: { from: card.y + 12, to: card.y }, duration: motion.normal, ease: 'Sine.easeOut' });
        return card;
    }

    private fadeOut(card?: GameObjects.Container) {
        if (!card) return;
        if (this.state.reducedMotion) card.destroy();
        else this.tweens.add({ targets: card, alpha: 0, duration: motion.fast, onComplete: () => card.destroy() });
    }

    private makeExit() {
        const g = this.add.graphics();
        g.fillStyle(colour.ink, 0.92).fillRoundedRect(-190, -36, 380, 72, 36);
        const label = this.add.text(0, 0, '←  Into the cold room', {
            fontFamily: font.display, fontSize: 30, fontStyle: '700', color: css.cream,
        }).setOrigin(0.5);
        const b = this.add.container(240, 520, [g, label]).setSize(380, 72).setDepth(45).setAlpha(0);
        b.setInteractive({ useHandCursor: true }).on('pointerup', () => this.leave());
        if (this.state.reducedMotion) b.setAlpha(1);
        else this.tweens.add({ targets: b, alpha: 1, x: { from: 220, to: 240 }, duration: motion.normal });
        return b;
    }

    private params(): S03Params {
        return this.stationData.params as unknown as S03Params;
    }

    /** The base `leave()` slides the set left and calls goNext; guard so a double press cannot fire twice. */
    protected leave() {
        if (this.left) return;
        this.left = true;
        super.leave();
    }
}
