"""Build the data for a run without depending on the terminal interface.

World generators provide the map and starting point. This module turns that
output into the shared state used by the action layer and the curses display.
"""

from dataclasses import dataclass

from entities import create_player, spawn_random_entities
from items import spawn_random_items
from tiles import TILE_DATA, get_walkable_tiles
from worldgen import generate_overworld


@dataclass
class GameState:
    """Mutable state for one run, independent of how it is displayed.

    ``grid``, ``elevation``, and ``regions`` come from a world generator.
    Player, entities, and items change during play; ``explored`` records the
    player's map memory, while ``messages`` feeds the on-screen log.
    The remaining fields are presentation metadata supplied by a world
    profile, and ``outcome`` becomes ``victory`` or ``defeat`` when the run
    ends.
    """

    grid: list
    elevation: list
    regions: list
    player: dict
    entities: list
    items: list
    explored: list
    messages: list
    area_label: str
    location_name: str
    intro_title: str
    intro_text: str
    outcome: str | None = None


def create_game_state(
    width,
    height,
    *,
    world_generator=generate_overworld,
    seed=None,
    entity_count=15,
    item_count=12,
    area_label="Area",
    location_name="the wilderness",
    intro_title="",
    intro_text="",
    starting_message="Explore.",
):
    """Create a complete run from a generator and spawn settings.

    A generator must accept ``width``, ``height``, and ``seed`` and return
    ``(grid, elevation, regions, start_x, start_y)``. Keeping that contract
    small lets the same entity/item setup work with the overworld or dungeon.
    Spawn counts and descriptive text are parameters so a world profile can
    customize a run without changing the state-building code.
    """
    grid, elevation, regions, player_x, player_y = world_generator(
        width,
        height,
        seed=seed,
    )

    start = (player_x, player_y)
    player = create_player(*start)
    # Don't let random content cover the start, a pickup objective, or an exit.
    reserved_tiles = {
        (x, y)
        for y, row in enumerate(grid)
        for x, tile in enumerate(row)
        if TILE_DATA[tile].get("exit") or TILE_DATA[tile].get("pickup")
    }
    reserved_tiles.add(start)
    # Entities and items use the generator's region labels to choose matching
    # entries from entities.json and items.json.
    entity_tiles = get_walkable_tiles(grid, exclude=reserved_tiles)
    entities = spawn_random_entities(
        grid,
        regions,
        entity_tiles,
        count=entity_count,
    )

    # Place items after entities and exclude their occupied positions too.
    occupied_tiles = {start} | {
        (entity["x"], entity["y"]) for entity in entities
    }
    item_tiles = get_walkable_tiles(
        grid,
        exclude=occupied_tiles | reserved_tiles,
    )
    items = spawn_random_items(
        grid,
        regions,
        item_tiles,
        count=item_count,
    )

    return GameState(
        grid=grid,
        elevation=elevation,
        regions=regions,
        player=player,
        entities=entities,
        items=items,
        explored=[[False for _ in row] for row in grid],
        messages=[starting_message],
        area_label=area_label,
        location_name=location_name,
        intro_title=intro_title,
        intro_text=intro_text,
    )
