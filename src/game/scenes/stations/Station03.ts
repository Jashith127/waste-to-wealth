// Station 3 · Weigh-in and payment, the hub's front counter (Run 2).
// Drag the crate onto the platform scale, then talk it through with the attendant (Space per line):
// the weight, the rate, the number (masked on screen), and the UPI ping flips the tag from −₹5 to
// the estimated payout (≈₹3/kg sorted, ≈₹1/kg mixed; endcard.json payout_note says how).
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

type Phase = 'sort' | 'drag' | 'talk' | 'leave';
interface SortItem { label: string; kind: string; keep: boolean; why: string }
interface SortParams {
    title: string; keep_label: string; reject_label: string; keys: string; count: string; done: string; score: string;
    verdict_clean: string; verdict_mixed: string; verdict_lost: string; items: SortItem[];
}

interface TalkLine { who: 'riyaz' | 'attendant'; text: string; mixed?: string; do?: 'mask' | 'pay' }

interface S03Params {
    weight_label: string;
    rate_board: { line: string; rate: string }[];
    rate_note: string;
    number_masked: string;
    slip: { title: string; lines: string[]; lines_mixed: string[] };
    tag_after: KiloTagState;
    tag_after_mixed?: KiloTagState;
    talk: TalkLine[];
    speakers: Record<TalkLine['who'], string>;
    sort: SortParams;
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
    private left = false;

    constructor() {
        super('s03');
    }

    preload() {
        this.loadLayers();
        this.load.pack('s03items', 'assets/stations/s03items/pack.json');     // the sort's rendered items
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

        this.openTray();
    }

    // --- sort before you weigh (mini-game) -------------------------------------------------------
    //
    // The kilo comes out of the bag one piece at a time, the way it was swept off the block: bone,
    // offal, fat and skin, and the rubbish that gets in with them (a carry bag, a tea cup, twine,
    // newspaper, a foam tray). Each piece goes to the crate or the bin: ← / A, → / D, a click on
    // either side, or a drag. Every choice sticks: rubbish in the crate makes it a mixed crate (the
    // lower rate), meat waste in the bin is value thrown away. The rendered items are real models
    // (art/scripts/items_build.py), not icons.

    private sort?: {
        box: GameObjects.Container; item?: GameObjects.Container; queue: GameObjects.Image[]; count: GameObjects.Text;
        zones: Record<'crate' | 'bin', GameObjects.Container>; i: number; right: number; mixed: number; lost: number; busy: boolean;
    };
    private clean = true;

    private static readonly PANEL = { w: 1160, h: 560 };

    private openTray() {
        this.phase = 'sort';
        const p = this.params().sort;
        const { w, h } = Station03.PANEL;
        const box = this.add.container(960, layout.hudBottom + Station03.PANEL.h / 2 + 8).setDepth(40);   // clear of the objective card
        const g = this.add.graphics();
        drawCard(g, -w / 2, -h / 2, w, h, colour.brown);
        box.add(g);
        box.add(this.add.text(-w / 2 + 32, -h / 2 + 50, p.title, { fontFamily: font.display, fontSize: 36, fontStyle: '700', color: css.ink }).setOrigin(0, 0.5));
        const count = this.add.text(w / 2 - 32, -h / 2 + 50, '', { fontFamily: font.display, fontSize: 28, fontStyle: '700', color: css.muted }).setOrigin(1, 0.5);
        box.add(count);
        const zones = { crate: this.zone(box, 'crate', -w / 2 + 190, p.keep_label, '←'), bin: this.zone(box, 'bin', w / 2 - 190, p.reject_label, '→') };
        // the work surface in the middle: a steel tray the piece lands on
        const tray = this.add.graphics();
        tray.fillStyle(0xb9bdbc, 1).fillRoundedRect(-170, 10, 340, 150, 18).lineStyle(3, colour.ink, 0.5).strokeRoundedRect(-170, 10, 340, 150, 18);
        box.add(tray);
        box.add(this.add.text(0, h / 2 - 34, p.keys, { fontFamily: font.body, fontSize: 22, color: css.muted }).setOrigin(0.5));
        this.sort = { box, queue: [], count, zones, i: -1, right: 0, mixed: 0, lost: 0, busy: false };
        this.clean = true;

        const kb = this.input.keyboard!;
        const key = (k: string, to: 'crate' | 'bin') => kb.on(`keydown-${k}`, (e: KeyboardEvent) => { if (!e.repeat && this.phase === 'sort') this.choose(to); });
        key('LEFT', 'crate'); key('A', 'crate'); key('RIGHT', 'bin'); key('D', 'bin');

        this.prompt.show(this.prompts().sort, '← →');
        if (!this.state.reducedMotion) {
            box.setAlpha(0).setScale(0.96);
            this.tweens.add({ targets: box, alpha: 1, scale: 1, duration: motion.normal, ease: 'Back.easeOut' });
        }
        this.nextItem();
    }

    /** One side of the panel: the crate or the dustbin as rendered, its label and key, clickable. */
    private zone(box: GameObjects.Container, which: 'crate' | 'bin', x: number, label: string, key: string) {
        const z = this.add.container(x, 40);
        const g = this.add.graphics();
        g.fillStyle(colour.cream, 1).fillRoundedRect(-150, -170, 300, 380, 20);
        g.lineStyle(3, colour.ink, 0.35).strokeRoundedRect(-150, -170, 300, 380, 20);
        const img = this.add.image(0, 10, which === 'crate' ? 's03_crate' : 's03items_bin');
        img.setScale(Math.min(240 / img.width, 220 / img.height));
        const t = this.add.text(0, 150, label, { fontFamily: font.display, fontSize: 28, fontStyle: '700', color: css.ink }).setOrigin(0.5);
        const kg = this.add.graphics();
        kg.fillStyle(colour.ink, 1).fillRoundedRect(-26, -150, 52, 40, 8);
        const kt = this.add.text(0, -130, key, { fontFamily: font.display, fontSize: 24, fontStyle: '700', color: css.cream }).setOrigin(0.5);
        z.add([g, img, t, kg, kt]);
        z.setData('g', g);
        z.setSize(300, 380).setInteractive({ useHandCursor: true }).on('pointerup', () => this.phase === 'sort' && this.choose(which));
        box.add(z);
        return z;
    }

    /** Deal the next piece onto the tray (and show the three after it, small, waiting). */
    private nextItem() {
        const st = this.sort!;
        const items = this.params().sort.items;
        st.i++;
        st.item?.destroy();
        st.queue.forEach((q) => q.destroy());
        st.queue = [];
        if (st.i >= items.length) return this.sortDone();
        st.count.setText(this.params().sort.count.replace('{n}', String(st.i + 1)).replace('{total}', String(items.length)));
        const it = items[st.i];
        const c = this.add.container(0, 70);
        const img = this.add.image(0, 0, `s03items_${it.kind}`);
        img.setScale(Math.min(300 / img.width, 170 / img.height, 1.6));
        const label = this.add.text(0, -118, it.label, { fontFamily: font.display, fontSize: 34, fontStyle: '700', color: css.ink }).setOrigin(0.5);
        c.add([img, label]);
        c.setSize(img.displayWidth, img.displayHeight).setInteractive({ draggable: true, useHandCursor: true });
        this.input.setDraggable(c);
        c.on('drag', (_p: Phaser.Input.Pointer, x: number, y: number) => c.setPosition(x, y));
        c.on('dragend', () => {
            if (c.x < -260) this.choose('crate');
            else if (c.x > 260) this.choose('bin');
            else this.tweens.add({ targets: c, x: 0, y: 70, duration: 200, ease: 'Back.easeOut' });
        });
        st.box.add(c);
        st.item = c;
        if (!this.state.reducedMotion) this.tweens.add({ targets: c, alpha: { from: 0, to: 1 }, y: { from: 20, to: 70 }, duration: 260, ease: 'Back.easeOut' });
        items.slice(st.i + 1, st.i + 4).forEach((q, k) => {
            const qi = this.add.image(-60 + k * 60, -150, `s03items_${q.kind}`).setAlpha(0.55);
            qi.setScale(Math.min(52 / qi.width, 40 / qi.height));
            st.box.add(qi);
            st.queue.push(qi);
        });
        st.busy = false;
    }

    /** The piece goes where it was sent. Right: a tick. Wrong: it still goes, with the reason. */
    private choose(to: 'crate' | 'bin') {
        const st = this.sort;
        if (!st || st.busy || !st.item) return;
        st.busy = true;
        const it = this.params().sort.items[st.i];
        const right = (to === 'crate') === it.keep;
        if (right) st.right++;
        else if (to === 'crate') st.mixed++;
        else st.lost++;
        this.events.emit('sfx', right ? 'sort_right' : 'sort_wrong');
        const zone = st.zones[to];
        const flash = this.add.graphics();
        flash.fillStyle(right ? colour.income : colour.cost, 0.18).fillRoundedRect(-150, -170, 300, 380, 20);
        zone.addAt(flash, 1);
        this.time.delayedCall(500, () => flash.destroy());
        const mark = this.add.text(zone.x + 110, -110, right ? '✓' : '✗', { fontFamily: font.display, fontSize: 48, fontStyle: '700', color: right ? css.income : css.cost }).setOrigin(0.5);
        st.box.add(mark);
        this.time.delayedCall(600, () => mark.destroy());
        let wait = 360;
        if (!right) {
            const why = this.add.text(0, 200, it.why, { fontFamily: font.body, fontSize: 26, fontStyle: '600', color: css.cost, backgroundColor: css.card, padding: { x: 14, y: 6 } }).setOrigin(0.5);
            st.box.add(why);
            this.time.delayedCall(1300, () => why.destroy());
            wait = 1100;
        }
        const item = st.item;
        st.item = undefined;
        if (this.state.reducedMotion) item.destroy();
        else this.tweens.add({ targets: item, x: zone.x, y: 40, scale: 0.35, alpha: 0.2, duration: 300, ease: 'Cubic.easeIn', onComplete: () => item.destroy() });
        this.time.delayedCall(this.state.reducedMotion ? 300 : wait, () => this.nextItem());
    }

    /** All dealt: the score and what it means for the rate, then the crate is sealed. */
    private sortDone() {
        const st = this.sort!;
        const p = this.params().sort;
        const total = p.items.length;
        this.clean = st.mixed === 0;
        st.count.setText(p.done);
        const lines = [p.score.replace('{right}', String(st.right)).replace('{total}', String(total)), this.clean ? p.verdict_clean : p.verdict_mixed];
        if (st.lost) lines.push(p.verdict_lost);
        const card = this.add.container(0, 60);
        const g = this.add.graphics();
        drawCard(g, -330, -100, 660, 200, this.clean ? colour.income : colour.cost);
        card.add(g);
        lines.forEach((line, k) => card.add(this.add.text(0, -46 + k * 46, line, {
            fontFamily: k === 0 ? font.display : font.body, fontSize: k === 0 ? 34 : 26, fontStyle: k === 0 ? '700' : '400',
            color: k === 1 ? (this.clean ? css.income : css.cost) : css.ink,
        }).setOrigin(0.5)));
        st.box.add(card);
        this.highlightRate(this.clean);
        this.time.delayedCall(this.state.reducedMotion ? 1200 : 2200, () => this.sealCrate());
    }

    /** The lid goes on the crate, then the drag to the scale. */
    private sealCrate() {
        const box = this.sort!.box;
        const c = this.crateCentre();
        const done = () => {
            box.destroy();
            this.sort = undefined;
            if (!this.state.reducedMotion) this.tweens.add({ targets: this.crate, y: this.crate.y - 6, duration: 110, yoyo: true });
            this.events.emit('sfx', 'crate_seal');
            this.phase = 'drag';
            this.prompt.show(this.prompts().drag, 'Space');
            this.ring = this.hint(c.x, c.y, 78);
        };
        if (this.state.reducedMotion) return done();
        this.tweens.add({ targets: box, alpha: 0, duration: 300, onComplete: done });
    }

    /** Space/Enter/→ walks the beat forward; the pointer handles the drag and the spoken number. */
    private press() {
        if (this.phase === 'sort') return;              // the sort has its own keys (← →)
        if (this.phase === 'drag') this.snap();
        else if (this.phase === 'talk') this.nextLine();
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
        if (this.phase === 'talk') this.nextLine();          // a click carries the conversation on
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

        this.events.emit('sfx', 'scale');
        setState(this, { kilo: { carried: false, tag: this.state.kilo.tag } });
        this.popCard(this.scaleDisplayCard(), this.state.reducedMotion);
        this.prompt.show(this.prompts().number, 'Space');
        this.phase = 'talk';
        this.line = -1;
        this.time.delayedCall(this.state.reducedMotion ? 0 : 450, () => this.nextLine());
    }

    // --- the weigh-in, as a conversation -----------------------------------------------------------
    //
    // The attendant and Riyaz talk it through the way a Shivajinagar counter does, in Dakhni and
    // English (s03.json talk). Each Space or click plays the next line as a bubble over its speaker;
    // a mixed crate gets the lines that go with it. The number is said but never shown: the screen
    // masks it ("mask"), and the UPI ping lands on "pay".

    private line = -1;
    private talkBusy = false;

    private nextLine() {
        if (this.phase !== 'talk' || this.talkBusy) return;
        const talk = this.params().talk;
        this.fadeOut(this.speechCard);
        this.speechCard = undefined;
        if (++this.line >= talk.length) return this.toLeave();
        const l = talk[this.line];
        this.speechCard = this.popCard(this.bubble(l.who, !this.clean && l.mixed ? l.mixed : l.text), this.state.reducedMotion);
        if (l.do === 'mask') this.time.delayedCall(220, () => {
            this.attendantIdle.setVisible(false);
            this.attendantType.setVisible(true);
            this.numberCard = this.popCard(this.maskedNumberCard(), this.state.reducedMotion);
            this.prompt.show(this.prompts().wait);
        });
        if (l.do === 'pay') {
            this.talkBusy = true;                        // a beat for the ping before the next line
            this.time.delayedCall(this.state.reducedMotion ? 0 : 700, () => { this.paid(); this.talkBusy = false; });
        }
    }

    /** UPI confirms by sound; the tag flips and the slip lands. */
    private paid() {
        const p = this.params();
        const tag = !this.clean && p.tag_after_mixed ? p.tag_after_mixed : p.tag_after;
        this.events.emit('sfx', 'upi_ping');
        this.tag.flipTo({ ...tag });
        setState(this, { kilo: { carried: false, tag: { ...tag } } });
        this.attendantType.setVisible(false);
        this.attendantIdle.setVisible(true);
        this.prompt.show(this.prompts().paid, 'Space');
        this.fadeOut(this.numberCard);
        this.popCard(this.slip(), this.state.reducedMotion);
    }

    private toLeave() {
        this.phase = 'leave';
        this.prompt.show(this.prompts().leave, 'Space');
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
        this.rateMark = this.add.graphics();
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

        this.add.container(x, y, [g, this.rateMark, ...rows, note, chip]).setDepth(16);
    }

    private rateMark?: GameObjects.Graphics;

    /** Light up the line the crate earned: the two sorted lines, or Mixed. */
    private highlightRate(clean: boolean) {
        const g = this.rateMark!;
        g.clear().fillStyle(clean ? colour.income : colour.cost, 0.16);
        if (clean) g.fillRoundedRect(10, 14, 380, 84, 8);
        else g.fillRoundedRect(10, 102, 380, 42, 8);
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

    /** A speech bubble over its speaker, with their name on a tab and a nudge to carry on. Riyaz's
     * hands stay wet and empty (task 03: he never touches a phone). */
    private bubble(who: TalkLine['who'], text: string) {
        const head = this.anchor(who === 'riyaz' ? 'riyaz_head' : 'attendant_head');
        const t = this.add.text(22, 46, text, { fontFamily: font.body, fontSize: 27, color: css.ink, wordWrap: { width: 400 }, lineSpacing: 2 });
        const name = this.add.text(22, 0, this.params().speakers[who], { fontFamily: font.display, fontSize: 20, fontStyle: '800', color: css.cream }).setOrigin(0, 0.5);
        const w = Math.max(t.width + 44, name.width + 60, 220), h = t.height + 76;
        const tx = who === 'riyaz' ? 70 : w - 36;                   // the tail leans to the speaker; the attendant's stays left of the slip
        const g = this.add.graphics();
        drawCard(g, 0, 0, w, h, who === 'riyaz' ? colour.ink : colour.income);
        g.fillStyle(colour.card, 1).fillTriangle(tx - 14, h - 2, tx, h + 24, tx + 14, h - 2);
        g.lineStyle(3, who === 'riyaz' ? colour.ink : colour.income, 1).beginPath().moveTo(tx - 14, h - 1).lineTo(tx, h + 24).lineTo(tx + 14, h - 1).strokePath();
        g.fillStyle(who === 'riyaz' ? colour.ink : colour.income, 1).fillRoundedRect(12, -16, name.width + 20, 32, 16);
        name.setPosition(22, 0);
        const more = this.add.text(w - 16, h - 14, '▸', { fontFamily: font.display, fontSize: 22, color: css.muted }).setOrigin(1, 1);
        if (!this.state.reducedMotion) this.tweens.add({ targets: more, alpha: 0.2, duration: 500, yoyo: true, repeat: -1 });
        const x = Math.min(Math.max(head.x - tx, 40), 1880 - w), y = head.y - 60 - h;
        return this.add.container(x, y, [g, t, name, more]).setDepth(24);
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
        const lines = (this.clean ? p.slip.lines : p.slip.lines_mixed).map((line, i) => this.add.text(24, 108 + i * 42, line, {
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
        return this.add.container(1180, 110, [g, title, ...lines, done, chip]).setDepth(22);
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
