"""Build the data for a run without depending on the terminal interface.

World generators provide the map and starting point. This module turns that
output into the shared state used by the action layer and the curses display.
"""

from dataclasses import dataclass

import random

from entities import ENTITY_DATA, create_entity, create_player, spawn_random_entities
from items import create_item, spawn_random_items
from tiles import FLOOR, TILE_DATA, get_walkable_tiles
from worldgen import generate_overworld


def boss_kind_for_floor(floor_number):
    """Which boss guards a floor's stairwell.

    Every floor has a Floor Boss. Every 3rd floor the boss is a Borough
    Boss, every 9th a District Boss, and every 18th a City Boss.
    """
    if floor_number % 18 == 0:
        return "city_boss"
    if floor_number % 9 == 0:
        return "district_boss"
    if floor_number % 3 == 0:
        return "borough_boss"
    return "floor_boss"


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
    floor_number: int = 1
    boss_room: tuple | None = None
    boss: dict | None = None
    boss_announced: bool = False
    pois: dict | None = None
    rested: bool = False


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
    floor_number=1,
    player=None,
):
    """Create a complete run from a generator and spawn settings.

    A generator must accept ``width``, ``height``, and ``seed`` and return
    ``(grid, elevation, regions, start_x, start_y)``. Keeping that contract
    small lets the same entity/item setup work with the overworld or dungeon.
    Spawn counts and descriptive text are parameters so a world profile can
    customize a run without changing the state-building code.
    """
    generated = world_generator(
        width,
        height,
        seed=seed,
    )
    # Dungeon generators add the boss room as a sixth element and a POI
    # dict as a seventh; the overworld returns five parts and has neither.
    grid, elevation, regions, player_x, player_y = generated[:5]
    boss_room = generated[5] if len(generated) > 5 else None
    pois = generated[6] if len(generated) > 6 else None

    start = (player_x, player_y)
    if player is None:
        player = create_player(*start)
    else:
        # Descending to a new floor: keep the crawler, reset position and
        # the per-floor boss key, and leave HP, pack, and equipment alone.
        player["x"], player["y"] = start
        player["has_key"] = False
    # Don't let random content cover the start, a pickup objective, or an exit.
    reserved_tiles = {
        (x, y)
        for y, row in enumerate(grid)
        for x, tile in enumerate(row)
        if TILE_DATA[tile].get("exit") or TILE_DATA[tile].get("pickup")
    }
    reserved_tiles.add(start)
    if boss_room is not None:
        # The boss room is the boss's arena: no random mobs or loot in it.
        boss_x, boss_y, boss_w, boss_h = boss_room
        reserved_tiles |= {
            (x, y)
            for y in range(boss_y, boss_y + boss_h)
            for x in range(boss_x, boss_x + boss_w)
        }
    if pois:
        # POI rooms are staged by the generator: keep random spawns out
        # so the vault stays sealed, the gauntlet stays a gauntlet, the
        # safe room stays safe, and the den keeps its own pack.
        for poi in pois.values():
            poi_x, poi_y, poi_w, poi_h = poi["room"]
            reserved_tiles |= {
                (x, y)
                for y in range(poi_y, poi_y + poi_h)
                for x in range(poi_x, poi_x + poi_w)
            }
    # Entities and items use the generator's region labels to choose matching
    # entries from entities.json and items.json.
    entity_tiles = get_walkable_tiles(grid, exclude=reserved_tiles)
    entities = spawn_random_entities(
        grid,
        regions,
        entity_tiles,
        count=entity_count,
    )
    if floor_number > 1:
        # Deeper floors hit harder: regular mobs gain HP with the floor.
        for entity in entities:
            if entity.get("hostile", False):
                entity["hp"] += floor_number - 1

    # The boss spawns in its room, next to the stairwell, leashed to the
    # room so it never roams the floor.
    boss = None
    if boss_room is not None:
        boss_kind = boss_kind_for_floor(floor_number)
        boss_x, boss_y, boss_w, boss_h = boss_room
        center_x = boss_x + boss_w // 2
        center_y = boss_y + boss_h // 2
        boss_spot = None
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
            candidate = (center_x + dx, center_y + dy)
            if grid[candidate[1]][candidate[0]] == FLOOR:
                boss_spot = candidate
                break
        if boss_spot is not None:
            boss = create_entity(boss_kind, *boss_spot)
            boss["leash"] = [
                boss_x,
                boss_y,
                boss_x + boss_w - 1,
                boss_y + boss_h - 1,
            ]
            entities.append(boss)

    # The monster den gets its own pack: three hostile dungeon creatures
    # placed on the generator's spawn spots, scaled like other floor mobs.
    if pois is not None and "den" in pois:
        den_kinds = [
            kind
            for kind, data in ENTITY_DATA.items()
            if data.get("hostile", False)
            and not data.get("boss", False)
            and "ruins" in data.get("biomes", [])
        ]
        den_weights = [ENTITY_DATA[k].get("spawn_weight", 1) for k in den_kinds]
        for spawn_x, spawn_y in pois["den"]["spawns"]:
            den_kind = random.choices(den_kinds, weights=den_weights, k=1)[0]
            den_entity = create_entity(den_kind, spawn_x, spawn_y)
            if floor_number > 1:
                den_entity["hp"] += floor_number - 1
            entities.append(den_entity)

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
    if pois:
        # POI loot is staged by the generator: vault boxes behind the
        # locked door, the gauntlet's prize, the den's guarded box.
        for poi in pois.values():
            for loot_x, loot_y, loot_kind in poi.get("loot", []):
                items.append(create_item(loot_kind, loot_x, loot_y))

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
        floor_number=floor_number,
        boss_room=boss_room,
        boss=boss,
        pois=pois,
    )
