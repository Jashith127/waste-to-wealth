import { AUTO, Game, Scale, Types } from 'phaser';
import { Boot } from './scenes/Boot';
import { Station01 } from './scenes/Station01';
import { Station02 } from './scenes/Station02';
import { StationCard } from './scenes/StationCard';
import { initState } from './state';
import { FRAME } from './theme';

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
    scene: [Boot, Station01, Station02, StationCard],
};

const StartGame = (parent: string) => {
    const game = new Game({ ...config, parent });
    initState(game);
    (window as unknown as { __game: Game }).__game = game;   // for Playwright screenshots
    return game;
};

export default StartGame;
