// The instruction pill in the top-left HUD band: what to do now, and its key. Left-aligned at (x, y).
import { GameObjects, Scene } from 'phaser';
import { colour, css, font, motion } from '../theme';

export class Prompt extends GameObjects.Container {
    private bg: GameObjects.Graphics;
    private label: GameObjects.Text;
    private key: GameObjects.Text;

    constructor(scene: Scene, x: number, y: number) {
        super(scene, x, y);
        this.bg = scene.add.graphics();
        this.label = scene.add.text(0, 0, '', { fontFamily: font.display, fontSize: 32, fontStyle: '600', color: css.cream }).setOrigin(0, 0.5);
        this.key = scene.add.text(0, 0, '', { fontFamily: font.display, fontSize: 20, fontStyle: '700', color: css.ink }).setOrigin(0.5, 0.5);
        this.add([this.bg, this.label, this.key]);
        this.setDepth(50);
        scene.add.existing(this);
    }

    show(text: string, keyHint?: string) {
        this.label.setText(text);
        const keyW = keyHint ? Math.max(44, this.key.setText(keyHint).width + 22) : 0;
        const w = this.label.width + 56 + (keyHint ? keyW + 16 : 0);
        const h = 60;
        this.bg.clear();
        this.bg.fillStyle(colour.ink, 0.92).fillRoundedRect(0, -h / 2, w, h, h / 2);
        this.label.setX(28);
        this.key.setVisible(!!keyHint);
        if (keyHint) {
            const kx = w - 28 - keyW / 2;
            this.bg.fillStyle(colour.cream, 1).fillRoundedRect(kx - keyW / 2, -17, keyW, 34, 7);
            this.key.setPosition(kx, 0);
        }
        this.setAlpha(0);
        this.scene.tweens.add({ targets: this, alpha: 1, duration: motion.normal, ease: 'Sine.easeOut' });
    }
}
