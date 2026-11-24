"""Procedural room-and-corridor map generation for dungeon runs.

The returned tuple matches ``worldgen.generate_overworld`` so the common
game-state factory can add a player, creatures, and loot to either map.
"""

import random

from tiles import EXIT, FLOOR, SPIKE, WALL


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


def generate_dungeon(width, height, seed=None):
    """Generate connected dungeon rooms and corridors.

    Returns the same grid, elevation, region, and starting-coordinate tuple
    as the overworld generator, so it can be used by ``create_game_state``.
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

    # Hazards are placed in room interiors. Even where a corridor crosses a
    # room, spikes remain walkable, so they add risk without cutting off the exit.
    for x, y, room_width, room_height in rooms:
        for room_y in range(y + 1, y + room_height - 1):
            for room_x in range(x + 1, x + room_width - 1):
                is_start_or_exit = (room_x, room_y) in (centers[0], centers[-1])
                if not is_start_or_exit and rng.random() < 0.025:
                    grid[room_y][room_x] = SPIKE

    start_x, start_y = centers[0]
    exit_x, exit_y = centers[-1]
    grid[exit_y][exit_x] = EXIT

    # The existing ruin creature and loot tables use the "ruins" region tag.
    # Walls share the tag, but only walkable cells are considered for spawns.
    regions = [
        ["ruins" for _ in range(width)]
        for _ in range(height)
    ]
    elevation = [[0.0 for _ in range(width)] for _ in range(height)]
    # Keep the same five-part interface as the overworld generator.
    return grid, elevation, regions, start_x, start_y
