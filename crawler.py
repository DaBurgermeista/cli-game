"""Curses front end for selecting a world and playing a turn-based run."""

import curses

from render import draw_map, init_colors, draw_message_log
from vision import get_visible_tiles
from ui import show_text_panel, show_inventory_panel, render_sidebar
from main_menu import show_main_menu
from game_state import create_game_state
from game_actions import ActionType, GameAction, apply_action
from world_profiles import WORLD_PROFILES

MAP_TOP = 2
MESSAGE_LOG_HEIGHT = 5
MAX_MESSAGES = MESSAGE_LOG_HEIGHT - 1
SIDEBAR_WIDTH = 30
MIN_MAP_WIDTH = 20
MIN_MAP_HEIGHT = 10

def add_message(messages, text):
    """Add a UI-only message and keep the same short history as the game log."""
    if not text:
        return

    messages.append(text)
    if len(messages) > MAX_MESSAGES:
        messages.pop(0)


def get_camera(player_x, player_y, map_width, map_height, view_width, view_height):
    """Center the viewport on the player, clamped to the map edges."""
    camera_x = player_x - (view_width // 2)
    camera_y = player_y - (view_height // 2)

    max_camera_x = max(0, map_width - view_width)
    max_camera_y = max(0, map_height - view_height)

    camera_x = max(0, min(camera_x, max_camera_x))
    camera_y = max(0, min(camera_y, max_camera_y))

    return camera_x, camera_y


def all_map_tiles(room):
    """Return every coordinate, used by the map-reveal debug modes."""
    return {
        (x, y)
        for y in range(len(room))
        for x in range(len(room[0]))
    }


def main(stdscr):
    """Run the menu, initialize the selected world, and handle screen input."""
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
        
        # World modes are data-driven; options and credits stay in this menu.
        if menu_choice in WORLD_PROFILES:
            break

    # The profile chooses map generation and flavor text; the state factory
    # handles shared player/entity/item setup for every mode.
    profile = WORLD_PROFILES[menu_choice]

    # Floor progression: the overworld is a single run, but a dungeon run
    # descends. Each stairwell victory generates the next floor and carries
    # Carl (HP, pack, equipment, gold) with it.
    descends = menu_choice == "Floor 1"
    floor_number = 1
    carried_player = None
    while True:
        if floor_number == 1:
            intro_title = profile.title
            intro_text = profile.intro
            starting_message = profile.starting_message
            location_name = profile.title
        else:
            intro_title = f"Floor {floor_number}"
            intro_text = (
                f"Welcome to Floor {floor_number}, Crawler. The dungeon "
                "gets deeper, and the bosses get bigger."
            )
            starting_message = f"You descend to Floor {floor_number}."
            location_name = f"Floor {floor_number}"

        game = create_game_state(
            profile.width,
            profile.height,
            world_generator=profile.generator,
            area_label=profile.area_label,
            location_name=location_name,
            intro_title=intro_title,
            intro_text=intro_text,
            starting_message=starting_message,
            floor_number=floor_number,
            player=carried_player,
        )
        # Local aliases make the rendering calls easier to read. Mutable values
        # still refer to the same objects held by GameState.
        room = game.grid
        elevation = game.elevation
        biomes = game.regions
        player = game.player
        entities = game.entities
        items = game.items
        explored_tiles = game.explored
        messages = game.messages

        display_intro = game.intro_text
        if game.boss is not None:
            display_intro += (
                f"\n\nBorant AI: \"{game.boss['name']} guards the "
                "stairwell. Defeat the boss to descend.\""
            )
        show_text_panel(stdscr, game.intro_title, display_intro)
        outcome = None

        while True:
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
                player["x"],
                player["y"],
                len(room[0]),
                len(room),
                view_width,
                view_height,
            )

            stdscr.erase()

            # Fog-of-war visibility is recalculated from the current player tile.
            natural_visible_tiles = get_visible_tiles(
                room,
                player["x"],
                player["y"],
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
                f"{game.location_name} | "
                f"Health: {player['hp']}/{player['max_hp']} | "
                f"Key: {'Yes' if player['has_key'] else 'No'} | "
                f"Pos: {player['x']}, {player['y']} | "
                f"{game.area_label}: {biomes[player['y']][player['x']].title()}"
            )
            if debug_elevation:
                hud += " | Elevation: On"
            stdscr.addnstr(0, 0, hud, max_x - 1)

            draw_map(
                stdscr,
                room,
                player["x"],
                player["y"],
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
                area_label=game.area_label,
            )

            stdscr.refresh()
            key = stdscr.getch()

            if key == ord("q"):
                outcome = "quit"
                break

            # These keys only change the display, so they do not advance a turn.
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

            # Inventory browsing is UI work. Only a selected item becomes an
            # action; cancelling the panel leaves the world untouched.
            if key == ord("i"):
                if not player["inventory"]:
                    show_text_panel(stdscr, "Inventory", "Your pack is empty.")
                    continue
                choice = show_inventory_panel(stdscr, "Inventory", player)
                if choice is None:
                    continue
                verb, item_index = choice
                if verb == "use":
                    action = GameAction(ActionType.USE_ITEM, item_index=item_index)
                else:
                    action = GameAction(ActionType.DROP_ITEM, item_index=item_index)
            # H is a quick heal: drink the first healing item without opening
            # the panel. It costs a turn, like using it from the panel.
            elif key == ord("h"):
                heal_index = next(
                    (
                        idx
                        for idx, item in enumerate(player["inventory"])
                        if item["type"] == "heal"
                    ),
                    None,
                )
                if heal_index is None:
                    add_message(messages, "You have no healing items.")
                    continue
                if player["hp"] >= player["max_hp"]:
                    add_message(messages, "You are already at full health.")
                    continue
                action = GameAction(ActionType.USE_ITEM, item_index=heal_index)
            # Convert terminal keys into game-level actions. The rules module
            # handles movement, combat, pickup, effects, and enemy turns.
            elif key in (ord("w"), curses.KEY_UP):
                action = GameAction(ActionType.MOVE, dy=-1)
            elif key in (ord("s"), curses.KEY_DOWN):
                action = GameAction(ActionType.MOVE, dy=1)
            elif key in (ord("a"), curses.KEY_LEFT):
                action = GameAction(ActionType.MOVE, dx=-1)
            elif key in (ord("d"), curses.KEY_RIGHT):
                action = GameAction(ActionType.MOVE, dx=1)
            elif key == ord("g"):
                action = GameAction(ActionType.PICK_UP)
            elif key == ord("."):
                action = GameAction(ActionType.WAIT)
            else:
                # Ignore unrecognized input without advancing the game state.
                continue

            result = apply_action(game, action, message_limit=MAX_MESSAGES)
            # The action layer reports semantic discoveries/outcomes; curses is
            # responsible only for presenting the corresponding panels.
            for title, text in result.discoveries:
                show_text_panel(stdscr, title, text)

            if result.outcome == "defeat":
                show_text_panel(stdscr, "Defeated!", "You died. The dungeon claims another crawler.")
                outcome = "defeat"
                break
            if result.outcome == "victory":
                if descends:
                    show_text_panel(
                        stdscr,
                        "Victory!",
                        "Floor cleared! You descend to the next floor.",
                    )
                else:
                    show_text_panel(
                        stdscr,
                        "Victory!",
                        "Floor cleared! You found the stairwell!\n",
                    )
                outcome = "victory"
                break

        # A stairwell victory on a dungeon run descends; anything else
            # (quit, defeat, or an overworld victory) ends the run.
        if outcome != "victory" or not descends:
            return
        floor_number += 1
        carried_player = game.player


curses.wrapper(main)
