// Typed access to src/data/. All game text and numbers come from these JSON files.
import evidenceMap from '../data/evidence-map.json';
import s01 from '../data/stations/s01.json';
import s02 from '../data/stations/s02.json';
import type { Meaning } from './theme';
import type { Run } from './state';

export type Lane = 'vendor' | 'frontstage' | 'backstage' | 'support' | 'evidence';

export interface BlueprintItem {
    lane: Lane;
    text: string;
    evidence: string[];
    proposed?: boolean;
}

export interface StationData {
    id: string;
    number: number;
    title: string;
    place: string;
    evidence: string[];
    greybox?: boolean;
    runs: Record<string, { prompts?: Record<string, string>; next?: string; summary?: string; proposed?: boolean }>;
    blueprint?: Record<string, BlueprintItem[]>;
    kilo?: { label: string; tag: { value: string; meaning: Meaning; note?: string }; evidence: string[] };
    [extra: string]: unknown;
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

const stations: Record<string, StationData> = { s01, s02 } as unknown as Record<string, StationData>;

export function station(id: string): StationData {
    const s = stations[id];
    if (!s) throw new Error(`no station data for ${id}`);
    return s;
}

export function runData(s: StationData, run: Run) {
    return s.runs[String(run)] ?? {};
}

export function blueprint(s: StationData, run: Run): BlueprintItem[] {
    return s.blueprint?.[String(run)] ?? [];
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
