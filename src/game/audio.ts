// Sound (task 19). Every `sfx` event a station emits plays its sound and always shows its caption.
// A sound plays from its file in public/assets/audio/ once that file exists; until then it is a short
// sound synthesised here with Web Audio (no samples, no voices). Ambient beds play only from our own
// recordings: with no file, a station is simply quiet. Text and file names: src/data/audio.json.
import type { Scene } from 'phaser';
import audioData from '../data/audio.json';
import { getState } from './state';
import { Captions } from './ui/Captions';

interface Sfx { caption: string; file: string; synth: string }
interface Ambient { caption: string; file: string }
const data = audioData as unknown as { sfx: Record<string, Sfx>; ambient: Record<string, Ambient>; station_ambient: Record<string, string> };

const present = new Map<string, boolean>();          // file url -> exists (checked once per session)
let ctx: AudioContext | undefined;
let bed: { key: string; el: HTMLAudioElement } | undefined;

function context() {
    ctx ??= new AudioContext();
    if (ctx.state === 'suspended') void ctx.resume();
    return ctx;
}

async function exists(url: string) {
    if (!present.has(url)) {
        try {
            const r = await fetch(url, { method: 'HEAD' });
            present.set(url, r.ok && !(r.headers.get('content-type') ?? '').includes('text/html'));
        } catch {
            present.set(url, false);
        }
    }
    return present.get(url)!;
}

/** Mount on a station scene: captions, effects for its sfx events, and its ambient bed. */
export function mountAudio(scene: Scene) {
    const captions = new Captions(scene);
    scene.events.on('sfx', (key: string) => {
        const s = data.sfx[key];
        if (!s) return;
        if (getState(scene).captions) captions.show(s.caption);
        void play(s);
    });
    const amb = data.station_ambient[scene.scene.key];
    void ambient(amb ? data.ambient[amb] : undefined, amb);
    scene.input.keyboard?.on('keydown-C', () => captions.toggle());
    return captions;
}

async function play(s: Sfx) {
    if (await exists(s.file)) {
        const a = new Audio(s.file);
        a.volume = 0.8;
        void a.play().catch(() => undefined);
        return;
    }
    try {
        synth(context(), s.synth);
    } catch {
        // no audio device: captions carry it
    }
}

async function ambient(a: Ambient | undefined, key?: string) {
    if (bed && bed.key !== key) {
        bed.el.pause();
        bed = undefined;
    }
    if (!a || !key || bed || !(await exists(a.file))) return;
    const el = new Audio(a.file);
    el.loop = true;
    el.volume = 0.35;
    bed = { key, el };
    void el.play().catch(() => undefined);
}

// --- synthesised effects ------------------------------------------------------------------------

function noise(c: AudioContext, seconds: number) {
    const b = c.createBuffer(1, Math.ceil(c.sampleRate * seconds), c.sampleRate);
    const d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    const src = c.createBufferSource();
    src.buffer = b;
    return src;
}

function env(c: AudioContext, peak: number, attack: number, decay: number, at = c.currentTime) {
    const g = c.createGain();
    g.gain.setValueAtTime(0.0001, at);
    g.gain.exponentialRampToValueAtTime(peak, at + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, at + attack + decay);
    g.connect(c.destination);
    return g;
}

function tone(c: AudioContext, type: OscillatorType, f0: number, f1: number, peak: number, attack: number, decay: number, at = c.currentTime) {
    const o = c.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(f0, at);
    o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), at + attack + decay);
    o.connect(env(c, peak, attack, decay, at));
    o.start(at);
    o.stop(at + attack + decay + 0.05);
}

function burst(c: AudioContext, kind: BiquadFilterType, freq: number, q: number, peak: number, attack: number, decay: number, at = c.currentTime) {
    const n = noise(c, attack + decay + 0.05);
    const f = c.createBiquadFilter();
    f.type = kind;
    f.frequency.value = freq;
    f.Q.value = q;
    n.connect(f).connect(env(c, peak, attack, decay, at));
    n.start(at);
}

function synth(c: AudioContext, kind: string) {
    const t = c.currentTime;
    switch (kind) {
        case 'thunk':      // a cleaver into a wooden block: a dull knock and the bite of the edge
            tone(c, 'sine', 140, 60, 0.6, 0.003, 0.18);
            burst(c, 'bandpass', 1800, 1.2, 0.35, 0.002, 0.06);
            break;
        case 'knock':
            tone(c, 'triangle', 180, 90, 0.4, 0.003, 0.14);
            burst(c, 'lowpass', 600, 0.7, 0.25, 0.002, 0.08);
            break;
        case 'clunk':      // the platform scale settling
            tone(c, 'sine', 95, 70, 0.55, 0.004, 0.3);
            burst(c, 'bandpass', 900, 2, 0.2, 0.002, 0.05);
            tone(c, 'triangle', 420, 400, 0.08, 0.002, 0.25, t + 0.02);
            break;
        case 'snap':
            burst(c, 'highpass', 2500, 0.7, 0.35, 0.001, 0.05);
            tone(c, 'square', 300, 200, 0.08, 0.001, 0.05);
            break;
        case 'tick':
            tone(c, 'sine', 880, 1320, 0.18, 0.004, 0.12);
            break;
        case 'buzz':
            tone(c, 'square', 150, 120, 0.12, 0.005, 0.22);
            break;
        case 'ping':       // the UPI confirmation: two bright notes
            tone(c, 'sine', 1318, 1318, 0.25, 0.005, 0.35);
            tone(c, 'sine', 1760, 1760, 0.22, 0.005, 0.5, t + 0.12);
            break;
        case 'seal':
            tone(c, 'sine', 70, 45, 0.6, 0.004, 0.25);
            burst(c, 'lowpass', 400, 0.7, 0.2, 0.01, 0.3);
            break;
        case 'unseal':
            burst(c, 'bandpass', 3000, 0.8, 0.2, 0.05, 0.35);
            tone(c, 'sine', 60, 80, 0.3, 0.01, 0.2);
            break;
        case 'powerdown':  // the fridge compressor winding down
            tone(c, 'sawtooth', 110, 30, 0.12, 0.01, 1.2);
            break;
        case 'swish':
            burst(c, 'bandpass', 1500, 0.6, 0.18, 0.05, 0.25);
            break;
        case 'engine':
            tone(c, 'sawtooth', 48, 70, 0.14, 0.2, 1.4);
            burst(c, 'lowpass', 220, 0.7, 0.2, 0.2, 1.4);
            break;
        case 'grind':
            tone(c, 'sawtooth', 70, 55, 0.12, 0.05, 0.6);
            burst(c, 'bandpass', 700, 1.5, 0.22, 0.05, 0.6);
            break;
        case 'hiss':
            burst(c, 'highpass', 4000, 0.5, 0.2, 0.08, 0.8);
            break;
        case 'whirr':
            tone(c, 'sawtooth', 200, 380, 0.08, 0.2, 0.7);
            burst(c, 'bandpass', 1200, 3, 0.1, 0.2, 0.7);
            break;
        case 'scatter':    // grains on a steel feeder, then a hen or two
            for (let i = 0; i < 14; i++) burst(c, 'highpass', 3500, 1, 0.08, 0.001, 0.02, t + 0.2 + Math.random() * 0.35);
            for (const d of [0.55, 0.75]) tone(c, 'square', 620, 420, 0.05, 0.01, 0.12, t + d);
            break;
    }
}
