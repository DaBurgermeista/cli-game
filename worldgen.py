import random
from tiles import (
    WALL,
    FLOOR,
    DOOR,
    KEY,
    EXIT,
    SPIKE,
    TREE,
    ROCK,
    WATER,
    BRIDGE,
    BANK,
)

def create_overworld(width, height):
    grid = [[FLOOR for _ in range(width)] for _ in range(height)]

    for x in range(width):
        grid[0][x] = WALL
        grid[height - 1][x] = WALL

    for y in range(height):
        grid[y][0] = WALL
        grid[y][width - 1] = WALL

    return grid

def stamp_blob(grid, center_x, center_y, tile_type, scale=0.04):
    height = len(grid)
    width = len(grid[0])

    # Calculate steps based on total map area
    steps = int((width * height) * scale)

    fx, fy = center_x, center_y

    for _ in range(steps):
        if 2 < fx < width - 3 and 2 < fy < height - 3:
            if grid[fy][fx] in (FLOOR, BANK):
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

        """ Build a walkable bridge halfway across
        if ry == bridge_y or ry == bridge_y + 1:
            grid[ry][rx] = BRIDGE
            if rx + 1 < width - 1:
                grid[ry][rx + 1] = BRIDGE
        else:
            grid[ry][rx] = WATER
            if rx + 1 < width - 1:
                grid[ry][rx + 1] = WATER
        """

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