from tiles import TILE_DATA


def bresenham_line(x0, y0, x1, y1):
    points = []

    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)

    step_x = 1 if x0 < x1 else -1
    step_y = 1 if y0 < y1 else -1

    error = dx + dy

    while True:
        points.append((x0, y0))

        if x0 == x1 and y0 == y1:
            break

        error_twice = 2 * error

        if error_twice >= dy:
            error += dy
            x0 += step_x

        if error_twice <= dx:
            error += dx
            y0 += step_y

    return points

def has_line_of_sight(grid, start_x, start_y, target_x, target_y):
    line = bresenham_line(start_x, start_y, target_x, target_y)

    # Skip the player's own tile.
    for x, y in line[1:]:
        tile_id = grid[y][x]
        blocks_sight = TILE_DATA[tile_id].get("blocks_sight", False)

        # The blocking tile itself is visible, but tiles beyond it are not.
        if blocks_sight:
            return (x, y) == (target_x, target_y)

    return True

def get_visible_tiles(grid, player_x, player_y, radius=8):
    visible = {(player_x, player_y)}

    min_y = max(0, player_y - radius)
    max_y = min(len(grid), player_y + radius + 1)

    min_x = max(0, player_x - radius)
    max_x = min(len(grid[0]), player_x + radius + 1)

    for y in range(min_y, max_y):
        for x in range(min_x, max_x):
            dx = x - player_x
            dy = y - player_y

            # Circular visibility radius.
            if dx * dx + dy * dy > radius * radius:
                continue

            if has_line_of_sight(grid, player_x, player_y, x, y):
                visible.add((x, y))

    return visible