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
    "The shrine is older than any stonework you have seen in the nearby "
    "ruins. Four weathered pillars surround a low altar marked with a "
    "single flowing line.\n\n"
    "When you place a hand on the stone, the river answers somewhere in "
    "the distance.\n\n"
    "For a moment, you are certain the forest is listening."
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
        "color": 6,
        "walkable": False,
        "blocks_sight": False,
        "bump_msg": "The river current is too deep to cross.",
    },
    MOUNTAIN: {
        "char": "M",
        "name": "Mountain",
        "color": 1,
        "walkable": False,
        "blocks_sight": True,
        "bump_msg": "Steep mountains block your path.",
    },
    HILL: {
        "char": "^",
        "name": "Hill",
        "color": 3,
        "walkable": True,
        "blocks_sight": True,
        "enter_msg": "You climb into rolling hills.",
    },
    SPIKE: {
        "char": "^",
        "name": "Spike",
        "color": 4,
        "walkable": True,
        "blocks_sight": False,
        "damage": 1,
    },
    DOOR: {
        "char": "+",
        "name": "Doorway",
        "color": 3,
        "walkable": True,
        "blocks_sight": False,
        "enter_msg": "You step through a weathered doorway.",
    },
    KEY: {
        "char": "K",
        "name": "Key",
        "color": 3,
        "walkable": True,
        "blocks_sight": False,
        "pickup": "key",
    },
    EXIT: {
        "char": "E",
        "name": "Exit",
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
        "name": "Ancient Shrine",
        "color": 5,
        "walkable": True,
        "blocks_sight": False,
        "enter_msg": (
            "You discover an ancient shrine. "
            "Its stone is warm to the touch."
        ),
        "text": SHRINE_TEXT,
    },
    CAMPFIRE: {
        "char": "*",
        "name": "Abandoned Camp",
        "color": 4,
        "walkable": True,
        "blocks_sight": False,
        "enter_msg": "You find the remains of an abandoned camp.",
        "text": (
            "A ring of stones surrounds a cold fire pit. The ash has not "
            "yet scattered, but the bedrolls and supplies are gone.\n\n"
            "Whoever camped here left in a hurry."
        ),
    },
}