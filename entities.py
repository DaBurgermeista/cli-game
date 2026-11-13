import random

# 1. Entity Templates
ENTITY_DATA = {
    "wolf": {"name": "Timber Wolf", "char": "w", "color": 4, "hp": 3, "hostile": True},
    "deer": {"name": "Forest Deer", "char": "d", "color": 3, "hp": 2, "hostile": False},
    "troll": {"name": "Cave Troll", "char": "T", "color": 4, "hp": 6, "hostile": True},
}

def create_entity(kind, x, y):

    template = ENTITY_DATA[kind]
    return {
        "kind": kind,
        "name": template["name"],
        "char": template["char"],
        "color": template["color"],
        "hp": template["hp"],
        "hostile": template["hostile"],
        "x": x,
        "y": y,
    }

def get_entity_at(entities, x, y):

    for entity in entities:
        if entity["x"] == x and entity["y"] == y:
            return entity
    return None