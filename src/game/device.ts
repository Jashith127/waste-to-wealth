// Phone vs desktop. The diorama stays 1920×1080 and Phaser FIT scales it to the screen; UI that must
// be readable in the hand (prompts, the briefing, the dock, the stick) uses this flag to grow and to
// speak in taps instead of keys. `?phone=1` / `?phone=0` overrides detection so a desktop browser can
// preview the phone layout.

let phone = false;

function detectPhone(): boolean {
    const q = new URLSearchParams(window.location.search).get('phone');
    if (q === '1') return true;
    if (q === '0') return false;
    const ua = navigator.userAgent || '';
    if (/iPhone|iPod|Windows Phone|webOS|BlackBerry|Opera Mini|IEMobile/i.test(ua)) return true;
    if (/Android/i.test(ua) && /Mobile/i.test(ua)) return true;
    const coarse = window.matchMedia('(pointer: coarse)').matches;
    const touch = navigator.maxTouchPoints > 0;
    const shortSide = Math.min(window.screen.width, window.screen.height);
    // A phone-sized touch screen. A laptop touchscreen has a fine pointer or a much taller short side.
    return coarse && touch && shortSide > 0 && shortSide <= 540;
}

export function isPhone() {
    return phone;
}

let onChange: () => void = () => {};

/** Side rails listen so they can show or hide when the phone rotates. */
export function onDeviceChange(fn: () => void) {
    onChange = fn;
}

/** Mark <html> with data-device and data-orient, and keep `isPhone()` current across rotation. */
export function installDevice() {
    const apply = () => {
        phone = detectPhone();
        const root = document.documentElement;
        root.dataset.device = phone ? 'phone' : 'desktop';
        root.dataset.orient = window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
        onChange();
    };
    apply();
    window.addEventListener('resize', apply);
    window.addEventListener('orientationchange', apply);
}

/** Phone held sideways: the 16:9 scene leaves room on both sides for the controls. */
export function phoneLandscape() {
    return phone && document.documentElement.dataset.orient === 'landscape';
}
