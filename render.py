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

    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_CYAN, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)

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

def draw_map(
    stdscr,
    grid,
    player_x,
    player_y,
    entities,
    camera_x,
    camera_y,
    view_width,
    view_height,
    visible_tiles,
    explored_tiles,
):
    # Draw only the current camera viewport.
    for screen_y in range(view_height):
        world_y = camera_y + screen_y

        for screen_x in range(view_width):
            world_x = camera_x + screen_x

            # Defensive check in case viewport and map sizes differ.
            if world_y >= len(grid) or world_x >= len(grid[0]):
                continue

            # Never seen: leave the tile blank.
            if not explored_tiles[world_y][world_x]:
                safe_addch(stdscr, screen_y + 2, screen_x, " ")
                continue

            tile_id = grid[world_y][world_x]
            props = TILE_DATA[tile_id]

            is_visible = (world_x, world_y) in visible_tiles

            attr = curses.color_pair(props["color"])

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

    # Draw entities only if they are currently visible and on-screen.
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