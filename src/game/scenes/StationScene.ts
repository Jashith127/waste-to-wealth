// Base for every station: the diorama void, layer placement from layers.json, prompt, blueprint (B),
// evidence (I), and the walk-out transition. A station subclass only adds its own interaction.
import { GameObjects, Scene } from 'phaser';
import { blueprint, runData, station, type StationData } from '../content';
import { goNext, type Beat } from '../flow';
import { getState, setState, type GameState } from '../state';
import { colour, FRAME, layout, motion } from '../theme';
import { BlueprintPanel } from '../ui/BlueprintPanel';
import { EvidencePanel } from '../ui/EvidencePanel';
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
        this.prompt = new Prompt(this, layout.prompt.x, layout.prompt.y);
        this.blueprintPanel = new BlueprintPanel(this, this.stationData, this.state.run, blueprint(this.stationData, this.state.run), this.state.reducedMotion);
        this.evidence = new EvidencePanel(this, this.stationData, this.state.reducedMotion);

        const kb = this.input.keyboard!;
        kb.on('keydown-B', () => setState(this, { blueprintOpen: this.blueprintPanel.toggle() }));
        kb.on('keydown-I', () => this.evidence.toggle());
        kb.on('keydown-ESC', () => { this.evidence.toggle(false); this.blueprintPanel.toggle(false); });
        if (getState(this).blueprintOpen) this.blueprintPanel.toggle(true);

        this.build();
        const ready = () => ((window as unknown as { __ready?: string }).__ready = this.stationId);   // Playwright waits on this
        if (this.state.reducedMotion) ready();
        else {
            this.cameras.main.fadeIn(motion.transition, 28, 23, 20);
            this.cameras.main.once('camerafadeincomplete', ready);
        }
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

    /** Pulsing ring around a hotspot; returns it so callers can remove it. */
    protected hint(x: number, y: number, r: number) {
        const ring = this.add.circle(x, y, r).setStrokeStyle(4, colour.cream, 0.95).setDepth(40);
        if (!this.state.reducedMotion) {
            this.tweens.add({ targets: ring, scale: 1.12, alpha: 0.35, duration: 700, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
        }
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
