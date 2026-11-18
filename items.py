import json
import random
from pathlib import Path

DATA_FILE = Path(__file__).parent / "items.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    ITEM_DATA = json.load(f)

def create_item(kind, x, y):

    template = ITEM_DATA[kind]
    return {
        "kind": kind,
        "name": template["name"],
        "char": template["char"],
        "color": template["color"],
        "value": template["value"],
        "type": template["type"],
        "x": x,
        "y": y,
    }

def get_item_at(items, x, y):
    for item in items:
        if item["x"] == x and item["y"] == y:
            return item
    return None

def spawn_random_items(room, biomes, walkable_tiles, count=12):
    items = []
    candidates = list(walkable_tiles)
    random.shuffle(candidates)

    for x, y in candidates:
        if len(items) >= count:
            break
    
        tile_biome = biomes[y][x]
        valid_kinds = [
            kind for kind, data in ITEM_DATA.items()
            if tile_biome in data.get("biomes", [])
        ]

        if not valid_kinds:
            continue

        weights = [ITEM_DATA[k].get("spawn_weight", 1) for k in valid_kinds]
        chosen_kind = random.choices(valid_kinds, weights=weights, k=1)[0]
        items.append(create_item(chosen_kind, x, y))
    
    return items

def format_inventory(player):
    lines = []
    for idx, item in enumerate(player["inventory"]):
        equipped_tag = " [Equipped]" if item is player["equipped_weapon"] else ""
        lines.append(f"{idx + 1}. {item['name']}{equipped_tag}")
    return lines

def use_item(player, choice):
    inventory = player["inventory"]
    if choice is None or not (0 <= choice < len(inventory)):
        return None

    selected_item = inventory[choice]

    if selected_item["type"] == "heal":
        player["hp"] = min(player["hp"], player["hp"] + selected_item["value"])
        inventory.pop(choice)
        return f"You use the {selected_item['name']} and recover {selected_item['value']} health."

    if selected_item["type"] == "weapon":
        player["equipped_weapon"] = selected_item
        return f"You equip the {selected_item['name']} (+{selected_item['value']} attack)."
    
    return f"You can't use the {selected_item['name']}."

