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
            # Only elevation 7 floors become hills
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

def carve_river(grid):
    height = len(grid)
    width = len(grid[0])

    # Start somewhere near the middle-ish of the top border
    rx = random.randint(width // 4, (width * 3) // 4)
    bridge_y = height // 2

    drift = random.choice([-1, 1])
    bend_timer = random.randint(4, 8)
    river_width = 2

    # Go from top border (y=1) to bottom border (height - 2)
    for ry in range(1, height - 1):
        left_bank = rx - 1
        right_bank =  rx + river_width
        if 1 < left_bank < width - 2 and grid[ry][left_bank] == FLOOR:
            grid[ry][left_bank] = BANK
        if 1 < right_bank < width - 2 and grid[ry][right_bank] == FLOOR:
            grid[ry][right_bank] = BANK

        for offset in range(river_width):
            curr_x = rx + offset
            if 1 < curr_x < width - 2:
                if ry == bridge_y or ry == bridge_y + 1:
                    grid[ry][curr_x] = BRIDGE
                else:
                    grid[ry][curr_x] = WATER

        # Handle momentum so the river makes wide, natural S-curves
        bend_timer -= 1
        if bend_timer <= 0:
            drift = random.choice([-1, 0, 1])
            bend_timer = random.randint(4, 8)

        # Occasionally widen or narrow the channel
        if random.random() < 0.25:
            river_width = max(2, min(4, river_width + random.choice([-1, 1])))

        # Move horizontally by 1 or 2 in current drift direction
        step = drift * random.choice([1, 1, 2])
        rx = max(3, min(width - river_width - 3, rx + step))

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

    room = create_overworld(map_width, map_height)

    # Generate Water Features first
    ## Generate River
    carve_river(room)

    ## Stamp Lakes
    for _ in range(3):
        lake_x = random.randint(5, map_width - 6)
        lake_y = random.randint(4, map_height - 5)
        stamp_blob(room, lake_x, lake_y, WATER, scale=0.04)

    apply_mountains(room, elevation)
    apply_hills(room, elevation)
    scatter_rocks(room, elevation)

    # Put forests in by water
    for _ in range(4):
        stamp_forest_near_water(
            room,
            scale=0.01,
            clusters=2,
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