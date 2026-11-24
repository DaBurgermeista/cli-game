# ~/tiles.py

# Constants
WALL = "wall"
FLOOR = "floor"
DOOR = "door"
KEY = "key"
EXIT = "exit"
SPIKE = "spike"
TREE = "tree"
TALL_GRASS = "tall_grass"
ROCK = "rock"
WATER = "water"
BRIDGE = "bridge"
BANK = "bank"
SHRINE = "shrine"
CAMPFIRE = "campfire"
MOUNTAIN = "mountain"
HILL = "hill"

SHRINE_TEXT = (
    "A Borant shrine, older than any stonework you have seen in the nearby "
    "ruins. Four weathered pillars surround a low altar marked with a "
    "single flowing line.\n\n"
    "When you place a hand on the stone, the dungeon answers somewhere in "
    "the distance.\n\n"
    "For a moment, you are certain the AI is listening."
)

TILE_DATA = {
    FLOOR: {
        "char": ".",
        "name": "Floor",
        "color": 2,
        "walkable": True,
        "blocks_sight": False,
    },
    WALL: {
        "char": "#",
        "name": "Wall",
        "color": 1,
        "walkable": False,
        "blocks_sight": True,
        "bump_msg": "Solid stone blocks your path.",
    },
    TREE: {
        "char": "T",
        "name": "Tree",
        "color": 2,
        "walkable": True,
        "blocks_sight": True,
        "enter_msg": "You push through the forest canopy.",
    },
    TALL_GRASS: {
        "char": '"',
        "name": "Tall Grass",
        "color": 3,
        "walkable": True,
        "blocks_sight": False,
        "enter_msg": "You push through waist-high grass.",
    },
    ROCK: {
        "char": "O",
        "name": "Rock",
        "color": 3,
        "walkable": False,
        "blocks_sight": True,
        "bump_msg": "A large rock blocks your path.",
    },
    WATER: {
        "char": "~",
        "name": "Water",
        "color": 7,
        "walkable": False,
        "blocks_sight": False,
        "bump_msg": "The river current is too deep to cross.",
    },
    MOUNTAIN: {
        "char": "▲",
        "name": "Mountain",
        "color": 1,
        "walkable": False,
        "blocks_sight": True,
        "bump_msg": "Steep mountains block your path.",
    },
    HILL: {
        "char": "∩",
        "name": "Hill",
        "color": 1,
        "walkable": True,
        "blocks_sight": True,
        "enter_msg": "You climb into rolling hills.",
    },
    SPIKE: {
        "char": "!",
        "name": "Spike Trap",
        "color": 10,
        "walkable": True,
        "blocks_sight": False,
        "damage": 1,
    },
    DOOR: {
        "char": "+",
        "name": "Dungeon Door",
        "color": 3,
        "walkable": True,
        "blocks_sight": False,
        "enter_msg": "You step through a weathered dungeon door.",
    },
    KEY: {
        "char": "K",
        "name": "Boss Key",
        "color": 3,
        "walkable": True,
        "blocks_sight": False,
        "pickup": "key",
    },
    EXIT: {
        "char": ">",
        "name": "Stairwell",
        "color": 3,
        "walkable": True,
        "blocks_sight": False,
        "exit": True,
    },
    BRIDGE: {
        "char": "=",
        "name": "Bridge",
        "color": 3,
        "walkable": True,
        "blocks_sight": False,
        "enter_msg": "Wooden planks creak beneath your boots.",
    },
    BANK: {
        "char": ",",
        "name": "Riverbank",
        "color": 3,
        "walkable": True,
        "blocks_sight": False,
        "enter_msg": "Soft mud squishes along the riverbank.",
    },
    SHRINE: {
        "char": "A",
        "name": "Borant Shrine",
        "color": 5,
        "walkable": True,
        "blocks_sight": False,
        "enter_msg": (
            "You discover a Borant shrine. "
            "Its stone hums with dungeon energy."
        ),
        "text": SHRINE_TEXT,
    },
    CAMPFIRE: {
        "char": "*",
        "name": "Safe Room",
        "color": 4,
        "walkable": True,
        "blocks_sight": False,
        "enter_msg": "You find a safe room. The AI marks it as a rest area.",
        "text": (
            "A ring of stones surrounds a cold fire pit. The ash has not "
            "yet scattered, but the bedrolls and supplies are gone.\n\n"
            "Whoever camped here left in a hurry, or the dungeon took them."
        ),
    },
}

def get_walkable_tiles(room, exclude=None):
    if exclude is None:
        exclude = set()

    walkable = []
    for y, row in enumerate(room):
        for x, tile in enumerate(row):
            if (x, y) in exclude:
                continue
            if TILE_DATA.get(tile, {}).get("walkable", False):
                walkable.append((x, y))
    return walkable