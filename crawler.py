import curses
import random

# Constants
WALL = "wall"
FLOOR = "floor"
DOOR = "door"
KEY = "key"
EXIT = "exit"
SPIKE = "spike"
PLAYER ="player"
TREE = "tree"
ROCK = "rock"
WATER = "water"
BRIDGE = "bridge"
BANK = "bank"

TILE_DATA = {
    FLOOR: {"char": ".", "name": "Floor", "color": 1, "walkable": True},
    WALL: {"char": "#", "name": "Wall", "color": 1, "walkable": False},
    TREE: {"char": "T", "name": "Tree", "color": 2, "walkable": True},
    ROCK: {"char": "O", "name": "Rock", "color": 3, "walkable": False},
    WATER: {"char": "~", "name": "Water", "color": 6, "walkable": False},
    SPIKE: {"char": "^", "name": "Spike", "color": 4, "walkable": True, "damage": 1},
    DOOR: {"char": "+", "name": "Doorway", "color": 3, "walkable": True, "needs_key": False},
    KEY: {"char": "K", "name": "Key", "color": 3, "walkable": True, "pickup": "key"},
    EXIT: {"char": "E", "name": "Exit", "color": 3, "walkable": True, "exit": True},
    BRIDGE: {"char": "=", "name": "Bridge", "color": 3, "walkable": True},
    BANK: {"char": ",", "name": "Riverbank", "color": 3, "walkable": True},
}

MAP_WIDTH = 50
MAP_HEIGHT = 22
MIN_ROOM_WIDTH = 4
MAX_ROOM_WIDTH = 6
MIN_ROOM_HEIGHT = 3
MAX_ROOM_HEIGHT = 5
# ---

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_CYAN, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)

def can_enter(tile_char, has_key):
    props = TILE_DATA[tile_char]
    if props.get("needs_key") and has_key:
        return True
    return props["walkable"]

def draw_map(stdscr, grid, player_x, player_y):
    for y, row in enumerate(grid):
        for x, tile_id in enumerate(row):
            if x == player_x and y == player_y:
                stdscr.addstr(y + 2, x, "@", curses.color_pair(5))
            else:
                props = TILE_DATA[tile_id]
                color_id = TILE_DATA[tile_id]["color"]
                attr = curses.color_pair(color_id)
                if tile_id == FLOOR:
                    attr |= curses.A_DIM
                stdscr.addstr(y + 2, x, props["char"], attr)
  

def create_overworld(width, height):
    grid = [[FLOOR for _ in range(width)] for _ in range(height)]

    for x in range(width):
        grid[0][x] = WALL
        grid[height - 1][x] = WALL

    for y in range(height):
        grid[y][0] = WALL
        grid[y][width - 1] = WALL

    return grid

def scatter_tiles(grid, symbol, count):
    height = len(grid)
    width = len(grid[0])

    placed = 0
    while placed < count:
        rx = random.randint(2, width - 3)
        ry = random.randint(2, height - 3)

        if grid[ry][rx] == FLOOR:
            grid[ry][rx] = symbol
            placed += 1

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
    width = len(grid)

    # Try 50 times to find a dry, open spot on map
    for _ in range(50):
        x1 = random.randint(3, width - w - 4)
        y1 = random.randint(3, height - h - 4)

        # Check footprint
        spot_clear = True
        for y in range(y1 - 1, y1 + h + 1):
            for x in range(x1 - 1, x1 - w + 1):
                if grid[y][x] in (WATER, BRIDGE, WALL, DOOR, KEY, EXIT):
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
                    

def main(stdscr):
    # Hide the blinking terminal cursor
    curses.curs_set(0)  
    init_colors()

    max_y, max_x = stdscr.getmaxyx()
    map_height = max_y - 4
    map_width = max_x - 1  

    room = create_overworld(map_width, map_height)

    total_tiles = map_width * map_height

    # Generate Water Features first
    ## Generate River
    carve_river(room)

    ## Stamp Lakes
    for _ in range(3):
        lake_x = random.randint(5, map_width - 6)
        lake_y = random.randint(4, map_height - 5)
        stamp_blob(room, lake_x, lake_y, WATER, scale=0.04)

    # Put forests in by water
    for _ in range(4):
        stamp_forest_near_water(room, scale=0.05)

    scatter_tiles(room, TREE, 4)

    stamp_building(room, w=7, h=5, interior_item=KEY, is_ruin=False)
    stamp_building(room, w=9, h=6, interior_item=EXIT, is_ruin=True)

    stamp_building(room, w=6, h=5, is_ruin=True)
    stamp_building(room, w=8, h=5, is_ruin=True)
    
    """ --- Was for testing purposes
    scatter_tiles(room, ROCK, total_tiles // 150)
    scatter_tiles(room, SPIKE, total_tiles // 250)
    """
    scatter_tiles(room, KEY, 1)
    scatter_tiles(room, EXIT, 1)

    player_x = map_width // 2
    player_y = map_height // 2
    room[player_y][player_x] == FLOOR

    health = 3
    has_key = False
    message = "Explore the map!"   

    while True:
        stdscr.erase()
        stdscr.addstr(0,0,f"Health: {health} | Key: {'Yes' if has_key else 'No'}")
        
        # 1. Render System draws the whole grid with colors
        draw_map(stdscr, room, player_x, player_y)

        stdscr.addstr(len(room) + 3, 0, message)
        stdscr.clrtoeol()
        stdscr.refresh()

        key = stdscr.getch()
        message = ""

        if key == ord("q"):
            break        
        
        next_x, next_y = player_x, player_y

        if key in (ord("w"), curses.KEY_UP):
            next_y -= 1
        elif key in (ord("s"), curses.KEY_DOWN):
            next_y += 1
        elif key in (ord("a"), curses.KEY_LEFT):
            next_x -= 1
        elif key in (ord("d"), curses.KEY_RIGHT):
            next_x += 1

        # 3. Movement System checks TILE_DATA
        if can_enter(room[next_y][next_x], has_key):
            player_x, player_y = next_x, next_y

        # 4. Interaction System reads flags from TILE_DATA
        current_tile = room[player_y][player_x]
        props = TILE_DATA[current_tile]
        
        if props.get("pickup")  == "key":
            message = "You found a key"
            has_key = True
            room[player_y][player_x] = FLOOR
        
        if props.get("need_key"):
            room[player_y][player_x] = FLOOR
            message = "You unlocked the door!"
        
        if "damage" in props:
            health -= props["damage"]
            message = f"Ouch! You took {props['damage']} damage! from a {props['name']}!"
            if health <= 0:
                break

        if props.get("exit"):
            break

curses.wrapper(main)
