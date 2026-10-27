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

// Layout (art-bible §6.3). The HUD keeps to the corners: the objective card top left, the kilo's
// docked tag top right, the control dock bottom left. Scene content starts below hudBottom.
export const layout = {
    hudBottom: 140,             // the objective card's lower edge, with a little air
    blueprintTop: 660,          // nothing the player needs sits below this line
    blueprintHeight: 420,
    prompt: { x: 32, y: 20 },   // the objective card's top-left corner
    dock: { x: 32, y: 1036, h: 54, gap: 12 },   // the control dock's left end, vertical centre
    gutter: 48,
} as const;

// HUD surfaces: dark game panels over the set, cream deck cards for briefings.
export const hud = {
    panel: 0x1c1714,
    panelAlpha: 0.9,
    shadow: 0x000000,
    dim: '#B8AE9C',             // secondary text on a dark panel
    keyLip: 0xb3a691,           // the underside of a key cap
} as const;

export const motion = {
    fast: 180,
    normal: 240,
    tagFlip: 300,
    transition: 650,
} as const;

export const cardStyle = { outline: 3, radius: 14, band: 12 } as const;
