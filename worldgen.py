import random
from tiles import (
    WALL,
    FLOOR,
    DOOR,
    KEY,
    EXIT,
    TREE,
    WATER,
    BRIDGE,
    BANK,
    SHRINE,
    ROCK,
    CAMPFIRE,
    TALL_GRASS,
    MOUNTAIN,
    HILL,
)

BASE_ELEVATION = 3
MAX_ELEVATION = 9
MIN_WORLD_WIDTH = 30
MIN_WORLD_HEIGHT = 20

def raise_hill(elevation, center_x, center_y, radius, peak_height):
    height = len(elevation)
    width = len(elevation[0])

    for y in range(max(0, center_y - radius), min(height, center_y + radius + 1)):
        for x in range(max(0, center_x - radius), min(width, center_x + radius + 1)):
            distance_squared = (x - center_x) ** 2 + (y - center_y) ** 2

            if distance_squared > radius ** 2:
                continue

            height_range = peak_height - BASE_ELEVATION
            distance = int(distance_squared ** 0.5)
            height_loss = (distance * height_range) // radius
            tile_height = peak_height - height_loss

            elevation[y][x] = max(elevation[y][x], tile_height)

def lower_basin(
    elevation,
    center_x,
    center_y,
    radius,
    floor_elevation=1,
):
    height = len(elevation)
    width = len(elevation[0])

    for y in range(
        max(1, center_y - radius),
        min(height - 1, center_y + radius + 1),
    ):
        for x in range(
            max(1, center_x - radius),
            min(width - 1, center_x + radius + 1),
        ):
            distance_squared = (x - center_x) ** 2 + (y - center_y) ** 2

            if distance_squared > radius ** 2:
                continue

            distance = distance_squared ** 0.5

            # Center is low; the basin rises gradually to BASE_ELEVATION
            # at its outer edge.
            progress_to_edge = distance / radius

            target_elevation = round(
                floor_elevation
                + (BASE_ELEVATION - floor_elevation) * progress_to_edge
            )

            # Never raise terrain; only lower it toward the basin shape.
            elevation[y][x] = min(
                elevation[y][x],
                target_elevation,
            )

def create_elevation_map(width, height):
    elevation = [
        [BASE_ELEVATION for _ in range(width)]
        for _ in range(height)
    ]

    # Broad rolling hills. These shape terrain but do not create mountains.
    for _ in range(5):
        center_x = random.randint(width // 8, width - (width // 8) - 1)
        center_y = random.randint(height // 8, height - (height // 8) - 1)

        radius = random.randint(8, 16)
        peak_height = random.randint(5, 7)

        raise_hill(
            elevation,
            center_x,
            center_y,
            radius,
            peak_height,
        )

    # Smaller number of high mountain regions.
    for _ in range(3):
        center_x = random.randint(width // 6, width - (width // 6) - 1)
        center_y = random.randint(height // 6, height - (height // 6) - 1)

        radius = random.randint(6, 12)
        peak_height = random.randint(8, MAX_ELEVATION)

        raise_hill(
            elevation,
            center_x,
            center_y,
            radius,
            peak_height,
        )

    return elevation

def smooth_elevation(elevation, passes=2):
    height = len(elevation)
    width = len(elevation[0])

    for _ in range(passes):
        result = [row[:] for row in elevation]

        for y in range(1, height - 1):
            for x in range(1, width - 1):
                neighbors = [
                    elevation[y - 1][x],
                    elevation[y + 1][x],
                    elevation[y][x - 1],
                    elevation[y][x + 1],
                    elevation[y][x],
                ]

                result[y][x] = round(sum(neighbors) / len(neighbors))

        elevation = result

    return elevation

def apply_mountains(grid, elevation, mountain_height=8):
    height = len(grid)
    width = len(grid[0])

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            # Only high elevation floors become mountains
            if elevation[y][x] >= mountain_height and grid[y][x] == FLOOR:
                grid[y][x] = MOUNTAIN

def apply_hills(grid, elevation, hill_height=7):
    height = len(grid)
    width = len(grid[0])

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            # Remaining high-elevation floor tiles become hills.
            if elevation[y][x] >= hill_height and grid[y][x] == FLOOR:
                grid[y][x] = HILL

def create_overworld(width, height):
    grid = [[FLOOR for _ in range(width)] for _ in range(height)]

    for x in range(width):
        grid[0][x] = WALL
        grid[height - 1][x] = WALL

    for y in range(height):
        grid[y][0] = WALL
        grid[y][width - 1] = WALL

    return grid

def stamp_blob(grid, center_x, center_y, tile_type, scale=0.04, replaceable_tiles=(FLOOR, BANK)):
    height = len(grid)
    width = len(grid[0])

    # Calculate steps based on total map area
    steps = int((width * height) * scale)

    fx, fy = center_x, center_y

    for _ in range(steps):
        if 2 < fx < width - 3 and 2 < fy < height - 3:
            if grid[fy][fx] in replaceable_tiles:
                grid[fy][fx] = tile_type
        
        dx, dy = random.choice([(0, -1), (0, 1), (1, 0), (-1, 0)])
        fx += dx
        fy += dy

def stamp_lake(grid, center_x, center_y, radius):
    height = len(grid)
    width = len(grid[0])

    water_tiles = []

    for y in range(
        max(1, center_y - radius),
        min(height - 1, center_y + radius + 1),
    ):
        for x in range(
            max(1, center_x - radius),
            min(width - 1, center_x + radius + 1),
        ):
            distance_squared = (x - center_x) ** 2 + (y - center_y) ** 2

            if distance_squared > radius ** 2:
                continue

            # Leaves the shoreline a little irregular.
            edge_chance = distance_squared / (radius ** 2)

            if edge_chance > 0.65 and random.random() < 0.30:
                continue

            if grid[y][x] not in (FLOOR, BANK, WATER):
                continue

            grid[y][x] = WATER
            water_tiles.append((x, y))

    # Add banks around the lake after placing water.
    for x, y in water_tiles:
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx = x + dx
            ny = y + dy

            if (
                1 <= nx < width - 1
                and 1 <= ny < height - 1
                and grid[ny][nx] == FLOOR
            ):
                grid[ny][nx] = BANK

def carve_river(grid, elevation, bridge_y=None):
    height = len(grid)
    width = len(grid[0])

    if bridge_y is None:
        bridge_y = random.randint(height // 3, (height * 2) // 3)

    bridge_rows = {bridge_y, bridge_y + 1}

    river_width = random.choice([2, 3])
    rx = random.randint(width // 4, (width * 3) // 4)

    river_path = []

    for ry in range(1, height - 1):
        # Occasionally vary river width, but keep it narrow enough to cross.
        if random.random() < 0.15:
            river_width = max(
                2,
                min(4, river_width + random.choice([-1, 1])),
            )

        min_x = 2
        max_x = width - river_width - 3

        # The river can drift one tile left, right, or continue straight.
        candidate_xs = [
            candidate_x
            for candidate_x in (rx - 1, rx, rx + 1)
            if min_x <= candidate_x <= max_x
        ]

        # Score each possible path by its elevation ahead of the river.
        # Lower terrain is more likely, but randomness prevents rigid routes.
        candidate_scores = []

        for candidate_x in candidate_xs:
            samples = []

            for look_ahead_y in range(ry, min(height - 1, ry + 3)):
                for offset in range(river_width):
                    samples.append(
                        elevation[look_ahead_y][candidate_x + offset]
                    )

            candidate_scores.append(sum(samples) / len(samples))

        lowest_score = min(candidate_scores)

        # Lower elevations receive higher weight. The +1 avoids division by zero.
        weights = [
            1 / (score - lowest_score + 1)
            for score in candidate_scores
        ]

        rx = random.choices(
            candidate_xs,
            weights=weights,
            k=1,
        )[0]

        river_path.append((rx, ry, river_width))

    # Lay down the river after choosing its full path.
    for rx, ry, river_width in river_path:
        tile_type = BRIDGE if ry in bridge_rows else WATER

        for offset in range(river_width):
            grid[ry][rx + offset] = tile_type

    # Add banks after the river so bends do not overwrite them.
    for rx, ry, river_width in river_path:
        left_bank_x = rx - 1
        right_bank_x = rx + river_width

        if grid[ry][left_bank_x] == FLOOR:
            grid[ry][left_bank_x] = BANK

        if grid[ry][right_bank_x] == FLOOR:
            grid[ry][right_bank_x] = BANK

    return {
        "bridge_y": bridge_y,
        "path": river_path,
    }

def stamp_forest_near_water(grid, scale=0.02, clusters=4):
    water_tiles = [
        (x, y)
        for y, row in enumerate(grid)
        for x, tile in enumerate(row)
        if tile == WATER
    ]

    if not water_tiles:
        return

    wx, wy = random.choice(water_tiles)

    for _ in range(clusters):
        start_x = wx + random.randint(-4, 4)
        start_y = wy + random.randint(-4, 4)
        stamp_blob(grid, start_x, start_y, TREE, scale=scale)

def stamp_forest_patch(grid, center_x, center_y, radius):
    height = len(grid)
    width = len(grid[0])

    for y in range(max(1, center_y - radius), min(height - 1, center_y + radius + 1)):
        for x in range(max(1, center_x - radius), min(width - 1, center_x + radius + 1)):
            distance = abs(x - center_x) + abs(y - center_y)

            if distance > radius:
                continue

            # Dense center, irregular outer edge.
            chance = 0.85 - (distance / (radius + 1)) * 0.45

            if grid[y][x] == FLOOR and random.random() < chance:
                grid[y][x] = TREE

def scatter_rocks(grid, elevation, minimum_elevation=6, chance=0.08):
    height = len(grid)
    width = len(grid[0])

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if (
                elevation[y][x] >= minimum_elevation
                and grid[y][x] == FLOOR
                and random.random() < chance
            ):
                grid[y][x] = ROCK

def stamp_building(grid, w=7, h=5, interior_item=None, is_ruin=False, biomes=None):
    height = len(grid)
    width = len(grid[0])

    # Try 50 times to find a dry, open spot on map
    for _ in range(50):
        x1 = random.randint(3, width - w - 4)
        y1 = random.randint(3, height - h - 4)

        # Check footprint
        spot_clear = True
        for y in range(y1 - 2, y1 + h + 2):
            for x in range(x1 - 2, x1 + w + 2):
                if 0 <= y < height and 0 <= x < width:
                    if grid[y][x] in (WATER, BRIDGE, WALL, DOOR, KEY, EXIT, TREE):
                        spot_clear = False
                        break
            if not spot_clear:
                break

        if spot_clear:
            for y in range(y1, y1 + h):
                for x in range(x1, x1 + w):
                    is_edge = (y == y1 or y == y1 + h - 1 or x == x1 or x == x1 + w - 1)
                    if is_edge:
                        if is_ruin and random.random() < 0.25:
                            grid[y][x] = FLOOR
                        else:
                            grid[y][x] = WALL
                    else:
                        grid[y][x] = FLOOR

            # Punch a doorway
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                grid[y1][x1 + (w // 2)] = DOOR
            elif side == "bottom":
                grid[y1 + h - 1][x1 + (w //2)] = DOOR
            elif side == "left":
                grid[y1 + (h // 2)][x1] = DOOR
            elif side == "right":
                grid[y1 + (h // 2)][x1 + w - 1] = DOOR

            # Place the key, Exit, or loot
            if interior_item:
                center_x = x1 + (w // 2)
                center_y = y1 + (h // 2)
                grid[center_y][center_x] = interior_item            

            if biomes is not None:
                tag = "ruins" if is_ruin else "building"
                for y in range(y1, y1 + h):
                    for x in range(x1, x1 + w):
                        biomes[y][x] = tag

            return True # Successfully places

    return False # Could not place

def stamp_shrine(grid, biomes=None):
    height = len(grid)
    width = len(grid[0])

    # 5 x 5 landmark needs a one-tile safety margin around it
    for _ in range(50):
        center_x = random.randint(3, width - 4)
        center_y = random.randint(3, height - 4)

        # Only place the shring on ordinary open floor
        spot_clear = True

        for y in range(center_y - 2, center_y + 3):
            for x in range(center_x - 2, center_x + 3):
                if grid[y][x] != FLOOR:
                    spot_clear = False
                    break
            
            if not spot_clear:
                break

        if not spot_clear:
            continue

        # Four standing stones around a walkable shrine center
        grid[center_y - 2][center_x - 1] = ROCK
        grid[center_y - 2][center_x + 1] = ROCK
        grid[center_y + 2][center_x - 1] = ROCK
        grid[center_y + 2][center_x + 1] = ROCK

        grid[center_y][center_x] = SHRINE

        if biomes is not None:
            for y in range(center_y - 2, center_y + 3):
                for x in range(center_x - 2, center_x + 3):
                    biomes[y][x] = "shrine"

        return {
            "kind": "shrine",
            "x": center_x,
            "y": center_y,
        }

    return None

def stamp_abandoned_camp(grid, biomes=None):
    height = len(grid)
    width = len(grid[0])

    # The camp occupies a 5x5 area.
    for _ in range(50):
        center_x = random.randint(3, width - 4)
        center_y = random.randint(3, height - 4)

        # Only place camps in clear ordinary floor terrain.
        spot_clear = True

        for y in range(center_y - 2, center_y + 3):
            for x in range(center_x - 2, center_x + 3):
                if grid[y][x] != FLOOR:
                    spot_clear = False
                    break

            if not spot_clear:
                break

        if not spot_clear:
            continue

        # Campfire at the center.
        grid[center_y][center_x] = CAMPFIRE

        # A rough ring of stones around the fire.
        grid[center_y + 1][center_x] = ROCK
        grid[center_y][center_x - 1] = ROCK
        grid[center_y][center_x + 1] = ROCK

        if biomes is not None:
            for y in range(center_y - 2, center_y + 3):
                for x in range(center_x - 2, center_x + 3):
                    biomes[y][x] = "camp"

        return {
            "kind": "abandoned_camp",
            "x": center_x,
            "y": center_y,
        }

    return None

def find_open_floor(grid, occupied=None):
    if occupied is None:
        occupied = set()

    floor_tiles = []

    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] == FLOOR and (x, y) not in occupied:
                floor_tiles.append((x, y))

    if not floor_tiles:
        raise RuntimeError("No open floor tiles are available.")

    return random.choice(floor_tiles)

def create_biome_map(grid, elevation):
    height = len(grid)
    width = len(grid[0])
    biomes = [["plains" for _ in range(width)] for _ in range(height)]

    for y in range(height):
        for x in range(width):
            tile = grid[y][x]
            elev = elevation[y][x]

            if tile in (WATER, BRIDGE):
                biomes[y][x] = "water"
            elif tile == BANK:
                biomes[y][x] = "riverbank"
            elif tile == TREE:
                biomes[y][x] = "forest"
            elif tile == TALL_GRASS:
                biomes[y][x] = "meadow"
            elif tile in (MOUNTAIN, HILL) or elev >= 7:
                biomes[y][x] = "highlands"
            else:
                biomes[y][x] = "plains"
    
    return biomes

def generate_overworld(map_width, map_height, seed=None):
    if seed is not None:
        random.seed(seed)
    
    if map_width < MIN_WORLD_WIDTH or map_height < MIN_WORLD_HEIGHT:
        raise ValueError(
            f"Map must be at least "
            f"{MIN_WORLD_WIDTH}x{MIN_WORLD_HEIGHT}."
        )

    elevation = create_elevation_map(map_width, map_height)
    elevation = smooth_elevation(elevation, passes=2)

    # Add basins after smoothing so their low elevations remain visible.
    basins = []

    for _ in range(2):
        basin_x = random.randint(
            map_width // 5,
            map_width - (map_width // 5) - 1,
        )
        basin_y = random.randint(
            map_height // 4,
            map_height - (map_height // 4) - 1,
        )

        basin_radius = random.randint(4, 7)
        basin_floor = random.choice([1, 2])

        lower_basin(
            elevation,
            basin_x,
            basin_y,
            radius=basin_radius,
            floor_elevation=basin_floor,
        )

        basins.append(
            (basin_x, basin_y, basin_radius)
        )

    room = create_overworld(map_width, map_height)

    # Generate Water Features first
    ## Generate River
    river_data = carve_river(room, elevation)

    ## Stamp Lakes
    # Turn low-elevation basins into lakes.
    for basin_x, basin_y, basin_radius in basins:
        stamp_lake(
            room,
            basin_x,
            basin_y,
            radius=max(3, basin_radius - 1),
        )

    apply_mountains(room, elevation)
    apply_hills(room, elevation)
    scatter_rocks(room, elevation)

    # Put forests in by water
    for _ in range(3):
        stamp_forest_near_water(
            room,
            scale=0.01,
            clusters=2,
        )
    
    # Larger inland forest regions.
    for _ in range(3):
        forest_x = random.randint(8, map_width - 9)
        forest_y = random.randint(8, map_height - 9)
        forest_radius = random.randint(5, 9)

        stamp_forest_patch(
            room,
            forest_x,
            forest_y,
            forest_radius,
        )

    # Add open-field texture
    for _ in range(8):
        grass_x = random.randint(4, map_width - 5)
        grass_y = random.randint(4, map_height - 5)

        stamp_blob(
            room,
            grass_x,
            grass_y,
            TALL_GRASS,
            scale=0.03,
            replaceable_tiles=(FLOOR,),
        )

    biomes = create_biome_map(room, elevation)

    key_placed = stamp_building(
        room, 
        w=7, 
        h=5, 
        interior_item=KEY, 
        is_ruin=True,
        biomes=biomes
    )
    exit_placed = stamp_building(
        room, 
        w=9, 
        h=6, 
        interior_item=EXIT, 
        is_ruin=False,
        biomes=biomes
    )

    if not key_placed:
        raise RuntimeError("Could not place the key building.")

    if not exit_placed:
        raise RuntimeError("Could not place the exit building.")

    stamp_building(room, w=6, h=5, is_ruin=True, biomes=biomes)
    stamp_building(room, w=8, h=5, is_ruin=True, biomes=biomes)

    shrine = stamp_shrine(room, biomes=biomes)
    camp = stamp_abandoned_camp(room, biomes=biomes)

    if shrine is None:
        raise RuntimeError("Could not place shrine.")

    if camp is None:
        raise RuntimeError("Could not place abandoned camp.")

    player_x, player_y = find_open_floor(room)

    return room, elevation, biomes, player_x, player_y