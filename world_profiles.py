"""Selectable world setups: generator, size, and introductory presentation."""

from dataclasses import dataclass

from dungeon import generate_dungeon
from worldgen import generate_overworld


@dataclass(frozen=True)
class WorldProfile:
    """Configuration needed to start and label one kind of run.

    Profiles keep world-specific setup out of the action rules and rendering
    loop. The generator follows the shared world-generator return contract.
    """

    menu_label: str  # Also serves as the menu's selection key.
    description: str
    width: int  # Map dimensions passed to the selected generator.
    height: int
    generator: object  # Callable returning grid/elevation/regions/start.
    title: str  # Shown in the intro panel and game HUD.
    intro: str  # World-specific text shown before the first turn.
    area_label: str  # Label for the current region in the HUD/sidebar.
    starting_message: str  # First entry in the in-game message log.


# The menu uses these keys as its returned choices; crawler.py looks up the
# matching profile and passes it to create_game_state.
WORLD_PROFILES = {
    "New Game": WorldProfile(
        menu_label="New Game",
        description="Begin a journey through the wilderness.",
        width=100,
        height=60,
        generator=generate_overworld,
        title="The Quiet River",
        intro=(
            "You have entered a wilderness few travelers cross willingly.\n\n"
            "Somewhere beyond these woods, the Quiet River has changed its "
            "course. Settlements on its banks speak of unfamiliar ruins, "
            "abandoned camps, and old shrines standing where no shrine "
            "should be.\n\n"
            "You came to see what the land is becoming."
        ),
        area_label="Biome",
        starting_message="Explore the wilderness.",
    ),
    "Dungeon Run": WorldProfile(
        menu_label="Dungeon Run",
        description="Explore connected rooms, corridors, and hazards.",
        width=64,
        height=36,
        generator=generate_dungeon,
        title="Dungeon Floor 1",
        intro=(
            "The stone passage narrows behind you. Ahead, old rooms and "
            "dark corridors descend into the dungeon. Find the exit and "
            "watch for creatures in the ruins."
        ),
        area_label="Area",
        starting_message="You enter the dungeon.",
    ),
}
