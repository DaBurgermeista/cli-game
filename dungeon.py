"""Procedural room-and-corridor map generation for dungeon runs.

The returned tuple matches ``worldgen.generate_overworld`` so the common
game-state factory can add a player, creatures, and loot to either map.
"""

import random

from tiles import CAMPFIRE, EXIT, FLOOR, KEY, LOCKED_DOOR, SPIKE, WALL


def _carve_room(grid, x, y, width, height):
    """Replace a rectangular area of wall with floor; return its center."""
    for room_y in range(y, y + height):
        for room_x in range(x, x + width):
            grid[room_y][room_x] = FLOOR
    return x + width // 2, y + height // 2


def _carve_corridor(grid, start, end, rng):
    """Connect two room centers with an L-shaped, always-walkable passage."""
    x1, y1 = start
    x2, y2 = end

    if rng.choice((True, False)):
        horizontal = range(min(x1, x2), max(x1, x2) + 1)
        for x in horizontal:
            grid[y1][x] = FLOOR
        vertical = range(min(y1, y2), max(y1, y2) + 1)
        for y in vertical:
            grid[y][x2] = FLOOR
    else:
        vertical = range(min(y1, y2), max(y1, y2) + 1)
        for y in vertical:
            grid[y][x1] = FLOOR
        horizontal = range(min(x1, x2), max(x1, x2) + 1)
        for x in horizontal:
            grid[y2][x] = FLOOR


def _rect_tiles(room):
    """Every tile of a room rect, walls included."""
    x, y, width, height = room
    return {
        (room_x, room_y)
        for room_y in range(y, y + height)
        for room_x in range(x, x + width)
    }


def _interior_tiles(grid, room):
    """Walkable floor tiles strictly inside a room."""
    x, y, width, height = room
    return [
        (room_x, room_y)
        for room_y in range(y + 1, y + height - 1)
        for room_x in range(x + 1, x + width - 1)
        if grid[room_y][room_x] == FLOOR
    ]


def _reachable(grid, start, targets):
    """True when every target is reachable from start without locked doors.

    Locked vault doors count as walls here: a POI must never gate the
    key, the boss room, or any other room behind itself.
    """
    from tiles import TILE_DATA

    width, height = len(grid[0]), len(grid)
    seen = {start}
    frontier = [start]
    while frontier:
        x, y = frontier.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in seen:
                continue
            if not TILE_DATA.get(grid[ny][nx], {}).get("walkable", False):
                continue
            seen.add((nx, ny))
            frontier.append((nx, ny))
    return all(target in seen for target in targets)


def _build_vault(grid, room, rng):
    """Seal a room behind locked doors with loot inside and a key outside.

    Returns the vault POI dict, or None when the room cannot be sealed
    without cutting off the key, another room, or the stairwell.
    """
    interior = _interior_tiles(grid, room)
    if len(interior) < 2:
        return None
    loot_spots = rng.sample(interior, 2)

    # A vault mouth is a floor tile just outside the room that touches a
    # room floor tile: sealing each one closes the room.
    x, y, width, height = room
    room_tiles = _rect_tiles(room)
    mouths = []
    for ring_y in range(y - 1, y + height + 1):
        for ring_x in range(x - 1, x + width + 1):
            if (ring_x, ring_y) in room_tiles:
                continue
            if grid[ring_y][ring_x] != FLOOR:
                continue
            if any(
                (ring_x + dx, ring_y + dy) in room_tiles
                and grid[ring_y + dy][ring_x + dx] == FLOOR
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                mouths.append((ring_x, ring_y))
    if not mouths:
        return None

    for mouth_x, mouth_y in mouths:
        grid[mouth_y][mouth_x] = LOCKED_DOOR
    loot = [
        (loot_x, loot_y, kind)
        for (loot_x, loot_y), kind in zip(
            loot_spots, ("loot_box_bronze", "loot_box_silver")
        )
    ]
    return {"room": room, "loot": loot, "mouths": mouths, "key": None}


def generate_dungeon(width, height, seed=None):
    """Generate connected dungeon rooms and corridors.

    Returns the same grid, elevation, region, and starting-coordinate tuple
    as the overworld generator, plus the boss room ``(x, y, width, height)``
    as a sixth element and a POI dict as a seventh. The boss room is the
    largest room that is not the start room; the stairwell sits inside it,
    and the boss guards it.
    """
    if width < 24 or height < 16:
        raise ValueError("Dungeon maps must be at least 24x16.")

    # A local generator makes the dungeon layout repeatable for a supplied
    # seed without resetting the shared RNG used later for spawns and combat.
    rng = random.Random(seed)
    grid = [[WALL for _ in range(width)] for _ in range(height)]
    rooms = []
    centers = []

    # Randomly place rooms. Connecting each new room to the previous one
    # produces one connected chain, while the attempt limit keeps generation
    # time bounded even when the map gets crowded.
    for _ in range(max(80, (width * height) // 8)):
        room_width = rng.randint(5, min(12, width - 4))
        room_height = rng.randint(4, min(8, height - 4))
        x = rng.randint(1, width - room_width - 1)
        y = rng.randint(1, height - room_height - 1)

        # Keep a one-tile wall between rooms unless a corridor joins them.
        if any(
            x - 1 < other_x + other_width
            and x + room_width + 1 > other_x
            and y - 1 < other_y + other_height
            and y + room_height + 1 > other_y
            for other_x, other_y, other_width, other_height in rooms
        ):
            continue

        center = _carve_room(grid, x, y, room_width, room_height)
        if centers:
            _carve_corridor(grid, centers[-1], center, rng)
        centers.append(center)
        rooms.append((x, y, room_width, room_height))

    if len(centers) < 2:
        # Keep a distinct start and exit even on a layout with few placements.
        grid = [[WALL for _ in range(width)] for _ in range(height)]
        rooms = []
        first = (1, 1, 6, 5)
        last = (width - 7, height - 6, 6, 5)
        centers = [
            _carve_room(grid, *first),
            _carve_room(grid, *last),
        ]
        rooms.extend((first, last))
        _carve_corridor(grid, centers[0], centers[1], rng)

    # The boss room is the largest room that is not the start room, so the
    # boss always has a real arena and the start stays safe. The stairwell
    # sits at its center: reaching the exit means going through the boss.
    start_room = rooms[0]
    boss_room = max(
        (room for room in rooms if room != start_room),
        key=lambda room: room[2] * room[3],
    )
    boss_center_x = boss_room[0] + boss_room[2] // 2
    boss_center_y = boss_room[1] + boss_room[3] // 2

    # Hazards are placed in room interiors. Even where a corridor crosses a
    # room, spikes remain walkable, so they add risk without cutting off the exit.
    for x, y, room_width, room_height in rooms:
        for room_y in range(y + 1, y + room_height - 1):
            for room_x in range(x + 1, x + room_width - 1):
                is_start_or_exit = (room_x, room_y) in (
                    centers[0],
                    (boss_center_x, boss_center_y),
                )
                if not is_start_or_exit and rng.random() < 0.025:
                    grid[room_y][room_x] = SPIKE

    start_x, start_y = centers[0]
    exit_x, exit_y = boss_center_x, boss_center_y
    grid[exit_y][exit_x] = EXIT

    # Points of interest: up to two rooms that are not the start room or
    # the boss room, each becoming one POI type. POIs add loot, danger, or
    # rest without ever gating the rest of the floor behind themselves.
    pois = {}
    poi_rooms = [room for room in rooms[1:] if room != boss_room]
    rng.shuffle(poi_rooms)
    poi_types = ["vault", "trap", "safe", "den", "training"]
    rng.shuffle(poi_types)
    for room, poi_type in zip(poi_rooms[:2], poi_types[:2]):
        if poi_type == "vault":
            vault = _build_vault(grid, room, rng)
            if vault is None:
                continue
            # The vault key spawns on the open floor, outside the vault
            # and boss rooms, so it is always findable before the vault.
            vault_room_tiles = _rect_tiles(room)
            boss_room_tiles = _rect_tiles(boss_room)
            key_spots = [
                (x, y)
                for y, row in enumerate(grid)
                for x, tile in enumerate(row)
                if tile == FLOOR
                and (x, y) not in vault_room_tiles
                and (x, y) not in boss_room_tiles
                and (x, y) != (start_x, start_y)
            ]
            if not key_spots:
                for mouth_x, mouth_y in vault["mouths"]:
                    grid[mouth_y][mouth_x] = FLOOR
                continue
            key_x, key_y = rng.choice(key_spots)
            grid[key_y][key_x] = KEY
            vault["key"] = (key_x, key_y)
            # The vault is optional: key, rooms, and stairwell must all
            # stay reachable without passing through its locked doors.
            # (The vault room's own center is sealed by design, so it is
            # not a target: it is reachable only with the key.)
            vault_center = (room[0] + room[2] // 2, room[1] + room[3] // 2)
            targets = [
                center for center in centers if center != vault_center
            ] + [(exit_x, exit_y), (key_x, key_y)]
            if not _reachable(grid, (start_x, start_y), targets):
                for mouth_x, mouth_y in vault["mouths"]:
                    grid[mouth_y][mouth_x] = FLOOR
                grid[key_y][key_x] = FLOOR
                continue
            pois["vault"] = vault
        elif poi_type == "trap":
            interior = _interior_tiles(grid, room)
            if not interior:
                continue
            loot_x, loot_y = rng.choice(interior)
            for tile_x, tile_y in interior:
                if (tile_x, tile_y) != (loot_x, loot_y) and rng.random() < 0.4:
                    grid[tile_y][tile_x] = SPIKE
            pois["trap"] = {
                "room": room,
                "loot": [(loot_x, loot_y, "loot_box_silver")],
            }
        elif poi_type == "safe":
            center_x = room[0] + room[2] // 2
            center_y = room[1] + room[3] // 2
            grid[center_y][center_x] = CAMPFIRE
            pois["safe"] = {"room": room, "fire": (center_x, center_y)}
        elif poi_type == "training":
            # A quiet room with two dummies: a safe place to practice a
            # weapon style. Dummies never fight back, move, or drop loot.
            interior = _interior_tiles(grid, room)
            if len(interior) < 2:
                continue
            spawn_spots = rng.sample(interior, 2)
            pois["training"] = {"room": room, "spawns": spawn_spots}
        elif poi_type == "den":
            interior = _interior_tiles(grid, room)
            if len(interior) < 4:
                continue
            center_x = room[0] + room[2] // 2
            center_y = room[1] + room[3] // 2
            spawn_spots = rng.sample(
                [tile for tile in interior if tile != (center_x, center_y)],
                3,
            )
            pois["den"] = {
                "room": room,
                "loot": [(center_x, center_y, "loot_box_bronze")],
                "spawns": spawn_spots,
            }

    # The existing ruin creature and loot tables use the "ruins" region tag.
    # Walls share the tag, but only walkable cells are considered for spawns.
    regions = [
        ["ruins" for _ in range(width)]
        for _ in range(height)
    ]
    elevation = [[0.0 for _ in range(width)] for _ in range(height)]
    # The boss room rides along as a sixth element and the POI dict as a
    # seventh; create_game_state handles generators that return five parts
    # (like the overworld) too.
    return grid, elevation, regions, start_x, start_y, boss_room, pois
