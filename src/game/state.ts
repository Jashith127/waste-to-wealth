// The one game state, kept in Phaser's registry so every scene sees the same copy.
import type { Game, Scene } from 'phaser';
import type { Meaning } from './theme';

export type Run = 1 | 2;

export interface KiloTagState {
    value: string;      // as shown, e.g. "−₹5" or "+₹[__]"
    meaning: Meaning;
    note?: string;
}

export interface GameState {
    run: Run;
    station: string;
    kilo: { carried: boolean; tag: KiloTagState | null };
    blueprintOpen: boolean;
    reducedMotion: boolean;
}

const KEY = 'state';

export function initState(game: Game): GameState {
    const params = new URLSearchParams(window.location.search);
    const state: GameState = {
        run: params.get('run') === '2' ? 2 : 1,
        station: params.get('station') ?? 's01',
        kilo: { carried: false, tag: null },
        blueprintOpen: false,
        reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches || params.has('reducedMotion'),
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
