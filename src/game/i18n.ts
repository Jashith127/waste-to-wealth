// Languages: English, Hindi, Urdu and Kannada. Every Text in the game goes through one hook (install(),
// called before the game starts): its string is translated from src/data/i18n/strings.json, its font
// is swapped for one that has the script, letter-spacing is dropped (Phaser spaces letter by letter,
// which breaks Devanagari, Kannada and Urdu shaping), and Urdu is set right to left. So the data files
// and the scenes keep writing English, and a missing translation falls back to it.
//
// The language comes from ?lang=hi|ur|kn|en, else the last one picked (localStorage), else English.
// Changing it reloads the page (setLocale), so every scene is rebuilt in the new script.
import { GameObjects } from 'phaser';
import strings from '../data/i18n/strings.json';

export type Locale = 'en' | 'hi' | 'ur' | 'kn';
export const LOCALES: { id: Locale; name: string }[] = [
    { id: 'en', name: 'English' },
    { id: 'hi', name: 'हिन्दी' },
    { id: 'ur', name: 'اردو' },
    { id: 'kn', name: 'ಕನ್ನಡ' },
];

const KEY = 'wtw.lang';

function detect(): Locale {
    const ok = (v: string | null): v is Locale => LOCALES.some((l) => l.id === v);
    const param = new URLSearchParams(window.location.search).get('lang');
    if (ok(param)) return param;
    try {
        const saved = window.localStorage.getItem(KEY);
        if (ok(saved)) return saved;
    } catch { /* storage blocked: English */ }
    return 'en';
}

export const locale: Locale = detect();
export const rtl = locale === 'ur';

/** Switch language: remember it, and reload so every scene is rebuilt in the new script. */
export function setLocale(next: Locale) {
    try { window.localStorage.setItem(KEY, next); } catch { /* the URL carries it */ }
    const url = new URL(window.location.href);
    url.searchParams.set('lang', next);
    window.location.replace(url.toString());
}

// --- fonts -------------------------------------------------------------------------------------------
// Baloo 2 and Hind already carry Devanagari. Kannada: Baloo Tamma 2 (the same family's Kannada cut)
// and Noto Sans Kannada. Urdu: Noto Nastaliq Urdu, the script's proper book hand, for both.

const FONTS: Record<Locale, { display: string; body: string; sample: string }> = {
    en: { display: '"Baloo 2"', body: 'Hind', sample: 'Aa' },
    hi: { display: '"Baloo 2"', body: 'Hind', sample: 'कचरा' },
    kn: { display: '"Baloo Tamma 2"', body: '"Noto Sans Kannada"', sample: 'ಕನ್ನಡ' },
    ur: { display: '"Noto Nastaliq Urdu"', body: '"Noto Nastaliq Urdu"', sample: 'اردو' },
};

/** Font loads for Boot to wait on, so the first frame is not drawn in a fallback face. */
export function fontLoads(): Promise<unknown>[] {
    const f = FONTS[locale];
    return [
        document.fonts.load(`800 56px ${f.display}`, f.sample),
        document.fonts.load(`700 40px ${f.display}`, f.sample),
        document.fonts.load(`400 28px ${f.body}`, f.sample),
        document.fonts.load(`700 28px ${f.body}`, f.sample),
    ];
}

function swapFont(family: string): string {
    if (locale === 'en') return family;
    const f = FONTS[locale];
    if (family.includes('Baloo')) return `${f.display}, ${family}`;
    if (family.includes('Hind')) return `${f.body}, ${family}`;
    return family;
}

// --- lookup ------------------------------------------------------------------------------------------

type Entry = Partial<Record<Locale, string>>;
const table = strings as unknown as Record<string, Entry | string>;
const exact = new Map<string, string>();
const lower = new Map<string, string>();
const templates: { re: RegExp; names: string[]; out: string }[] = [];
if (locale !== 'en') {
    for (const [en, entry] of Object.entries(table)) {
        if (en.startsWith('_') || typeof entry === 'string') continue;
        const t = entry[locale];
        if (!t) continue;
        if (en.includes('{')) {
            const names: string[] = [];
            const src = en.replace(/[.*+?^$()|[\]\\]/g, '\\$&').replace(/\\?\{(\w+)\\?\}/g, (_, n: string) => (names.push(n), '(.+?)'));
            templates.push({ re: new RegExp(`^${src}$`, 'i'), names, out: t });
        } else {
            exact.set(en, t);
            lower.set(en.toLowerCase(), t);
        }
    }
}
const missing = new Set<string>();

/** The current language's text for an English string; English (as given) when there is none. */
export function tr(text: string): string {
    if (locale === 'en' || !text || !/[A-Za-z]/.test(text)) return text;
    const hit = exact.get(text) ?? lower.get(text.toLowerCase());
    if (hit) return hit;
    for (const t of templates) {
        const m = t.re.exec(text);
        if (m) return t.names.reduce((s, n, i) => s.replace(`{${n}}`, tr(m[i + 1])), t.out);
    }
    // composites the code builds: "A · B", "A: B", a leading "12 ", a trailing "  ▶" or "  →"
    for (const sep of ['   ·   ', ' · ', ': ']) {
        if (text.includes(sep)) {
            const parts = text.split(sep);
            const out = parts.map(tr);
            if (out.some((p, i) => p !== parts[i])) return out.join(sep);
        }
    }
    let m = /^(\d+)\s+(.+)$/.exec(text);
    if (m) { const r = tr(m[2]); if (r !== m[2]) return `${m[1]} ${r}`; }
    m = /^(.+?)(\s*[▶→←]\s*)$/.exec(text);
    if (m) { const r = tr(m[1]); if (r !== m[1]) return `${r}${m[2]}`; }
    m = /^([←→]\s+)(.+)$/.exec(text);
    if (m) { const r = tr(m[2]); if (r !== m[2]) return `${m[1]}${r}`; }
    if (import.meta.env.DEV && !missing.has(text)) {
        missing.add(text);
        console.debug(`[i18n:${locale}] no translation for`, JSON.stringify(text));
    }
    return text;
}

// --- the hook ---------------------------------------------------------------------------------------

/** Patch Phaser's Text once: translate on setText, script font, no letter-spacing, Urdu RTL. */
export function install() {
    document.documentElement.lang = locale;
    if (locale === 'en') return;
    const proto = GameObjects.Text.prototype as unknown as {
        setText(v: string | string[]): GameObjects.Text;
        setLetterSpacing(n: number): GameObjects.Text;
        updateText(): GameObjects.Text;
    };
    const setText = proto.setText;
    proto.setText = function (this: GameObjects.Text, value: string | string[]) {
        const self = this as GameObjects.Text & { __i18n?: boolean };
        const v = Array.isArray(value) ? value.join('\n') : value;
        setText.call(this, typeof v === 'string' ? tr(v) : v);
        if (self.__i18n) return self;
        // first call (from the constructor, once the text is in): the script's font, and for Urdu,
        // right to left with room above and below, since Nastaliq sits low and tall
        self.__i18n = true;
        const style = self.style as GameObjects.TextStyle & { fontFamily: string };
        style.fontFamily = swapFont(style.fontFamily);
        if (locale === 'ur') {
            // Nastaliq reads larger than Latin at the same size and stands much taller: 85% keeps it
            // as legible while fitting the cards and tags laid out for Latin
            const size = Math.round((parseInt(String(style.fontSize), 10) || 24) * 0.85);
            style.fontSize = `${size}px`;
            self.setRTL(true);
            self.setLineSpacing(Math.round(size * 0.35));
            self.setPadding(0, Math.round(size * 0.25), 0, Math.round(size * 0.45));
        }
        style.update(true);                    // re-measure in the new font and redraw
        return self;
    };
    proto.setLetterSpacing = function (this: GameObjects.Text) {
        (this as unknown as { letterSpacing: number }).letterSpacing = 0;
        return this;
    };
}
