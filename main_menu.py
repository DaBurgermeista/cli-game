"""Curses main menu; playable world choices come from world profiles."""

import curses

from world_profiles import WORLD_PROFILES

# Game modes are derived from profiles so adding a world does not require
# duplicating its name and description in the menu.
MENU_ITEMS = [
    (profile.menu_label, profile.description)
    for profile in WORLD_PROFILES.values()
] + [
    ("Options", "Configure display and gameplay settings."),
    ("Credits", "View game and project credits."),
    ("Quit", "Exit The Quiet River."),
]


def center_text(window, y, text, attr=curses.A_NORMAL):
    """Draw one line centered horizontally, clipped to the window width."""
    max_y, max_x = window.getmaxyx()

    if not (0 <= y < max_y):
        return

    x = max(0, (max_x - len(text)) // 2)

    window.addnstr(
        y,
        x,
        text,
        max(0, max_x - x - 1),
        attr,
    )


def print_menu_items(
    window,
    items,
    selected_index,
    offset_x,
    offset_y,
    spacing=1,
    is_main_menu=True,
):
    """Draw selectable labels and return their screen rows."""
    item_rows = []
    max_y, max_x = window.getmaxyx()

    for index, item in enumerate(items):
        row = offset_y + index * spacing
        item_rows.append(row)

        if not (0 <= row < max_y):
            continue

        is_selected = index == selected_index
        prefix = "> " if is_selected else "  "

        attr = curses.A_NORMAL

        if is_selected:
            attr |= curses.A_REVERSE | curses.A_BOLD

        # Reserve space for the cursor prefix so all labels line up.
        text = f"{prefix}{item}"

        available_width = max(0, max_x - offset_x - 1)

        window.addnstr(
            row,
            offset_x,
            text,
            available_width,
            attr,
        )

    return item_rows


def show_main_menu(stdscr):
    """Display the menu until a mode, utility page, or quit is selected."""
    selected_index = 0

    while True:
        max_y, max_x = stdscr.getmaxyx()
        stdscr.erase()

        # The menu uses five rows plus a description and footer; avoid drawing
        # into overlapping rows when the terminal is shorter than that layout.
        if max_y < 20 or max_x < 40:
            center_text(
                stdscr,
                max_y // 2,
                "Terminal too small. Resize to continue.",
                curses.A_BOLD,
            )
            stdscr.refresh()
            stdscr.getch()
            continue

        title = "THE QUIET RIVER"
        subtitle = "A procedural adventure crawler"

        center_text(
            stdscr,
            2,
            title,
            curses.A_BOLD | curses.color_pair(5),
        )

        center_text(
            stdscr,
            4,
            subtitle,
            curses.A_DIM,
        )

        # The menu labels are stored separately from descriptions.
        labels = [label for label, _ in MENU_ITEMS]

        menu_x = max(2, (max_x - 28) // 2)
        menu_y = 6

        print_menu_items(
            stdscr,
            labels,
            selected_index,
            menu_x,
            menu_y,
            spacing=2,
            is_main_menu=True,
        )

        # Show contextual help for the selected menu item.
        selected_description = MENU_ITEMS[selected_index][1]

        center_text(
            stdscr,
            menu_y + len(MENU_ITEMS) * 2 + 1,
            selected_description,
            curses.A_DIM,
        )

        # Footer controls.
        footer = "W/S or Arrow Keys: Select | Enter: Confirm | Q: Quit"

        center_text(
            stdscr,
            max_y - 2,
            footer,
            curses.A_DIM,
        )

        stdscr.refresh()

        key = stdscr.getch()

        if key in (ord("w"), curses.KEY_UP):
            selected_index = (selected_index - 1) % len(MENU_ITEMS)

        elif key in (ord("s"), curses.KEY_DOWN):
            selected_index = (selected_index + 1) % len(MENU_ITEMS)

        elif key in (10, 13, curses.KEY_ENTER):
            return MENU_ITEMS[selected_index][0]

        elif key in (ord("q"), 27):
            return "Quit"
