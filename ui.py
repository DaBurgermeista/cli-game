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