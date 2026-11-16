import curses
from tiles import TILE_DATA, FLOOR

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_CYAN, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)

def draw_map(stdscr, grid, player_x, player_y, entities, camera_x, camera_y, view_width, view_height, visible_tiles, explore_tiles,):
    # Draw terrain grid first
    for screen_y in range(view_height):
        world_y = camera_y + screen_y

    for screen_x in range(view_width):
        world_x = camera_x + screen_x

        if world_y >= len(grid) or world_x >= len(grid[0]):
            continue

        tile_id = grid[world_y][world_x]
        props = TILE_DATA[tile_id]

        if not explored_tiles[world_y, world_x]:
            stdscr.addstr(screen_y + 2, screen_x, " ")
        
        is_visible =  (world_x, world_y) in visible_tiles

        attr = curses.color_pair(props["color"])
        if not is_visible:
            attr |= curses.A_DIM


        stdscr.addstr(
            screen_y + 2,
            screen_x,
            props["char"],
            attr,
        )

    map_height = len(grid)
    map_width = len(grid[0]) if grid else 0

    # Draw entities
    for entity in entities:
    if (entity["x"], entity["y"]) not in visible_tiles:
        continue

    screen_x = entity["x"] - camera_x
    screen_y = entity["y"] - camera_y

    if 0 <= screen_x < view_width and 0 <= screen_y < view_height:
        stdscr.addstr(
            screen_y + 2,
            screen_x,
            entity["char"],
            curses.color_pair(entity["color"]),
        )

    # Add player last
    stdscr.addstr(
        player_y + 2, 
        player_x, 
        "@", 
        curses.color_pair(5) | curses.A_BOLD,
    )
