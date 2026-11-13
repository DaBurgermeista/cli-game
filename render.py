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