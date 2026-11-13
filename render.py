import curses
from tiles import TILE_DATA, FLOOR, PLAYER

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_CYAN, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)

def draw_map(stdscr, grid, player_x, player_y, entities):
    # Draw terrain grid first
    for y, row in enumerate(grid):
        for x, tile_id in enumerate(row):
            props = TILE_DATA[tile_id]
            color_id = TILE_DATA[tile_id]["color"]
            attr = curses.color_pair(color_id)
            if tile_id == FLOOR:
                attr |= curses.A_DIM
            stdscr.addstr(y + 2, x, props["char"], attr)

    # Draw all monsters
    for entity in entities:
        attr = curses.color_pair(entity["color"])
        stdscr.addstr(entity["y"] + 2, entity["x"], entity["char"], attr)

    # Add player last
    stdscr.addstr(player_y + 2, player_x, "@", curses.color_pair(5))