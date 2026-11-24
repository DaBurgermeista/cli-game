import curses
import textwrap

from items import PACK_CAPACITY, format_inventory, item_detail


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

def show_inventory_panel(stdscr, title, player):
    """Navigable inventory panel.

    Arrow keys (or W/S) move the selection, Enter uses the selected item,
    D drops one of it, number keys are a shortcut to use a slot, and
    Esc/Q closes without doing anything.

    Returns ("use", index), ("drop", index), or None when closed.
    """
    max_y, max_x = stdscr.getmaxyx()

    # Keep a margin around the panel and ensure a usable minimum size.
    box_width = min(70, max_x - 4)
    box_height = min(18, max_y - 4)

    if box_width < 20 or box_height < 10:
        return None

    start_y = (max_y - box_height) // 2
    start_x = (max_x - box_width) // 2
    text_width = box_width - 4

    window = curses.newwin(box_height, box_width, start_y, start_x)
    # New windows default to keypad off, so arrow keys arrive as a raw
    # escape sequence: the first getch() returns ESC (27), which is the
    # panel's close key. Enabling keypad makes getch() return KEY_UP /
    # KEY_DOWN instead, like stdscr does under curses.wrapper.
    window.keypad(True)
    selected = 0

    while True:
        lines = format_inventory(player)
        if not lines:
            return None
        selected = max(0, min(selected, len(lines) - 1))

        window.erase()
        window.box()
        window.addnstr(1, 2, title, text_width, curses.A_BOLD)

        # Leave room for the title, the detail lines, and the prompt.
        available_lines = box_height - 8
        top = 0
        if selected >= top + available_lines:
            top = selected - available_lines + 1
        for row, line in enumerate(lines[top:top + available_lines]):
            index = top + row
            attr = curses.A_REVERSE if index == selected else 0
            window.addnstr(row + 3, 2, line, text_width, attr)

        detail = item_detail(player["inventory"][selected], player)
        detail_lines = textwrap.wrap(detail, width=text_width)[:2]
        detail_y = box_height - 4
        window.hline(detail_y - 1, 1, curses.ACS_HLINE, box_width - 2)
        for offset, detail_line in enumerate(detail_lines):
            window.addnstr(detail_y + offset, 2, detail_line, text_width, curses.A_DIM)

        prompt = "Up/Down select | Enter use | D drop | 1-9 use | Esc close"
        prompt_x = max(2, (box_width - len(prompt)) // 2)
        window.addnstr(box_height - 2, prompt_x, prompt, text_width, curses.A_DIM)

        window.refresh()
        key = window.getch()

        if key in (curses.KEY_UP, ord("w")):
            selected = max(0, selected - 1)
        elif key in (curses.KEY_DOWN, ord("s")):
            selected = min(len(lines) - 1, selected + 1)
        elif key in (10, 13, curses.KEY_ENTER):
            return ("use", selected)
        elif key == ord("d"):
            return ("drop", selected)
        elif ord("1") <= key <= ord("9"):
            index = key - ord("1")
            if index < len(lines):
                return ("use", index)
        elif key in (27, ord("q")):
            return None


def render_sidebar(
    stdscr,
    player,
    area_name,
    visible_entities,
    start_x,
    panel_width,
    area_label="Area",
):
    """Show player details and visible entities beside the map.

    ``area_name`` is the generator's current region tag (for example,
    ``forest`` or ``ruins``); ``area_label`` lets each world profile choose
    the UI term shown before that value.
    """
    panel_width = 25
    stats = player.get("stats", {})
    weapon = player["equipped_weapon"]["name"] if player["equipped_weapon"] else "Fists"
    level = player.get("level", 1)
    skills = player.get("skills") or {}

    def _skill_line(name):
        skill = skills.get(name.lower(), {"level": 1, "xp": 0})
        skill_level = skill.get("level", 1)
        return (
            f"{name} {skill_level} "
            f"({skill.get('xp', 0)}/{5 * skill_level})"
        )

    lines = [
        f"=== {player['name']} ===",
        f"HP:   {player['hp']}/{player['max_hp']}",
        f"Lvl:  {level} | XP: {player.get('xp', 0)}/{100 * level}",
        f"Wpn:  {weapon}",
        f"Key:  {'Yes' if player['has_key'] else 'No'} | Gold: {player['money']}",
        f"Pack: {len(player['inventory'])}/{PACK_CAPACITY}",
        "",
        "--- Location ---",
        f"{area_label}: {area_name.title()}",
        f"Pos: {player['x']}, {player["y"]}",
        "",
        "--- Attributes ---",
        f"STR: {stats.get('str', 1)}    INT: {stats.get('int', 1)}",
        f"DEX: {stats.get('dex', 1)}    WIS: {stats.get('wis', 1)}",
        f"CON: {stats.get('con', 1)}    LCK: {stats.get('luck', 1)}",
        "",
        "--- Skills ---",
        _skill_line("Unarmed"),
        _skill_line("Blades"),
        _skill_line("Spears"),
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

    for row_idx in range(max_y - 1):
        stdscr.addnstr(row_idx, start_x, "|", curses.A_DIM)
        if row_idx < len(lines) and avail_width > 0:
            stdscr.addnstr(row_idx, start_x+2, lines[row_idx], avail_width)
