import curses
import random

# Constants
WALL = "#"
FLOOR = "."
DOOR = "+"
KEY = "K"
EXIT = "E"
SPIKE = "^"
PLAYER ="@"
TREE = "T"
ROCK = "O"
WATER = "~"

TILE_DATA = {
    FLOOR: {"name": "Floor", "color": 1, "walkable": True},
    WALL: {"name": "Wall", "color": 1, "walkable": False},
    TREE: {"name": "Tree", "color": 2, "walkable": False},
    ROCK: {"name": "Rock", "color": 3, "walkable": False},
    WATER: {"name": "Water", "color": 6, "walkable": False},
    SPIKE: {"name": "Spikes", "color": 4, "walkable": True, "damage": 1},
    "D": {"name": "Door", "color": 3, "walkable": False, "needs_key": True},
    KEY: {"name": "Key", "color": 3, "walkable": True, "pickup": "key"},
    EXIT: {"name": "Exit", "color": 3, "walkable": True, "exit": True},
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
        for x, tile_char in enumerate(row):
            if x == player_x and y == player_y:
                stdscr.addstr(y + 2, x, "@", curses.color_pair(5))
            else:
                color_id = TILE_DATA[tile_char]["color"]
                stdscr.addstr(y + 2, x, tile_char, curses.color_pair(color_id))
  

def create_overworld(width, height):
    grid = [["." for _ in range(width)] for _ in range(height)]

    for x in range(width):
        grid[0][x] = "#"
        grid[height - 1][x] = "#"

    for y in range(height):
        grid[y][0] = "#"
        grid[y][width - 1] = "#"

    return grid

def scatter_tiles(grid, symbol, count):
    height = len(grid)
    width = len(grid[0])

    placed = 0
    while placed < count:
        rx = random.randint(2, width - 3)
        ry = random.randint(2, height - 3)

        if grid[ry][rx] == ".":
            grid[ry][rx] = symbol
            placed += 1

def stamp_forest(grid, center_x, center_y, size=25):
    height = len(grid)
    width = len(grid[0])

    fx, fy = center_x, center_y

    for _ in range(size):
        if 2 < fx < width - 3 and 2 < fy < height - 3:
            if grid[fy][fx] == FLOOR:
                grid[fy][fx] = TREE
        
        dx, dy = random.choice([(0, -1), (0, 1), (1, 0), (-1, 0)])
        fx += dx
        fy += dy

def stamp_lake(grid, center_x, center_y, size=25):
    height = len(grid)
    width = len(grid[0])

    fx, fy = center_x, center_y

    for _ in range(size):
        if 2 < fx < width - 3 and 2 < fy < height - 3:
            if grid[fy][fx] == FLOOR:
                grid[fy][fx] = WATER
        
        dx, dy = random.choice([(0, -1), (0, 1), (1, 0), (-1, 0)])
        fx += dx
        fy += dy

def main(stdscr):
    # Hide the blinking terminal cursor
    curses.curs_set(0)  
    init_colors()

    max_y, max_x = stdscr.getmaxyx()
    map_height = max_y - 4
    map_width = max_x - 1  

    room = create_overworld(map_width, map_height)

    # Stamp in forests
    for _ in range(4):
        forest_x = random.randint(5, map_width - 6)
        forest_y = random.randint(4, map_height - 5)
        stamp_forest(room, forest_x, forest_y, size=30)

    # Stamp Lakes
    for _ in range(4):
        lake_x = random.randint(5, map_width - 6)
        lake_y = random.randint(4, map_height - 5)
        stamp_lake(room, lake_x, lake_y, size=30)

    scatter_tiles(room, TREE, 4)
    scatter_tiles(room, ROCK, 10)
    scatter_tiles(room, SPIKE, 5)
    scatter_tiles(room, KEY, 1)
    scatter_tiles(room, EXIT, 1)

    player_x = map_width // 2
    player_y = map_height // 2
    room[player_y][player_x] == FLOOR

    health = 3
    has_key = False
    message = "Explore the map!"   

    while True:
        stdscr.clear()
        stdscr.addstr(0,0,f"Health: {health} | Key: {'Yes' if has_key else 'No'}")
        
        # 1. Render System draws the whole grid with colors
        draw_map(stdscr, room, player_x, player_y)

        stdscr.addstr(len(room) + 3, 0, message)
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
