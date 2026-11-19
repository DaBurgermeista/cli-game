import curses

from tiles import FLOOR, TILE_DATA


def safe_addch(stdscr, y, x, char, attr=0):
    max_y, max_x = stdscr.getmaxyx()

    # Do not write to the terminal's final column. Curses can error there.
    if 0 <= y < max_y and 0 <= x < max_x - 1:
        stdscr.addch(y, x, char, attr)


def init_colors():
    curses.start_color()
    curses.use_default_colors()

    # Existing general-purpose foreground colors.
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_CYAN, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)

    # Terrain-specific background pairs.
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Water
    curses.init_pair(8, curses.COLOR_CYAN, curses.COLOR_BLUE)     # Deep water / basin
    curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Dry hills
    curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_RED)    # Hazard / warning

def draw_message_log(stdscr, messages, start_y, width, height):
    # Clear every row belonging to the message area. 
    for row in range(height):
        stdscr.move(start_y + row, 0)
        stdscr.clrtoeol()

    # Draw a divider above the messages
    stdscr.addnstr(
        start_y,
        0,
        "-" * (width - 1),
        width - 1,
        curses.A_DIM,
    )

    available_rows = height - 1

    recent_messages = messages[-available_rows:]

    first_message_y = start_y + 1 + (available_rows - len(recent_messages))

    for index, text in enumerate(recent_messages):
        stdscr.addnstr(
            first_message_y + index,
            0,
            text,
            width - 1,
        )

def get_elevation_attr(value):
    if value <= 2:
        return curses.color_pair(6)  # Blue: basin / lake level

    if value <= 4:
        return curses.color_pair(2)  # Green: lowland

    if value <= 6:
        return curses.color_pair(3)  # Yellow: hills

    if value <= 7:
        return curses.color_pair(4)  # Red: high hills

    return curses.color_pair(1)      # White: mountain peaks

def draw_map(
    stdscr,
    grid,
    player_x,
    player_y,
    entities,
    items,
    camera_x,
    camera_y,
    view_width,
    view_height,
    visible_tiles,
    explored_tiles,
    elevation=None,
    show_elevation=False,
):
    # Draw only the current camera viewport.
    for screen_y in range(view_height):
        world_y = camera_y + screen_y

        for screen_x in range(view_width):
            world_x = camera_x + screen_x

            # Defensive check in case viewport and map sizes differ.
            if world_y >= len(grid) or world_x >= len(grid[0]):
                continue

            is_visible = (world_x, world_y) in visible_tiles

            # Hide a tile only when it has never been explored AND is not currently displayed.
            if not show_elevation and not explored_tiles[world_y][world_x] and not is_visible:
                safe_addch(stdscr, screen_y + 2, screen_x, " ")
                continue

            # Elevation debug mode replaces terrain with elevation digits.
            if show_elevation and elevation is not None:
                elevation_value = elevation[world_y][world_x]
                display_value = round(elevation_value)

                safe_addch(
                    stdscr,
                    screen_y + 2,
                    screen_x,
                    str(display_value),
                    get_elevation_attr(elevation_value),
                )

                continue

            tile_id = grid[world_y][world_x]
            props = TILE_DATA[tile_id]

            attr = curses.color_pair(props["color"])

            # Hills use the same highlands color as mountains,
            # but appear subdued to show lower elevation.
            if tile_id == HILL:
                attr |= curses.A_DIM

            # Previously explored tiles remain visible but dim.
            if not is_visible:
                attr |= curses.A_DIM

            # Floor is always slightly dimmer than special terrain.
            if tile_id == FLOOR:
                attr |= curses.A_DIM

            safe_addch(
                stdscr,
                screen_y + 2,
                screen_x,
                props["char"],
                attr,
            )
    
    # Draw entities and items only if they are currently visible and on-screen.
    if not show_elevation:
        for item in items:
            if (item["x"], item["y"]) not in visible_tiles:
                continue

            screen_x = item["x"] - camera_x
            screen_y = item["y"] - camera_y

            if 0 <= screen_x < view_width and 0 <= screen_y < view_height:
                safe_addch(
                    stdscr,
                    screen_y + 2,
                    screen_x,
                    item["char"],
                    curses.color_pair(item["color"]),
                )

        for entity in entities:
            if (entity["x"], entity["y"]) not in visible_tiles:
                continue

            screen_x = entity["x"] - camera_x
            screen_y = entity["y"] - camera_y

            if 0 <= screen_x < view_width and 0 <= screen_y < view_height:
                safe_addch(
                    stdscr,
                    screen_y + 2,
                    screen_x,
                    entity["char"],
                    curses.color_pair(entity["color"]),
                )

    # Draw player last, ensuring the player appears over terrain/entities.
    player_screen_x = player_x - camera_x
    player_screen_y = player_y - camera_y

    if 0 <= player_screen_x < view_width and 0 <= player_screen_y < view_height:
        safe_addch(
            stdscr,
            player_screen_y + 2,
            player_screen_x,
            "@",
            curses.color_pair(5) | curses.A_BOLD,
        )