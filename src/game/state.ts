// The one game state, kept in Phaser's registry so every scene sees the same copy.
import type { Game, Scene } from 'phaser';
import type { Meaning } from './theme';

export type Run = 1 | 2;

export interface KiloTagState {
    value: string;      // as shown, e.g. "−₹5" or "+₹[__]"
    meaning: Meaning;
    note?: string;
    label?: string;     // the small caption over the value, e.g. "Disposal fee"
}

export interface GameState {
    run: Run;
    beat: number;       // index into runs.json beats for this run
    station: string;    // scene currently playing
    kilo: { carried: boolean; tag: KiloTagState | null };
    blueprintOpen: boolean;
    reducedMotion: boolean;
    captions: boolean;  // sound captions (task 19), C toggles
    briefings: boolean; // the how-to card before each beat; ?noBrief skips them (screenshots)
}

const KEY = 'state';

/** URL params for reviewers and screenshots: ?run=2&beat=3, or ?station=s04 (first beat of that station);
 * ?noBrief starts each beat without its briefing. */
export function initState(game: Game, beats: Record<Run, string[]>): GameState {
    const params = new URLSearchParams(window.location.search);
    const run: Run = params.get('run') === '2' ? 2 : 1;
    let beat = Number(params.get('beat') ?? 0);
    const wanted = params.get('station');
    if (wanted) beat = Math.max(0, beats[run].findIndex((b) => b.split(':')[0] === wanted));
    const state: GameState = {
        run,
        beat,
        station: beats[run][beat]?.split(':')[0] ?? 's01',
        kilo: { carried: false, tag: null },
        blueprintOpen: false,
        reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches || params.has('reducedMotion'),
        captions: !params.has('noCaptions'),
        briefings: !params.has('noBrief'),
    };
    game.registry.set(KEY, state);
    return state;
}

export function getState(scene: Scene): GameState {
    return scene.registry.get(KEY) as GameState;
}

/** Change state and tell everyone: listeners use scene.registry.events.on('changedata-state', ...). */
export function setState(scene: Scene, patch: Partial<GameState>): GameState {
    const next = { ...getState(scene), ...patch };
    scene.registry.set(KEY, next);
    return next;
}
