# ~/tiles.py

# Constants
WALL = "wall"
FLOOR = "floor"
DOOR = "door"
KEY = "key"
EXIT = "exit"
SPIKE = "spike"
TREE = "tree"
ROCK = "rock"
WATER = "water"
BRIDGE = "bridge"
BANK = "bank"
SHRINE = "shrine"

TILE_DATA = {
    FLOOR:  {"char": ".", "name": "Floor",      "color": 1, "walkable": True, "blocks_sight": False},
    WALL:   {"char": "#", "name": "Wall",       "color": 1, "walkable": False, "blocks_sight": True,  "bump_msg": "Solid stone blocks your path."},
    TREE:   {"char": "T", "name": "Tree",       "color": 2, "walkable": True,   "enter_msg": "You push through the forest canopy."},
    ROCK:   {"char": "O", "name": "Rock",       "color": 3, "walkable": False},
    WATER:  {"char": "~", "name": "Water",      "color": 6, "walkable": False,  "bump_msg": "The river current is too deep to cross."},
    SPIKE:  {"char": "^", "name": "Spike",      "color": 4, "walkable": True, "damage": 1},
    DOOR:   {"char": "+", "name": "Doorway",    "color": 3, "walkable": True,   "enter_msg": "You step through a weathered doorway."},
    KEY:    {"char": "K", "name": "Key",        "color": 3, "walkable": True, "pickup": "key"},
    EXIT:   {"char": "E", "name": "Exit",       "color": 3, "walkable": True, "exit": True},
    BRIDGE: {"char": "=", "name": "Bridge",     "color": 3, "walkable": True,   "enter_msg": "Wooden planks creak beneath your boots."},
    BANK:   {"char": ",", "name": "Riverbank",  "color": 3, "walkable": True,   "enter_msg": "Soft mud squishes along the riverbank."},
    SHRINE: {
        "char": "A",
        "name": "Ancient Shrine",
        "color": 5,
        "walkable": True,
        "enter_msg": "You discover an ancient shrine. Its stone is warm to the touch."
    },
}