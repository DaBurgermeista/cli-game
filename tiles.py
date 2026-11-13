# ~/tiles.py

# Constants
WALL = "wall"
FLOOR = "floor"
DOOR = "door"
KEY = "key"
EXIT = "exit"
SPIKE = "spike"
PLAYER ="player"
TREE = "tree"
ROCK = "rock"
WATER = "water"
BRIDGE = "bridge"
BANK = "bank"

TILE_DATA = {
    FLOOR: {"char": ".", "name": "Floor", "color": 1, "walkable": True},
    WALL: {"char": "#", "name": "Wall", "color": 1, "walkable": False},
    TREE: {"char": "T", "name": "Tree", "color": 2, "walkable": True},
    ROCK: {"char": "O", "name": "Rock", "color": 3, "walkable": False},
    WATER: {"char": "~", "name": "Water", "color": 6, "walkable": False},
    SPIKE: {"char": "^", "name": "Spike", "color": 4, "walkable": True, "damage": 1},
    DOOR: {"char": "+", "name": "Doorway", "color": 3, "walkable": True, "needs_key": False},
    KEY: {"char": "K", "name": "Key", "color": 3, "walkable": True, "pickup": "key"},
    EXIT: {"char": "E", "name": "Exit", "color": 3, "walkable": True, "exit": True},
    BRIDGE: {"char": "=", "name": "Bridge", "color": 3, "walkable": True},
    BANK: {"char": ",", "name": "Riverbank", "color": 3, "walkable": True},
}