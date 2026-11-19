import curses

from entities import (
    create_player,
    get_entity_at,
    spawn_random_entities,
    attack_entity,
    update_entities,
)
from items import spawn_random_items, get_item_at, format_inventory, use_item
from render import draw_map, init_colors, draw_message_log
from tiles import FLOOR, TILE_DATA, get_walkable_tiles
from worldgen import generate_overworld
from vision import get_visible_tiles
from ui import show_text_panel, show_inventory_panel, render_sidebar
from main_menu import show_main_menu

WORLD_WIDTH = 100
WORLD_HEIGHT = 60

MAP_TOP = 2
MESSAGE_LOG_HEIGHT = 5
MAX_MESSAGES = MESSAGE_LOG_HEIGHT - 1
SIDEBAR_WIDTH = 30
MIN_MAP_WIDTH = 20
MIN_MAP_HEIGHT = 10

INTRO_TITLE = "The Quiet River"
INTRO_TEXT = (
    "You have entered a wilderness few travelers cross willingly.\n\n"
    "Somewhere beyond these woods, the Quiet River has changed its course. "
    "Settlements on its banks speak of unfamiliar ruins, abandoned camps, "
    "and old shrines standing where no shrine should be.\n\n"
    "You came to see what the land is becoming."
)


def add_message(messages, text):
    if not text:
        return

    messages.append(text)
    if len(messages) > MAX_MESSAGES:
        messages.pop(0)


def can_enter(tile_char, has_key):
    props = TILE_DATA[tile_char]
    return props["walkable"] or (props.get("needs_key", False) and has_key)


def get_camera(player_x, player_y, map_width, map_height, view_width, view_height):
    camera_x = player_x - (view_width // 2)
    camera_y = player_y - (view_height // 2)

    max_camera_x = max(0, map_width - view_width)
    max_camera_y = max(0, map_height - view_height)

    camera_x = max(0, min(camera_x, max_camera_x))
    camera_y = max(0, min(camera_y, max_camera_y))

    return camera_x, camera_y


def all_map_tiles(room):
    return {
        (x, y)
        for y in range(len(room))
        for x in range(len(room[0]))
    }


def main(stdscr):
    curses.curs_set(0)
    init_colors()

    debug_reveal_map = False
    debug_elevation = False
    while True:
        # Shows main menu on launch
        menu_choice = show_main_menu(stdscr)

        if menu_choice == "Quit":
            return
        
        if menu_choice == "Credits":
            show_text_panel(
                stdscr,
                "Credits",
                "Created by DaBurgermeista",
            )
            continue
        
        if menu_choice == "Options":
            # TODO(#1): Create options menu
            show_text_panel(
                stdscr,
                "Options",
                "Options are not implemented yet.",
            )
            continue
        
        if menu_choice == "New Game":
            break

    # Begins world generation
    room, elevation, biomes, player_x, player_y = generate_overworld(
        WORLD_WIDTH,
        WORLD_HEIGHT,
    )

    explored_tiles = [
        [False for _ in range(WORLD_WIDTH)]
        for _ in range(WORLD_HEIGHT)
    ]

    walkable_tiles = get_walkable_tiles(room, exclude={(player_x, player_y)})
    entities = spawn_random_entities(room, biomes, walkable_tiles, count=15)

    occupied_by_entities = {(player_x, player_y)} | {
        (entity["x"], entity["y"]) for entity in entities
    }
    item_tiles = get_walkable_tiles(room, exclude=occupied_by_entities)
    items = spawn_random_items(room, biomes, item_tiles, count=12)

    player = create_player(player_x, player_y)
    messages = ["Explore the wilderness."]

    show_text_panel(stdscr, INTRO_TITLE, INTRO_TEXT)

    while True:
        took_turn = False
        max_y, max_x = stdscr.getmaxyx()

        if (
            max_y < MAP_TOP + MESSAGE_LOG_HEIGHT + MIN_MAP_HEIGHT
            or max_x < SIDEBAR_WIDTH + MIN_MAP_WIDTH
        ):
            stdscr.erase()
            stdscr.addstr(0, 0, "Terminal too small. Resize it to continue.")
            stdscr.refresh()
            stdscr.getch()
            continue

        view_height = max_y - MAP_TOP - MESSAGE_LOG_HEIGHT
        view_width = max_x - SIDEBAR_WIDTH
        sidebar_x = view_width

        camera_x, camera_y = get_camera(
            player_x,
            player_y,
            len(room[0]),
            len(room),
            view_width,
            view_height,
        )

        stdscr.erase()

        natural_visible_tiles = get_visible_tiles(
            room,
            player_x,
            player_y,
            radius=8,
        )

        for x, y in natural_visible_tiles:
            explored_tiles[y][x] = True

        if debug_reveal_map or debug_elevation:
            display_visible_tiles = all_map_tiles(room)
        else:
            display_visible_tiles = natural_visible_tiles

        visible_entities = [
            entity
            for entity in entities
            if (entity["x"], entity["y"]) in display_visible_tiles
            and entity["hp"] > 0
        ]

        hud = (
            f"Health: {player['hp']}/{player['max_hp']} | "
            f"Key: {'Yes' if player['has_key'] else 'No'} | "
            f"Pos: {player_x}, {player_y} | "
            f"Biome: {biomes[player_y][player_x].title()}"
        )
        if debug_elevation:
            hud += " | Elevation: On"
        stdscr.addnstr(0, 0, hud, max_x - 1)

        draw_map(
            stdscr,
            room,
            player_x,
            player_y,
            entities,
            items,
            camera_x,
            camera_y,
            view_width,
            view_height,
            display_visible_tiles,
            explored_tiles,
            elevation=elevation,
            show_elevation=debug_elevation,
        )

        log_y = MAP_TOP + view_height
        draw_message_log(
            stdscr,
            messages,
            log_y,
            view_width,
            MESSAGE_LOG_HEIGHT,
        )

        render_sidebar(
            stdscr,
            player,
            biomes[player["y"]][player["x"]],
            visible_entities,
            start_x=sidebar_x,
            panel_width=SIDEBAR_WIDTH,
        )

        stdscr.refresh()
        key = stdscr.getch()

        if key == ord("q"):
            break

        if key == ord("f"):
            debug_reveal_map = not debug_reveal_map
            add_message(
                messages,
                "Debug map reveal enabled."
                if debug_reveal_map
                else "Debug map reveal disabled.",
            )
            continue

        if key == ord("e"):
            debug_elevation = not debug_elevation
            add_message(
                messages,
                "Elevation debug view enabled."
                if debug_elevation
                else "Elevation debug view disabled.",
            )
            continue

        if key == ord("i"):
            if not player["inventory"]:
                show_text_panel(stdscr, "Inventory", "Your pack is empty.")
            else:
                choice = show_inventory_panel(
                    stdscr,
                    "Inventory",
                    format_inventory(player),
                )
                message = use_item(player, choice)
                if message:
                    add_message(messages, message)
                    # Using an item consumes a turn; browsing or cancelling does not.
                    took_turn = True
            if not took_turn:
                continue

        next_x, next_y = player_x, player_y

        if key == ord("g"):
            item = get_item_at(items, player_x, player_y)
            if item is None:
                add_message(messages, "There is nothing here to pick up.")
            else:
                items.remove(item)
                player["inventory"].append(item)
                add_message(messages, f"You pick up the {item['name']}.")
            took_turn = True

        elif key in (ord("w"), curses.KEY_UP):
            next_y -= 1
            took_turn = True
        elif key in (ord("s"), curses.KEY_DOWN):
            next_y += 1
            took_turn = True
        elif key in (ord("a"), curses.KEY_LEFT):
            next_x -= 1
            took_turn = True
        elif key in (ord("d"), curses.KEY_RIGHT):
            next_x += 1
            took_turn = True
        elif key != ord("i"):
            # Ignore unrecognized input without advancing the game state.
            continue

        if (next_x, next_y) != (player_x, player_y):
            if not (0 <= next_y < len(room) and 0 <= next_x < len(room[0])):
                # Attempted movement consumes a turn, just like bumping a wall.
                add_message(messages, "You cannot go that way.")
            else:
                target_tile = room[next_y][next_x]
                target_props = TILE_DATA[target_tile]
                target_entity = get_entity_at(entities, next_x, next_y)

                if target_entity is not None:
                    add_message(messages, attack_entity(player, target_entity))
                    if target_entity["hp"] <= 0:
                        entities.remove(target_entity)

                elif can_enter(target_tile, player["has_key"]):
                    player_x, player_y = next_x, next_y
                    player["x"], player["y"] = player_x, player_y

                    if target_props.get("needs_key"):
                        room[player_y][player_x] = FLOOR
                        add_message(messages, "You unlocked the door!")
                    else:
                        add_message(messages, target_props.get("enter_msg", ""))

                else:
                    add_message(
                        messages,
                        target_props.get("bump_msg", "Something blocks your way."),
                    )

        if not took_turn:
            continue

        current_tile = room[player_y][player_x]
        props = TILE_DATA[current_tile]
        ground_item = get_item_at(items, player_x, player_y)

        if ground_item is not None:
            add_message(messages, f"You see a {ground_item['name']} here.")

        if props.get("pickup") == "key":
            add_message(messages, "You found a key.")
            player["has_key"] = True
            room[player_y][player_x] = FLOOR
            props = TILE_DATA[FLOOR]

        if "damage" in props:
            player["hp"] = max(0, player["hp"] - props["damage"])
            add_message(
                messages,
                f"Ouch! You took {props['damage']} damage from {props['name']}!",
            )
            if player["hp"] <= 0:
                show_text_panel(stdscr, "Defeated!", "You died.")
                break

        if props.get("exit"):
            show_text_panel(
                stdscr,
                "Victory!",
                "Good job! You found the exit!\n",
            )
            break

        if "text" in props:
            show_text_panel(stdscr, props["name"], props["text"])

        for message in update_entities(entities, room, player):
            add_message(messages, message)

        if player["hp"] <= 0:
            show_text_panel(stdscr, "Defeated!", "You died.")
            break


curses.wrapper(main)