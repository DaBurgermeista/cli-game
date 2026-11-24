import json
import random
from pathlib import Path

DATA_FILE = Path(__file__).parent / "items.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    ITEM_DATA = json.load(f)

# A stack counts as one slot, so ten potions take one slot, not ten.
PACK_CAPACITY = 12

RARITY_RANK = {"common": 0, "uncommon": 1, "rare": 2}
CATEGORY_ORDER = {"loot_box": 0, "heal": 1, "weapon": 2}
LOOT_BOX_KINDS = ("loot_box_bronze", "loot_box_silver", "loot_box_gold")

# Odds that a defeated enemy drops a loot box, and which tier it is.
ENEMY_LOOT_DROP_CHANCE = 0.35
ENEMY_LOOT_DROP_WEIGHTS = {
    "loot_box_bronze": 80,
    "loot_box_silver": 15,
    "loot_box_gold": 5,
}


def create_item(kind, x, y):
    template = ITEM_DATA[kind]
    item = {
        "kind": kind,
        "name": template["name"],
        "char": template["char"],
        "color": template["color"],
        "value": template["value"],
        "type": template["type"],
        "rarity": template.get("rarity", "common"),
        "description": template.get("description", ""),
        "stackable": template.get("stackable", False),
        "count": 1,
        "x": x,
        "y": y,
    }
    if template["type"] == "loot_box":
        item["rolls"] = template.get("rolls", 1)
        item["guarantee"] = template.get("guarantee")
    if template["type"] == "weapon":
        item["skill"] = template.get("skill", "unarmed")
    return item


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


def sort_inventory(player):
    """Keep the pack in a stable, scannable order: boxes, heals, weapons."""
    player["inventory"].sort(
        key=lambda item: (
            CATEGORY_ORDER.get(item["type"], 3),
            -RARITY_RANK.get(item.get("rarity", "common"), 0),
            item["name"],
        )
    )


def add_to_inventory(player, item):
    """Add an item to the pack. Returns False when the pack is full.

    Stackable items merge into an existing stack and never take a new slot.
    """
    inventory = player["inventory"]
    if item.get("stackable"):
        for stack in inventory:
            if stack["kind"] == item["kind"]:
                stack["count"] += item.get("count", 1)
                return True
    if len(inventory) >= PACK_CAPACITY:
        return False
    inventory.append(item)
    sort_inventory(player)
    return True


def _take_one(player, choice):
    """Remove one unit from a stack (or the whole entry) and return it.

    Returns a single-count copy for stackable items, the entry itself
    otherwise, or None for an invalid choice.
    """
    inventory = player["inventory"]
    if choice is None or not (0 <= choice < len(inventory)):
        return None
    entry = inventory[choice]
    if entry.get("stackable") and entry.get("count", 1) > 1:
        entry["count"] -= 1
        single = dict(entry)
        single["count"] = 1
        return single
    return inventory.pop(choice)


def format_inventory(player):
    lines = []
    for idx, item in enumerate(player["inventory"]):
        equipped_tag = " [Equipped]" if item is player["equipped_weapon"] else ""
        count_tag = f" x{item['count']}" if item.get("count", 1) > 1 else ""
        rarity = item.get("rarity", "common").title()
        if item["type"] == "heal":
            effect = f" (+{item['value']} HP)"
        elif item["type"] == "weapon":
            effect = f" (+{item['value']} atk)"
        elif item["type"] == "loot_box":
            effect = " (open me!)"
        else:
            effect = ""
        lines.append(
            f"{idx + 1}. {item['name']}{count_tag} [{rarity}]{effect}{equipped_tag}"
        )
    return lines


def item_detail(item, player):
    """One or two lines describing the item, for the inventory panel."""
    parts = [item.get("description", "")]
    if item["type"] == "weapon":
        equipped = player.get("equipped_weapon")
        if equipped is item:
            parts.append("Equipped. Press Enter to unequip.")
        elif equipped is not None:
            parts.append(
                f"Equipping swaps out {equipped['name']} (+{equipped['value']} atk)."
            )
        else:
            parts.append("Press Enter to equip.")
    elif item["type"] == "loot_box":
        parts.append("Press Enter to open it. Opening takes a turn.")
    elif item["type"] == "heal":
        parts.append("Press Enter to use it.")
    return " ".join(part for part in parts if part)


def use_item(player, choice):
    """Use one inventory entry.

    Returns (message, consumed_turn). A wasted use, like drinking a potion
    at full health, does not consume a turn. Loot boxes are opened by the
    action layer, not here, because opening needs the game state.
    """
    inventory = player["inventory"]
    if choice is None or not (0 <= choice < len(inventory)):
        return None, False

    selected_item = inventory[choice]

    if selected_item["type"] == "loot_box":
        return None, False

    if selected_item["type"] == "heal":
        if player["hp"] >= player["max_hp"]:
            return "You are already at full health.", False
        _take_one(player, choice)
        player["hp"] = min(player["max_hp"], player["hp"] + selected_item["value"])
        return (
            f"You use the {selected_item['name']} and recover "
            f"{selected_item['value']} health.",
            True,
        )

    if selected_item["type"] == "weapon":
        if player["equipped_weapon"] is selected_item:
            player["equipped_weapon"] = None
            return f"You unequip the {selected_item['name']}.", True
        player["equipped_weapon"] = selected_item
        return f"You equip the {selected_item['name']} (+{selected_item['value']} attack).", True

    return f"You can't use the {selected_item['name']}.", False


def drop_item(player, choice):
    """Drop one unit of an inventory entry. Returns (dropped, message)."""
    inventory = player["inventory"]
    if choice is None or not (0 <= choice < len(inventory)):
        return None, "Nothing to drop."
    was_equipped = player.get("equipped_weapon") is inventory[choice]
    dropped = _take_one(player, choice)
    if dropped is None:
        return None, "Nothing to drop."
    if was_equipped:
        player["equipped_weapon"] = None
    return dropped, f"You drop the {dropped['name']}."


def roll_loot_box(box):
    """Roll the contents of a loot box. Returns a list of new items."""
    rolls = box.get("rolls", 1)
    guarantee = box.get("guarantee")
    pool = [
        kind for kind, data in ITEM_DATA.items()
        if data.get("type") != "loot_box"
    ]
    results = []
    for roll_index in range(rolls):
        # The last roll honors the box's rarity guarantee, if it has one.
        if guarantee is not None and roll_index == rolls - 1:
            minimum = RARITY_RANK[guarantee]
            eligible = [
                kind for kind in pool
                if RARITY_RANK.get(ITEM_DATA[kind].get("rarity", "common"), 0) >= minimum
            ]
        else:
            eligible = pool
        weights = [ITEM_DATA[kind].get("spawn_weight", 1) for kind in eligible]
        chosen = random.choices(eligible, weights=weights, k=1)[0]
        results.append(create_item(chosen, 0, 0))
    return results


def open_loot_box(game, player, choice):
    """Open a loot box in the pack.

    Returns (messages, discovery). Rolled items that do not fit in the pack
    spill onto the floor at the player's feet.
    """
    inventory = player["inventory"]
    if choice is None or not (0 <= choice < len(inventory)):
        return [], None
    box = inventory[choice]
    if box["type"] != "loot_box":
        return [], None

    _take_one(player, choice)
    rolled = roll_loot_box(box)
    box_name = box["name"]

    messages = [
        f"You open the {box_name}!",
        "The Borant AI chimes in: \"Let's see what our Crawler gets...\"",
    ]
    lines = [f"You crack open the {box_name}. The AI leans in."]
    spilled = []
    for item in rolled:
        rarity = item.get("rarity", "common")
        if rarity == "rare":
            messages.append(
                "The AI gasps: \"A RARE drop! The viewers are going wild!\""
            )
        if add_to_inventory(player, item):
            lines.append(f"- {item['name']} [{rarity.title()}]")
        else:
            item["x"], item["y"] = player["x"], player["y"]
            game.items.append(item)
            spilled.append(item)
            lines.append(f"- {item['name']} [{rarity.title()}] (no room, dropped at your feet)")
    if spilled:
        messages.append("Your pack is full, so some loot spilled to the floor.")
    messages.append(
        "Inside: " + ", ".join(item["name"] for item in rolled) + "."
    )
    return messages, ("Loot Box Opened!", "\n".join(lines))
