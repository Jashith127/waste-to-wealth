// Phone landscape keeps the 16:9 scene in the middle and puts everything that used to sit on top of it
// into the side gutters, in real CSS pixels, so it never covers the diorama and its words can wrap.
// Left rail: the panel buttons up top, the stick at the thumb. Right rail: the station, the step dots and
// the objective up top, the tap button at the thumb. Each control says what it does right beside it.
import type { Game } from 'phaser';
import { howToText } from './content';
import { controlHelp, currentControl, currentHint, touchText } from './controls';
import { onDeviceChange, phoneLandscape } from './device';

type Action = 'blueprint' | 'evidence' | 'help' | 'menu';
const ACTIONS: Action[] = ['blueprint', 'evidence', 'help', 'menu'];

export interface RailHandlers {
    onStick: (held: { LEFT: boolean; RIGHT: boolean; UP: boolean; DOWN: boolean }) => void;
    onSwipe: (code: 'LEFT' | 'RIGHT') => void;
    onTap: () => void;
    onAction: (action: Action) => void;
}

const NONE = { LEFT: false, RIGHT: false, UP: false, DOWN: false };

export function mountRails(game: Game, handlers: RailHandlers) {
    const left = document.getElementById('rail-left')!;
    const right = document.getElementById('rail-right')!;
    left.replaceChildren();
    right.replaceChildren();

    // left: panel buttons, then the stick with its caption
    const dock = el('div', 'rail-dock');
    const buttons = {} as Record<Action, HTMLButtonElement>;
    for (const a of ACTIONS) {
        const b = document.createElement('button');
        b.type = 'button';
        b.textContent = howToText.dock[a];
        b.addEventListener('pointerup', (e) => { e.preventDefault(); handlers.onAction(a); });
        dock.append(b);
        buttons[a] = b;
    }
    const stickBox = el('div', 'rail-ctl');
    const stickTitle = el('p', 'rail-kicker');
    const stickHelp = el('p', 'rail-help');
    const stick = el('div', 'stick');
    const knob = el('div', 'stick-knob');
    stick.append(knob);
    stickBox.append(stickTitle, stickHelp, stick);
    left.append(dock, stickBox);

    // right: where you are and what to do, then the tap button with its caption
    const now = el('div', 'rail-now');
    const head = el('div', 'rail-head');
    const badge = el('span', 'rail-badge');
    const title = el('span', 'rail-title');
    head.append(badge, title);
    const dots = el('div', 'rail-dots');
    const objective = el('p', 'rail-objective');
    now.append(head, dots, objective);
    const tapBox = el('div', 'rail-ctl');
    const tapHelp = el('p', 'rail-help');
    const tap = document.createElement('button');
    tap.type = 'button';
    tap.className = 'rail-tap';
    const screenHint = el('p', 'rail-screen');
    tapBox.append(tapHelp, tap, screenHint);
    right.append(now, tapBox);

    tap.addEventListener('pointerdown', (e) => { e.preventDefault(); tap.classList.add('down'); handlers.onTap(); });
    tap.addEventListener('pointerup', () => tap.classList.remove('down'));
    tap.addEventListener('pointercancel', () => tap.classList.remove('down'));

    let tracking = false;
    let origin = { x: 0, y: 0 };
    const place = (clientX: number, clientY: number) => {
        const box = stick.getBoundingClientRect();
        const cx = box.left + box.width / 2, cy = box.top + box.height / 2;
        const dx = clientX - cx, dy = clientY - cy;
        const dist = Math.hypot(dx, dy) || 1;
        const cl = Math.min(dist, box.width * 0.32);
        knob.style.transform = `translate(calc(-50% + ${(dx / dist) * cl}px), calc(-50% + ${(dy / dist) * cl}px))`;
        if (currentControl().stick !== 'move') return;
        const live = dist > box.width * 0.12;
        const nx = dx / dist, ny = dy / dist;
        handlers.onStick({
            RIGHT: live && nx > 0.4, LEFT: live && nx < -0.4,
            UP: live && ny < -0.4, DOWN: live && ny > 0.4,
        });
    };
    stick.addEventListener('pointerdown', (e) => {
        tracking = true;
        origin = { x: e.clientX, y: e.clientY };
        stick.setPointerCapture(e.pointerId);
        e.preventDefault();
        place(e.clientX, e.clientY);
    });
    stick.addEventListener('pointermove', (e) => { if (tracking) place(e.clientX, e.clientY); });
    const release = (e: PointerEvent) => {
        if (!tracking) return;
        tracking = false;
        knob.style.transform = 'translate(-50%, -50%)';
        handlers.onStick(NONE);
        if (currentControl().stick === 'swipe') {
            const dx = e.clientX - origin.x, dy = e.clientY - origin.y;
            if (Math.abs(dx) > 24 && Math.abs(dx) > Math.abs(dy)) handlers.onSwipe(dx > 0 ? 'RIGHT' : 'LEFT');
        }
    };
    stick.addEventListener('pointerup', release);
    stick.addEventListener('pointercancel', release);

    const sync = () => {
        const on = phoneLandscape();
        left.hidden = !on;
        right.hidden = !on;
        game.scale.refresh();
    };
    onDeviceChange(sync);
    sync();

    // only touch the DOM when something changed: update() runs every frame
    let shown = '';
    const set = (node: HTMLElement, text: string) => {
        if (node.textContent !== text) node.textContent = text;
        node.hidden = !text;
    };

    return {
        update(state: { actions: Action[]; lit: Partial<Record<Action, boolean>> } | null) {
            const hint = currentHint();
            const help = controlHelp();
            const key = JSON.stringify([state, hint, help]);
            if (key === shown) return;
            shown = key;

            left.classList.toggle('idle', !state);
            right.classList.toggle('idle', !state);
            for (const a of ACTIONS) {
                buttons[a].hidden = !state?.actions.includes(a);
                buttons[a].classList.toggle('lit', !!state?.lit[a]);
            }
            if (!state) {
                if (tracking) { tracking = false; knob.style.transform = 'translate(-50%, -50%)'; handlers.onStick(NONE); }
                return;
            }

            set(badge, hint.badge ?? '');
            set(title, hint.title ?? '');
            head.hidden = !hint.badge && !hint.title;
            dots.replaceChildren();
            if (hint.step) {
                for (let i = 0; i < hint.step.of; i++) {
                    dots.append(el('i', i < hint.step.at ? 'done' : i === hint.step.at ? 'now' : ''));
                }
                dots.append(Object.assign(el('span', ''), { textContent: `Step ${hint.step.at + 1} of ${hint.step.of}` }));
            }
            dots.hidden = !hint.step;
            set(objective, hint.text ? touchText(hint.text) : '');

            stickBox.hidden = !help.stick;
            set(stickTitle, help.stick?.title ?? '');
            set(stickHelp, help.stick?.body ?? '');
            if (!help.stick && tracking) { tracking = false; knob.style.transform = 'translate(-50%, -50%)'; handlers.onStick(NONE); }

            tap.hidden = !help.tap;
            set(tap, help.tap?.label ?? '');
            tap.classList.toggle('long', (help.tap?.label.length ?? 0) > 6);
            set(tapHelp, help.tap?.body ?? '');
            set(screenHint, help.screen ?? '');
        },
    };
}

function el(tag: string, className: string) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    return node;
}
