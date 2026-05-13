ITEMS_FR = {
    "wooden_sword": "Épée en bois",
    "stick": "Bâton",
    "oak_plank": "Planche en bois",
    "diamond_sword": "Épée en diamant",
    "stone": "Pierre",
    "dirt": "Terre",
    "grass": "Herbe",
    "diamond": "Diamant",
    "diamond_pickaxe": "Pioche en diamant",
    "wooden_pickaxe": "Pioche en bois",
    "stone_sword": "Épée en pierre",
    "stone_pickaxe": "Pioche en pierre",
    "crafting_table": "Table de craft",
    "oak_trunk": "Tronc de bois",
    "iron_ore": "Mineraie de fer",
    "coal_ore": "Mineraie de charbon",
    "coal_ingot": "Charbon",
    "iron_ingot": "Lingot de fer",
    "diamond_axe": "Hache en diamant",
    "mushroom": "Champignon",
    "wooden_axe": "Hache en bois",
    "torch": "Torche",
    "bow": "Arc",
    "arrow": "Flèche",
    "coal": "Charbon",
    "tnt": "Explosif",
    "iron_ingot": "Lingot de fer"
}

ITEMS_EN = {
    "wooden_word": "Wooden sword",
    "mushroom": "Mushroom",
    "coal_ingot": "Coal ingot",
    "tnt": "Tnt",

}

class LANGUAGE_TYPE:
    FRANCE = "FR"
    ENGLISH = "EN"

def get_language_items(name: str, language_type: LANGUAGE_TYPE) -> (str | None):
    if language_type == LANGUAGE_TYPE.FRANCE:
        return ITEMS_FR.get(name, None)
    elif language_type == LANGUAGE_TYPE.ENGLISH:
        return ITEMS_EN.get(name, None)
    else:
        return None