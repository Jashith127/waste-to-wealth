// What a phone shows instead of a key cap, and which on-screen control (if any) stands in for that key.
import type { MouseHint } from './content';
import { locale } from './i18n';

export type TouchVerb = 'tap' | 'move' | 'swipe' | 'drag' | 'hold';

const LABEL: Record<TouchVerb, string> = {
    tap: 'Tap', move: 'Move', swipe: 'Swipe', drag: 'Drag', hold: 'Hold',
};

export function touchLabel(verb: TouchVerb) {
    return LABEL[verb];
}

/** The chip a prompt or briefing should show for this key row. */
export function verbFromKeys(keys: string[], mouse?: MouseHint): TouchVerb | undefined {
    if (keys.length >= 4) return 'move';
    if (mouse === 'hold') return 'hold';
    if (keys.includes('←') && keys.includes('→') && keys.length === 2) return 'swipe';
    if (mouse === 'drag') return 'drag';
    if (keys.length || mouse === 'click') return 'tap';
    return undefined;
}

export interface ControlMode {
    verb?: TouchVerb;
    /** Key the round action button fires. Absent when the screen itself is the control (a tap on a pile). */
    tapKey?: 'SPACE' | 'RIGHT' | 'LEFT';
    /** A stick: walk (held) or a left/right flick (sort). "Wait" still offers the stick so the cart can be dodged. */
    stick: null | 'move' | 'swipe';
}

export function controlMode(key?: string, mouse?: MouseHint): ControlMode {
    if (key === 'Wait') return { stick: 'move' };
    if (key === 'Arrows' || mouse === 'hold') return { verb: 'move', stick: 'move' };
    if (key === '← →') return { verb: 'swipe', stick: 'swipe' };
    if (key === '→') return { verb: mouse === 'drag' ? 'drag' : 'tap', tapKey: 'RIGHT', stick: null };
    if (key === '←') return { verb: mouse === 'drag' ? 'drag' : 'tap', tapKey: 'LEFT', stick: null };
    if (key === 'Space') return { verb: mouse === 'drag' ? 'drag' : 'tap', tapKey: 'SPACE', stick: null };
    if (mouse === 'drag') return { verb: 'drag', stick: null };
    if (mouse === 'click') return { verb: 'tap', stick: null };
    return { stick: null };
}

let hint: { key?: string; mouse?: MouseHint } = {};

/** The objective card publishes the current key here; the phone dock reads it. */
export function setControlHint(key?: string, mouse?: MouseHint) {
    hint = { key, mouse };
}

export function currentControl() {
    return controlMode(hint.key, hint.mouse);
}

/** English how-to sentences, rewritten for a finger. Other languages keep their translation. */
export function touchText(text: string) {
    if (locale !== 'en') return text;
    return text
        .replace(/Arrows or WASD to walk, or hold the mouse where you want to go\./g, 'Use the move stick, or hold a finger on the street where you want to go.')
        .replace(/Press as the ring/g, 'Tap as the ring')
        .replace(/Each press/g, 'Each tap')
        .replace(/Space for each line/g, 'Tap for each line')
        .replace(/1 · 2 · 3 switch the map lens: waste, money, power\./g, 'Tap a lens: waste, money, power.')
        .replace(/\bPress\b/g, 'Tap')
        .replace(/\bClick\b/g, 'Tap')
        .replace(/hold the mouse/g, 'hold a finger');
}
