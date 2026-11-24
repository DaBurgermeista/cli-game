# Dungeon Crawler Carl Game

Early Python/curses exploration-game prototype, themed on Dungeon Crawler Carl.

## Controls

- `W`, `A`, `S`, `D` or arrow keys: move
- `G`: pick up the item under you
- `I`: open inventory (arrows/W/S to select, Enter to use, `D` to drop, Esc to close)
- `H`: quick-heal with the first healing item
- `.`: wait one turn
- `F`: toggle full-map debug reveal
- `E`: toggle elevation debug view
- `Q`: quit

The main menu offers both the original overworld and Floor 1, a generated dungeon run. You play as Carl, a crawler in the Borant dungeon.

## Current features

- Procedural overworld generation
- Rivers, lakes, bridges, forests, and buildings
- Scrolling camera
- Field of view and explored-map memory
- Boss keys, stairwells, spike traps, and turn-based entity movement
- Connected-room dungeon generation
- A game-state/action layer separate from curses input

## How a run is assembled

- `world_profiles.py` defines the modes shown in the main menu. Each profile
  selects a map generator, map size, and introductory text.
- `game_state.py` calls that generator and creates the player, entities,
  items, explored-map memory, and message log in a `GameState`.
- `crawler.py` draws the state and translates keyboard input into a
  `GameAction`.
- `game_actions.py` applies the action and advances hazards and enemies.
  It returns discoveries or an ending for the curses interface to display.
- `dungeon.py` and `worldgen.py` produce maps using the same generator
  interface, so both modes share the same state and action rules.

## Status

Early development prototype. Gameplay systems and objectives are still in progress.

## v0.2.0

- Added tall-grass terrain patches
- Added Borant shrine and safe-room landmarks
- Added reusable modal text panels for discoveries and future dialogue
- Added a persistent message log
- Improved map variety and exploration feedback
