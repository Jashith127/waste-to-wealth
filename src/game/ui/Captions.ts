// Captions for sounds (task 19): bottom centre, above the blueprint line (or above the panel when
// it is open), Hind 26 px on an ink pill at 80%, 1.6 s each, stacked when two fire together.
// C toggles them; the choice is kept in state so it carries across beats.
import { GameObjects, Scene } from 'phaser';
import { getState, setState } from '../state';
import { colour, css, font, layout } from '../theme';

const SHOW_MS = 1600;

export class Captions {
    private live: GameObjects.Container[] = [];

    constructor(private scene: Scene) {}

    show(text: string) {
        const t = this.scene.add.text(0, 0, text, { fontFamily: font.body, fontSize: 26, color: css.cream }).setOrigin(0.5);
        const w = t.width + 40, h = 46;
        const g = this.scene.add.graphics();
        g.fillStyle(colour.ink, 0.8).fillRoundedRect(-w / 2, -h / 2, w, h, h / 2);
        const c = this.scene.add.container(960, 0, [g, t]).setDepth(60);
        this.live.push(c);
        this.layout();
        this.scene.time.delayedCall(SHOW_MS, () => {
            c.destroy();
            this.live = this.live.filter((x) => x !== c);
            this.layout();
        });
    }

    toggle() {
        const on = !getState(this.scene).captions;
        setState(this.scene, { captions: on });
        if (!on) {
            this.live.forEach((c) => c.destroy());
            this.live = [];
        }
        this.show(on ? 'Captions on' : 'Captions off');
    }

    private layout() {
        const bottom = (getState(this.scene).blueprintOpen ? layout.blueprintTop - 12 : layout.blueprintTop - 20) - 23;
        this.live.forEach((c, i) => c.setY(bottom - (this.live.length - 1 - i) * 54));
    }
}
