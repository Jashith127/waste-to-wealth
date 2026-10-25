// Typed access to src/data/. All game text and numbers come from these JSON files.
// New station files in src/data/stations/ are picked up automatically.
import evidenceMap from '../data/evidence-map.json';
import runsData from '../data/runs.json';
import type { Meaning } from './theme';
import type { Run } from './state';

export type Lane = 'vendor' | 'frontstage' | 'backstage' | 'support' | 'evidence';

export interface BlueprintItem {
    lane: Lane;
    text: string;
    evidence: string[];
    proposed?: boolean;
}

export interface Tag { value: string; meaning: Meaning; note?: string }

export interface RunData { prompts?: Record<string, string>; next?: string; summary?: string; proposed?: boolean }

export interface StationData {
    id: string;
    number: number;
    title: string;
    label?: string;
    place: string;
    evidence: string[];
    greybox?: boolean;
    set: { blend: string; renders: string; lighting: string };
    runs: Partial<Record<'1' | '2', RunData>>;
    blueprint?: Partial<Record<'1' | '2', BlueprintItem[]>>;
    kilo?: { label: string; tag: Tag; evidence: string[] };
    signs?: unknown[];
    params?: Record<string, unknown>;
}

export interface Source {
    kind: string;
    title?: string;
    file?: string;
    url?: string;
    deck_page?: number;
    licence?: string;
    credit?: string;
    supports?: string;
    proposed?: boolean;
}

export type ClockPhase = 'morning' | 'evening' | 'night';

export interface RunInfo { title: string; subtitle: string; beats: string[]; target_seconds?: number; proposed?: boolean; evidence: string[]; clock?: Record<string, ClockPhase> }

const files = import.meta.glob<StationData>('../data/stations/*.json', { eager: true, import: 'default' });
const stations: Record<string, StationData> = Object.fromEntries(Object.values(files).map((s) => [s.id, s]));

export const runs = runsData as unknown as Record<Run, RunInfo>;

export function station(id: string): StationData {
    const s = stations[id];
    if (!s) throw new Error(`no station data for ${id} (add src/data/stations/${id}.json)`);
    return s;
}

/** False until a station task adds src/data/stations/<id>.json; the grey-box placeholder still plays the beat. */
export function hasStation(id: string): boolean {
    return id in stations;
}

export function runData(s: StationData, run: Run): RunData {
    return s.runs[String(run) as '1' | '2'] ?? {};
}

export function blueprint(s: StationData, run: Run): BlueprintItem[] {
    return s.blueprint?.[String(run) as '1' | '2'] ?? [];
}

export function source(id: string): Source {
    const src = (evidenceMap.sources as Record<string, Source>)[id];
    if (!src) throw new Error(`evidence id ${id} is not in evidence-map.json`);
    return src;
}

export const LANE_LABELS: Record<Lane, string> = {
    vendor: 'Vendor action',
    frontstage: 'Frontstage',
    backstage: 'Backstage',
    support: 'Support',
    evidence: 'Evidence',
};
