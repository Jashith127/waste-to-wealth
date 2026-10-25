import { AUTO, Game, Scale, type Scene, Types } from 'phaser';
import { runs } from './content';
import { Boot } from './scenes/Boot';
import { EndCard } from './scenes/EndCard';
import { Hud } from './scenes/Hud';
import { MarketMap } from './scenes/MarketMap';
import { SkipMenu } from './menu/SkipMenu';
import { Placeholder } from './scenes/Placeholder';
import { StationCard } from './scenes/StationCard';
import { initState } from './state';
import { FRAME } from './theme';

// Every station scene in scenes/stations/ registers itself: default-export a StationScene subclass.
const stationScenes = Object.values(
    import.meta.glob<new () => Scene>('./scenes/stations/*.ts', { eager: true, import: 'default' }),
);

// https://docs.phaser.io/api-documentation/typedef/types-core#gameconfig
const config: Types.Core.GameConfig = {
    type: AUTO,
    width: FRAME.width,
    height: FRAME.height,
    backgroundColor: '#1C1714',
    scale: {
        mode: Scale.FIT,
        autoCenter: Scale.CENTER_BOTH,
    },
    scene: [Boot, ...stationScenes, StationCard, Placeholder, MarketMap, EndCard, Hud, SkipMenu],   // Hud and SkipMenu last: they draw over every scene
};

const StartGame = (parent: string) => {
    const game = new Game({ ...config, parent });
    initState(game, { 1: runs[1].beats, 2: runs[2].beats });
    (window as unknown as { __game: Game }).__game = game;   // for Playwright screenshots
    return game;
};

export default StartGame;
