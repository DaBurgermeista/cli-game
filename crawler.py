import curses

from entities import create_entity, get_entity_at
from render import draw_map, init_colors
from tiles import FLOOR, TILE_DATA
from worldgen import generate_overworld, find_open_floor
from vision import get_visible_tiles
from ui import show_text_panel

WORLD_WIDTH = 100
WORLD_HEIGHT = 60

INTRO_TITLE = "The Quiet River"
INTRO_TEXT = (
    "For three days, you have followed the river north.\n\n"
    "The water runs cold, but the banks are warm beneath your boots. "
    "No birds call from the trees, and every trail seems to lead deeper "
    "into the forest.\n\n"
    "The last settlement spoke of old shrines waking in the wilds. "
    "You came to see whether the stories were true."
)

def can_enter(tile_char, has_key):
    props = TILE_DATA[tile_char]
    if props.get("needs_key") and has_key:
        return True
    return props["walkable"]                

def get_camera(player_x, player_y, map_width, map_height, view_width, view_height):
    camera_x = player_x - (view_width // 2)
    camera_y = player_y - (view_height // 2)

    max_camera_x = max(0, map_width - view_width)
    max_camera_y = max(0, map_height - view_height)

    camera_x = max(0, min(camera_x, max_camera_x))
    camera_y = max(0, min(camera_y, max_camera_y))

    return camera_x, camera_y

def main(stdscr):
    # Hide the blinking terminal cursor
    curses.curs_set(0)  
    init_colors()
    debug_reveal_map = False

    room, player_x, player_y = generate_overworld(WORLD_WIDTH, WORLD_HEIGHT)

    explored_tiles = [
        [False for _ in range(WORLD_WIDTH)]
        for _ in range(WORLD_HEIGHT)
    ]

    occupied = {(player_x, player_y)}

    wolf_x, wolf_y = find_open_floor(room, occupied)
    occupied.add((wolf_x, wolf_y))

    deer_x, deer_y = find_open_floor(room, occupied)
    occupied.add((deer_x, deer_y))

    troll_x, troll_y = find_open_floor(room, occupied)

    health = 3
    has_key = False
    message = "Explore the map!"   

    entities = [
        create_entity("wolf", wolf_x, wolf_y),
        create_entity("deer", deer_x, deer_y),
        create_entity("troll", troll_x, troll_y),
    ]

    show_text_panel(stdscr, INTRO_TITLE, INTRO_TEXT)

    while True:

        max_y, max_x = stdscr.getmaxyx()
    
        if max_y < 10 or max_x < 20:
            stdscr.erase()
            stdscr.addstr(0, 0, "Terminal too small. Resize it to continue.")
            stdscr.refresh()
            stdscr.getch()
            continue

        view_height = max_y - 4
        view_width = max_x - 1

        camera_x, camera_y = get_camera(
            player_x,
            player_y,
            len(room[0]),
            len(room),
            view_width,
            view_height,
        )

        stdscr.erase()

        # HUD Rendering
        hud = (
            f"Health: {health} | Key: {'Yes' if has_key else 'No'} "
            f"| Pos: {player_x}, {player_y}"
        )
        stdscr.addnstr(0, 0, hud, max_x - 1)
        
        visible_tiles = get_visible_tiles(room, player_x, player_y, radius=8)

        if debug_reveal_map:
            visible_tiles = {
                (x, y)
                for y in range(len(room))
                for x in range(len(room[0]))
            }

        for x, y in visible_tiles:
            explored_tiles[y][x] = True

        # 1. Render System draws the whole grid with colors
        draw_map(stdscr, 
            room, 
            player_x, 
            player_y, 
            entities, 
            camera_x,
            camera_y,
            view_width,
            view_height,
            visible_tiles,
            explored_tiles,
        )

        message_y = max_y - 1

        stdscr.move(message_y, 0)
        stdscr.clrtoeol()
        stdscr.addnstr(message_y, 0, message, max_x - 1)

        stdscr.refresh()

        key = stdscr.getch()
        message = ""

        if key == ord("q"):
            break        
        
        if key == ord("f"):
            debug_reveal_map = not debug_reveal_map
            message = (
                "Debug map reveal enabled."
                if debug_reveal_map
                else "Debug map reveal disabled."
            )
            continue

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
            if not (0 <= next_y < len(room) and 0 <= next_x < len(room[0])):
                message = "You cannot go that way."
                continue

            target_tile = room[next_y][next_x]
            target_props = TILE_DATA[target_tile]
            target_entity = get_entity_at(entities, next_x, next_y)

            if target_entity is not None:
                message = f"A {target_entity['name']} blocks your path!"

            elif can_enter(target_tile, has_key):
                player_x, player_y = next_x, next_y
                message = target_props.get("enter_msg", "")

            else:
                message = target_props.get(
                    "bump_msg",
                    "Something blocks your way.",
                )

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
            health = max(0, health - props["damage"])
            message = f"Ouch! You took {props['damage']} damage! from a {props['name']}!"
            if health <= 0:
                break
        
        if "text" in props:
            show_text_panel(stdscr, props["name"], props["lore"])

        if props.get("exit"):
            show_text_panel(stdscr, "Victory!", "Good Job! You found the super easy to get to exit!\n")
            break

curses.wrapper(main)
