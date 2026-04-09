ITEMS_FR = {
    "wooden_sword": "Epée en bois",
    "stick": "Bâton",
    "oak_plank": "Planche en bois",
    "diamond_sword": "Epée en diamant",
    "stone": "Pierre",
    "dirt": "Terre",
    "grass": "Herbe",
    "diamond": "Diamant",
    "diamond_pickaxe": "Pioche en diamant",
    "wooden_pickaxe": "Pioche en bois",
    "stone_sword": "Epée en pierre",
    "stone_pickaxe": "Pioche en pierre",
}

class LANGUAGE_TYPE:
    FRANCE = "FR"

def get_language_items(name: str, language_type: LANGUAGE_TYPE) -> (str | None):
    if language_type == LANGUAGE_TYPE.FRANCE:
        return ITEMS_FR.get(name, None)
    else:
        return None