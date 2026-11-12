import curses
import random

# Constants
WALL = "#"
FLOOR = "."
DOOR = "+"
KEY = "K"
EXIT = "E"
SPIKE = "^"
PLAYER ="@"

MAP_WIDTH = 50
MAP_HEIGHT = 22
MIN_ROOM_WIDTH = 4
MAX_ROOM_WIDTH = 6
MIN_ROOM_HEIGHT = 3
MAX_ROOM_HEIGHT = 5
# ---

def generate_room(width, height, num_spikes):
    # 1. Start with a solid block of walls
    grid = [[WALL for _ in range(width)] for _ in range(height)]

    # 2. Carve out open floor inside the outer border and collect open floor tiles
    floor_tiles = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            grid[y][x] = FLOOR
            floor_tiles.append((x, y))

    # Shuffle the list so popping from it gives guaranteed unique positions
    random.shuffle(floor_tiles)

    # Place the player, key, exit, and spikes without overlapping
    start_x, start_y = floor_tiles.pop()

    key_x, key_y = floor_tiles.pop()
    grid[key_y][key_x] = KEY

    exit_x, exit_y = floor_tiles.pop()
    grid[exit_y][exit_x] = EXIT

    for _ in range(num_spikes):
        if floor_tiles:
            sx, sy = floor_tiles.pop()
            grid[sy][sx] = SPIKE

    return grid, start_x, start_y

def can_enter(tile, has_key):
    return tile != WALL and (tile != DOOR or has_key)

def is_area_solid(grid, x1, y1, w, h):
    # Make sure the room itself stays inside the outer wall border
    if x1 < 1 or y1 < 1:
        return False

    if x1 + w > len(grid[0]) - 1:
        return False

    if y1 + h > len(grid) - 1:
        return False

    # Check only the proposed room tiles.
    # Do not check the surrounding border, because one side touches the hallway.
    for y in range(y1, y1 + h):
        for x in range(x1, x1 + w):
            if grid[y][x] != WALL:
                return False

    return True

def add_doors_to_room(grid, rx, ry, rw, rh, max_doors=2):
    possible_doors = []

    # Collect valid spots for doors on top and bottom walls
    for x in range(rx, rx + rw):
        possible_doors.append((x, ry - 1))
        possible_doors.append((x, ry + rh))

    # Collect valid door spots for left and right walls
    for y in range(ry, ry + rh):
        possible_doors.append((rx - 1, y))
        possible_doors.append((rx + rw, y))

    # Shuffle so doors appear on random walls
    random.shuffle(possible_doors)

    doors_placed = 0
    for dx, dy in possible_doors:
        if doors_placed >= max_doors:
            break

        # Make sure the door isn't on the outer edge of the map
        # and make sure it is a solid wall
        if 1 <= dx < len(grid[0]) - 1 and 1 <= dy < len(grid) - 1:
            if grid[dy][dx] == WALL:
                grid[dy][dx] = "+"
                doors_placed += 1
    

def expand_from_door(grid, door_x, door_y, dx, dy):
    # Turn '+' door just stepped on into an open floor
    grid[door_y][door_x] = FLOOR
    hall_length = random.randint(2, 4)

    # 1. Dig the hallway
    hx, hy = door_x, door_y
    for _ in range(hall_length):
        next_hx, next_hy = hx + dx, hy + dy
        # Stop if about to hit map edge
        if next_hx < 2 or next_hx >= len(grid[0]) - 2 or next_hy < 2 or next_hy >= len(grid) - 2:
            return
        hx, hy = next_hx, next_hy
        grid[hy][hx] = FLOOR

    # 2. Pick a random size for the new room
    rw = random.randint(4, 6)
    rh = random.randint(3, 5)

    # Postion the room depending on direction walked
    if dx == 1:
        rx, ry = hx + 1, hy - (rh // 2)
    elif dx == -1:
        rx, ry = hx - rw, hy - (rh // 2)
    elif dy == 1:
        rx, ry = hx - (rw // 2), hy + 1
    elif dy == -1:
        rx, ry = hx - (rw // 2), hy - rh

    # 3. Only carve the room if the space is untouched
    if is_area_solid(grid, rx, ry, rw, rh):
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                grid[y][x] = FLOOR
        # Add 1 or 2 new '+' doors
        add_doors_to_room(grid, rx, ry, rw, rh)

    

def main(stdscr):
    # Hide the blinking terminal cursor
    curses.curs_set(0)    

    floor = 1
    health = 3
    has_key = False
    message = f"Floor {floor}: Find the key and reach the exit!"
    
    room  = [[WALL for _ in range(50)] for _ in range(22)]
    
    start_rx, start_ry, start_rw, start_rh = 22, 9, 6, 4
    for y in range(start_ry, start_ry + start_rh):
        for x in range(start_rx, start_rx + start_rw):
            room[y][x] = FLOOR

    add_doors_to_room(room, start_rx, start_ry, start_rw, start_rh, max_doors=3)

    player_x = start_rx + 2
    player_y = start_ry + 2    

    while True:
        stdscr.clear()
        
        stdscr.addstr(0,0,f"Floor: {floor} | Health: {health} | Key: {'Yes' if has_key else 'No'}")
        
        # Build room on screen from raw_room        
        for y, row in enumerate(room):
            for x, tile in enumerate(row):
                if x == player_x and y == player_y:
                    stdscr.addstr(y + 2, x, PLAYER)
                else:
                    stdscr.addstr(y + 2, x, tile)

        stdscr.addstr(len(room) + 3, 0, message)
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

        if can_enter(room[next_y][next_x], has_key):
            dx = next_x - player_x
            dy = next_y - player_y
            player_x, player_y = next_x, next_y
            
            if room[player_y][player_x] == "+":
                expand_from_door(room, player_x, player_y, dx, dy)
                message = "You opened a door into the unknown!"
            

        current_tile = room[player_y][player_x]
        
        if current_tile  == KEY:
            message = "You found a key"
            has_key = True
            room[player_y][player_x] = FLOOR
        if current_tile == EXIT:
            message = "You escaped!"
            break
        if current_tile  == "+":
            message = "You open the door."
            room[player_y][player_x] = FLOOR
        if health == 0:
            message = "You died."
            stdscr.getkey()
            break
        if current_tile == SPIKE:
            room[player_y][player_x] = FLOOR
            health = max(0, health - 3)
            message = "Ouch! You stepped on a spike!"

curses.wrapper(main)
