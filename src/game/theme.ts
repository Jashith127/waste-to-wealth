// Design tokens from docs/art-bible.md §3 and §8. UI code uses these names, never raw hex.

export const FRAME = { width: 1920, height: 1080 } as const;

export const colour = {
    cost: 0xc42b20,      // waste as a cost, −₹5
    income: 0x2e6b34,    // money in, Chamber A
    pay: 0xf0a31f,       // payment accent
    offsite: 0x1f5ba8,   // off-site; Chamber B
    cream: 0xf4ecde,
    card: 0xfbf7ef,
    ink: 0x1c1714,
    brown: 0x7a4b2c,
    void: 0x1c1714,
} as const;

export const css = {
    cost: '#C42B20', income: '#2E6B34', pay: '#F0A31F', offsite: '#1F5BA8',
    cream: '#F4ECDE', card: '#FBF7EF', ink: '#1C1714', brown: '#7A4B2C', muted: '#5E554E',
} as const;

export type Meaning = 'cost' | 'income' | 'pay' | 'offsite';

export const font = {
    display: '"Baloo 2", system-ui, sans-serif',
    body: 'Hind, system-ui, sans-serif',
} as const;

// Sizes at the 1920×1080 base frame (the canvas scales to fit; art-bible §8 minimums hold at 720p).
export const size = { stationTitle: 56, cardHeading: 36, body: 28, hud: 40, small: 22 } as const;

// Layout (art-bible §6.3)
export const layout = {
    hudBand: 96,
    blueprintTop: 660,          // nothing the player needs sits below this line
    blueprintHeight: 420,
    evidenceButton: { x: 1830, y: 56, r: 30 },
    prompt: { x: 48, y: 56 },
    gutter: 48,
} as const;

export const motion = {
    fast: 180,
    normal: 240,
    tagFlip: 300,
    transition: 650,
} as const;

export const cardStyle = { outline: 3, radius: 14, band: 12 } as const;
