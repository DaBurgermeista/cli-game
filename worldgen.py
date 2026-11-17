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
)

BASE_ELEVATION = 3
MAX_ELEVATION = 9

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
    for _ in range(8):
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

def apply_mountains(grid, elevation, mountain_height=8):
    height = len(grid)
    width = len(grid[0])

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            # Only high elevation floors become mountains
            if elevation[y][x] >= mountain_height and grid[y][x] == FLOOR:
                grid[y][x] = MOUNTAIN

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

def stamp_forest_near_water(grid, scale=0.05):
    water_tiles = []

    # Find every water tile on the map
    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile == WATER:
                water_tiles.append((x, y))

    # Pick a random water tile and start a tree blob
    if water_tiles:
        wx, wy = random.choice(water_tiles)
        stamp_blob(grid, wx, wy, TREE, scale=scale)

def stamp_building(grid, w=7, h=5, interior_item=None, is_ruin=False):
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

            return True # Successfully places
    return False # Could not place

def stamp_shrine(grid):
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

        return {
            "kind": "shrine",
            "x": center_x,
            "y": center_y,
        }

    return None

def stamp_abandoned_camp(grid):
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

def generate_overworld(map_width, map_height):
    elevation = create_elevation_map(map_width, map_height)
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

    # Put forests in by water
    for _ in range(4):
        stamp_forest_near_water(room, scale=0.05)

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

    key_placed = stamp_building(
        room, 
        w=7, 
        h=5, 
        interior_item=KEY, 
        is_ruin=True,
    )
    exit_placed = stamp_building(
        room, 
        w=9, 
        h=6, 
        interior_item=EXIT, 
        is_ruin=False,
    )

    if not key_placed:
        raise RuntimeError("Could not place the key building.")

    if not exit_placed:
        raise RuntimeError("Could not place the exit building.")

    stamp_building(room, w=6, h=5, is_ruin=True)
    stamp_building(room, w=8, h=5, is_ruin=True)

    shrine = stamp_shrine(room)
    camp = stamp_abandoned_camp(room)

    if shrine is None:
        raise RuntimeError("Could not place shrine.")

    if camp is None:
        raise RuntimeError("Could not place abandoned camp.")

    player_x, player_y = find_open_floor(room)

    return room, elevation, player_x, player_y