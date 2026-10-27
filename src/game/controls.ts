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

/** What the objective card says right now: the station, the step, the sentence and its control. */
export interface RailHint {
    key?: string;
    mouse?: MouseHint;
    text?: string;
    badge?: string;
    title?: string;
    /** The how-to step this sentence belongs to, by its label ("Chop"), and how far through the beat it is. */
    step?: { label: string; at: number; of: number };
}

let hint: RailHint = {};

/** The objective card publishes itself here; on a phone the side rails show it instead of the card. */
export function setControlHint(key?: string, mouse?: MouseHint, text?: string, extra: Omit<RailHint, 'key' | 'mouse' | 'text'> = {}) {
    hint = { key, mouse, text, ...extra };
}

export function currentControl() {
    return controlMode(hint.key, hint.mouse);
}

export function currentHint(): Readonly<RailHint> {
    return hint;
}

export interface ControlHelp {
    stick?: { title: string; body: string };
    tap?: { label: string; body: string };
    /** When the picture itself is the control. */
    screen?: string;
}

/** What each on-screen control does for this step, in a few words, so the rails can say it next to it. */
export function controlHelp(): ControlHelp {
    const mode = currentControl();
    const out: ControlHelp = {};
    if (hint.key === 'Wait') out.stick = { title: 'Wait', body: 'Let it pass. Use the stick only to step aside.' };
    else if (mode.stick === 'swipe') out.stick = { title: 'Sort', body: 'Flick the stick left or right, the way the arrows on the picture point.' };
    else if (mode.stick === 'move') out.stick = { title: 'Walk', body: 'Drag the stick, or hold a finger on the street.' };
    if (mode.tapKey) {
        const label = hint.step?.label;
        const name = label && label.length <= 12 ? label : 'Tap';
        const arrow = mode.tapKey === 'RIGHT' ? ' →' : mode.tapKey === 'LEFT' ? '← ' : '';
        out.tap = {
            label: mode.tapKey === 'LEFT' ? arrow + name : name + arrow,
            body: mode.verb === 'drag' ? 'Tap here, or drag the piece on the picture.' : 'Tap here to do it.',
        };
    } else if (mode.verb === 'drag') out.screen = 'Drag the piece on the picture with your finger.';
    else if (mode.verb === 'tap') out.screen = 'Tap the highlighted spot on the picture.';
    else if (!mode.stick) out.screen = 'Nothing to press. Watch.';
    return out;
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
        .replace(/\(←\)/g, '(flick left)')
        .replace(/\(→\)/g, '(flick right)')
        .replace(/\bPress\b/g, 'Tap')
        .replace(/\bClick\b/g, 'Tap')
        .replace(/hold the mouse/g, 'hold a finger');
}
