// Base for every station: the diorama void, layer placement from layers.json, prompt, blueprint (B),
// evidence (I), and the walk-out transition. A station subclass only adds its own interaction.
import { GameObjects, Scene } from 'phaser';
import { blueprint, howTo, runData, runs, station, type StationData } from '../content';
import { goNext, type Beat } from '../flow';
import { getState, setState, type GameState } from '../state';
import { colour, FRAME, layout, motion } from '../theme';
import { mountAudio } from '../audio';
import { BlueprintPanel } from '../ui/BlueprintPanel';
import { EvidencePanel } from '../ui/EvidencePanel';
import { beatTitle } from '../ui/Briefing';
import { keycap } from '../ui/keys';
import { LevelComplete, levelInfo } from '../ui/LevelComplete';
import { Prompt } from '../ui/Prompt';

export interface LayerInfo { x: number; y: number; w: number; h: number }
export interface Layers { frame: [number, number]; layers: Record<string, LayerInfo>; anchors: Record<string, [number, number]> }

export abstract class StationScene extends Scene {
    protected stationData!: StationData;
    protected state!: GameState;
    protected world!: GameObjects.Container;
    protected prompt!: Prompt;
    protected blueprintPanel!: BlueprintPanel;
    protected evidence!: EvidencePanel;
    protected layers?: Layers;
    protected variant?: string;     // e.g. "night" when runs.json says "s01:night"
    private leaving = false;

    constructor(readonly stationId: string) {
        super(stationId);
    }

    /** Queue the station's Blender layers (public/assets/stations/<id>/). */
    protected loadLayers() {
        this.load.pack(this.stationId, `assets/stations/${this.stationId}/pack.json`);
        this.load.json(`${this.stationId}_layers`, `assets/stations/${this.stationId}/layers.json`);
    }

    create({ beat }: { beat?: Beat } = {}) {
        this.variant = beat?.variant;
        this.stationData = station(this.stationId);
        this.state = setState(this, { station: this.stationId });
        this.layers = this.cache.json.get(`${this.stationId}_layers`);
        this.leaving = false;

        this.add.tileSprite(0, 0, FRAME.width, FRAME.height, 'lattice').setOrigin(0).setDepth(-10);
        this.world = this.add.container(0, 0);
        this.add.image(0, 0, 'skyline').setOrigin(0).setDepth(-9);       // the backdrop beyond the set
        if (this.clockPhase() !== 'night') {                               // morning haze over the street
            this.add.image(0, 0, 'haze').setOrigin(0).setDisplaySize(FRAME.width, FRAME.height).setDepth(20);
        }
        this.prompt = new Prompt(this, layout.prompt.x, layout.prompt.y, this.promptInfo());
        this.prompt.onStep = (i, n) => { if (i === n - 1) this.complete(); };
        this.blueprintPanel = new BlueprintPanel(this, this.stationData, this.state.run, blueprint(this.stationData, this.state.run), this.state.reducedMotion);
        this.evidence = new EvidencePanel(this, this.stationData, this.state.reducedMotion);

        const kb = this.input.keyboard!;
        kb.on('keydown-B', () => this.togglePanel('blueprint'));
        kb.on('keydown-I', () => this.togglePanel('evidence'));
        kb.on('keydown-ESC', () => { this.evidence.toggle(false); this.blueprintPanel.toggle(false); });
        if (getState(this).blueprintOpen) this.blueprintPanel.toggle(true);

        mountAudio(this);
        this.build();
        const ready = () => ((window as unknown as { __ready?: string }).__ready = this.stationId);   // Playwright waits on this
        if (this.state.reducedMotion) ready();
        else {
            this.cameras.main.fadeIn(motion.transition, 28, 23, 20);
            this.cameras.main.once('camerafadeincomplete', ready);
        }
    }

    /** The objective card's header and step dots, from the beat's how-to (howto.json). */
    private promptInfo() {
        const key = runs[this.state.run].beats[this.state.beat] ?? this.stationId;
        const prompts = this.prompts();
        const head = beatTitle(key);
        return {
            badge: head.badge, title: this.stationData.title, phase: this.clockPhase(),
            steps: howTo(this.state.run, key)?.steps.map((st) => ({ label: st.label, mouse: st.mouse, match: st.prompts.map((p) => prompts[p]).filter(Boolean) })),
        };
    }

    /** The beat's last step is up: "Level complete!", a moment after it lands (a tag flip, a reveal). */
    private complete() {
        const info = levelInfo(this.state.run, this.state.beat, this.stationData.title);
        if (!info) return;
        this.time.delayedCall(this.state.reducedMotion ? 0 : 650, () => {
            if (!this.leaving) new LevelComplete(this, info, () => this.advance());
        });
    }

    /** Continue from the "Level complete" card: what the station's own → does. */
    protected advance() {
        this.leave();
    }

    /** The control dock's buttons (Hud): what each panel shows, and toggling it. */
    panelOpen(which: 'blueprint' | 'evidence') {
        return which === 'blueprint' ? this.blueprintPanel.isOpen : this.evidence.isOpen;
    }

    togglePanel(which: 'blueprint' | 'evidence') {
        if (this.leaving) return;
        if (which === 'blueprint') setState(this, { blueprintOpen: this.blueprintPanel.toggle() });
        else this.evidence.toggle();
    }

    private clockPhase() {
        const beats = runs[this.state.run].beats[this.state.beat] ?? this.stationId;
        return runs[this.state.run].clock?.[beats] ?? 'morning';
    }

    /** Station-specific content. */
    protected abstract build(): void;

    /** Place a rendered layer at its position in the frame. */
    protected layer(name: string): GameObjects.Image {
        const info = this.layers!.layers[name];
        const img = this.add.image(info.x, info.y, `${this.stationId}_${name}`).setOrigin(0);
        this.world.add(img);
        return img;
    }

    protected anchor(name: string): { x: number; y: number } {
        const [x, y] = this.layers!.anchors[name];
        return { x, y };
    }

    protected prompts() {
        return runData(this.stationData, this.state.run).prompts ?? {};
    }

    /** Pulsing ring around a hotspot, with the objective's key bobbing above it; returns the ring so
     * callers can remove it (the key goes with it, and follows it if the ring is in a moving container). */
    protected hint(x: number, y: number, r: number) {
        const ring = this.add.circle(x, y, r).setStrokeStyle(4, colour.cream, 0.95).setDepth(40);
        const halo = this.add.circle(x, y, r + 8).setStrokeStyle(8, colour.pay, 0.35).setDepth(39);
        if (!this.state.reducedMotion) {
            this.tweens.add({ targets: ring, scale: 1.12, alpha: 0.35, duration: 700, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
            this.tweens.add({ targets: halo, scale: 1.25, alpha: 0, duration: 1100, repeat: -1, ease: 'Sine.easeOut' });
        }
        const key = this.prompt.key;
        const cap = key && key !== 'Wait' && key !== 'Arrows' ? keycap(this, key, 40).setDepth(41) : undefined;
        const bob = { y: 0 };
        if (cap && !this.state.reducedMotion) this.tweens.add({ targets: bob, y: -8, duration: 500, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
        const follow = () => {
            const parent = ring.parentContainer;
            const px = (parent?.x ?? 0) + ring.x, py = (parent?.y ?? 0) + ring.y;
            halo.setPosition(px, py).setDepth(parent ? parent.depth + 1 : 39).setVisible(ring.visible);
            const above = py - r - 34 > layout.hudBottom + 140;          // else under the ring, clear of the HUD's cards
            cap?.setPosition(px, (above ? py - r - 34 : py + r + 34) + bob.y).setVisible(ring.visible).setDepth(parent ? 960 : 41);
        };
        follow();
        this.events.on('update', follow);
        ring.once('destroy', () => {
            this.events.off('update', follow);
            halo.destroy();
            cap?.destroy();
        });
        return ring;
    }

    /** Walk out to the next beat in runs.json: the street slides past, fade, station card, next scene. */
    protected leave() {
        if (this.leaving) return;
        this.leaving = true;
        if (!this.state.reducedMotion) {
            this.tweens.add({ targets: this.world, x: -260, duration: motion.transition, ease: 'Sine.easeIn' });
        }
        goNext(this);
    }
}
