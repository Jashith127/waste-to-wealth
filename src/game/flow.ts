// The order of play: runs.json beats, the walk-out transition and the jump to the next beat.
import type { Scene } from 'phaser';
import { runs } from './content';
import { getState, setState, type Run } from './state';
import { motion } from './theme';

export interface Beat {
    run: Run;
    index: number;
    station: string;          // "s01"…"s07" or "end"
    variant?: string;         // e.g. "night" for "s01:night"
}

export function parseBeat(run: Run, index: number): Beat {
    const raw = runs[run].beats[index];
    const [station, variant] = raw.split(':');
    return { run, index, station, variant };
}

/** The beat after the current one: next in this run, else the start of Run 2, else the end card. */
export function nextBeat(scene: Scene): Beat {
    const { run, beat } = getState(scene);
    if (beat + 1 < runs[run].beats.length) return parseBeat(run, beat + 1);
    if (run === 1) return parseBeat(2, 0);
    return { run: 2, index: beat, station: 'end' };
}

/** Phaser scene key for a beat: the station's own scene if one is registered, else the grey-box placeholder. */
export function sceneFor(scene: Scene, beat: Beat): string {
    if (beat.station === 'end') return scene.scene.get('EndCard') ? 'EndCard' : 'Placeholder';
    return scene.scene.get(beat.station) ? beat.station : 'Placeholder';
}

/** Fade out, show the next station's card, start it. `before` runs after the fade (e.g. slide the set). */
export function goNext(scene: Scene) {
    const beat = nextBeat(scene);
    const runChanged = beat.run !== getState(scene).run;
    setState(scene, { run: beat.run, beat: beat.index, ...(runChanged ? { kilo: { carried: false, tag: null } } : {}) });
    scene.cameras.main.fadeOut(motion.transition, 28, 23, 20);
    scene.cameras.main.once('camerafadeoutcomplete', () => scene.scene.start('StationCard', { beat, runChanged }));
}
