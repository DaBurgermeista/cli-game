import curses
import textwrap


def show_text_panel(stdscr, title, text):
    max_y, max_x = stdscr.getmaxyx()

    # Keep a margin around the panel and ensure a usable minimum size.
    box_width = min(70, max_x - 4)
    box_height = min(16, max_y - 4)

    if box_width < 20 or box_height < 8:
        return

    start_y = (max_y - box_height) // 2
    start_x = (max_x - box_width) // 2

    window = curses.newwin(box_height, box_width, start_y, start_x)
    window.box()

    # Interior width: borders plus a one-character margin on both sides.
    text_width = box_width - 4

    wrapped_lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            wrapped_lines.append("")
            continue

        wrapped_lines.extend(textwrap.wrap(paragraph, width=text_width))

    # Leave space for title and the "press any key" prompt.
    available_lines = box_height - 5

    window.addnstr(1, 2, title, box_width - 4, curses.A_BOLD)

    for index, line in enumerate(wrapped_lines[:available_lines]):
        window.addnstr(index + 3, 2, line, text_width)

    prompt = "Press any key to continue"
    prompt_x = max(2, (box_width - len(prompt)) // 2)
    window.addnstr(box_height - 2, prompt_x, prompt, text_width, curses.A_DIM)

    window.refresh()
    window.getch()

def show_inventory_panel(stdscr, title, lines):

    max_y, max_x = stdscr.getmaxyx()

    # Keep a margin around the panel and ensure a usable minimum size.
    box_width = min(70, max_x - 4)
    box_height = min(16, max_y - 4)

    if box_width < 20 or box_height < 8:
        return

    start_y = (max_y - box_height) // 2
    start_x = (max_x - box_width) // 2

    window = curses.newwin(box_height, box_width, start_y, start_x)
    window.box()

    # Interior width: borders plus a one-character margin on both sides.
    text_width = box_width - 4 

    window.addnstr(1, 2, title, text_width, curses.A_BOLD)

    available_lines = box_height - 5
    for index, line in enumerate(lines[:available_lines]):
        window.addnstr(index + 3, 2, line, text_width)

    prompt = "Press 1-9 to use item, or any other key to close"
    prompt_x = max(2, (box_width - len(prompt)) // 2)
    window.addnstr(box_height - 2, prompt_x, prompt, text_width, curses.A_DIM)

    key = window.getch()
    if ord("1") <= key <= ord("9"):
        return key - ord("1")
    return None

def render_sidebar(stdscr, player, biome_name, visible_entities, start_x, panel_width):
    panel_width = 25
    stats = player.get("stats", {})
    weapon = player["equipped_weapon"]["name"] if player["equipped_weapon"] else "Fists"

    lines = [
        f"=== {player['name']} ===",
        f"HP:   {player['hp']}/{player['max_hp']}",
        f"Wpn:  {weapon}",
        f"Key:  {'Yes' if player['has_key'] else 'No'} | $: {player['money']}",
        "",
        "--- Location ---",
        f"Biome: {biome_name.title()}",
        f"Pos: {player['x']}, {player["y"]}",
        "",
        "--- Attributes ---",
        f"STR: {stats.get('str', 1)}    INT: {stats.get('int', 1)}",
        f"DEX: {stats.get('dex', 1)}    WIS: {stats.get('wis', 1)}",
        f"CON: {stats.get('con', 1)}    LCK: {stats.get('luck', 1)}",
        "",
        "--- Nearby ---",
    ]

    if not visible_entities:
        lines.append("None")
    else:
        for ent in visible_entities[:5]:
            lines.append(f"{ent['char']} {ent['name']} ({ent['hp']}hp)")

    max_y, max_x = stdscr.getmaxyx()

    if start_x >= max_x - 1:
        return
    
    avail_width = min(panel_width - 2, max_x - (start_x + 2) - 1)

    if row_idx in range(max_y - 1):
        stdscr.addnstr(row_idx, start_x, "|", curses.A_DIM)
        if row_idx < len(lines) and avail_width > 0:
            stdscr.addnstr(row_idx, start_x+2, lines[row_idx], avail_width)
