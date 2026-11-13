import curses
from tiles import TILE_DATA, FLOOR, KEY, EXIT, PLAYER
from worldgen import (
    create_overworld,
    carve_river,
    stamp_blob,
    stamp_forest_near_water,
    stamp_building,
    generate_overworld
)
from render import init_colors, draw_map
from entities import create_entity, get_entity_at

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

def main(stdscr):
    # Hide the blinking terminal cursor
    curses.curs_set(0)  
    init_colors()

    max_y, max_x = stdscr.getmaxyx()
    map_height = max_y - 4
    map_width = max_x - 1  

    room, player_x, player_y = generate_overworld(map_width, map_height)

    health = 3
    has_key = False
    message = "Explore the map!"   

    entities = [
        create_entity("wolf", player_x + 4, player_y)
        create_entity("deer", player_x - 4, player_y - 2)
        create_entity("troll", player_x + 6, player_y + 3)
    ]

    while True:
        stdscr.erase()
        stdscr.addstr(0,0,f"Health: {health} | Key: {'Yes' if has_key else 'No'}")
        
        # 1. Render System draws the whole grid with colors
        draw_map(stdscr, room, player_x, player_y, entities)

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
        if (next_x, next_y) != (player_x, player_y):
            target_tile = room[next_y][next_x]
            target_props = TILE_DATA[target_tile]

            if can_enter(target_tile, has_key):
                player_x, player_y = next_x, next_y
                message = target_props.get("enter_msg", "")
            else:
                message = target_props.get("bump_msg", "Something blocks your way.")

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
