import curses
import random
from tiles import TILE_DATA, FLOOR, KEY, EXIT, PLAYER
from worldgen import (
    create_overworld,
    carve_river,
    stamp_blob,
    stamp_forest_near_water,
    stamp_building,
)
from render import init_colors, draw_map

MAP_WIDTH = 50
MAP_HEIGHT = 22
MIN_ROOM_WIDTH = 4
MAX_ROOM_WIDTH = 6
MIN_ROOM_HEIGHT = 3
MAX_ROOM_HEIGHT = 5
# ---

def can_enter(tile_char, has_key):
    props = TILE_DATA[tile_char]
    if props.get("needs_key") and has_key:
        return True
    return props["walkable"]

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
