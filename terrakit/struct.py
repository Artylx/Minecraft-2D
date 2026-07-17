import json, pygame
from enum import Enum
from terrakit import game_property, game_type

STRUCTURES_DIR = "classes/structs/"

class StructureType(Enum):
    SMALL_TREE = "small_tree"
    HOUSE = "house"
    BIG_TREE = "big_tree"
    GRASS_1 = "grass_1"
    GRASS_2 = "grass_2"
    GRASS_3 = "grass_3"
    GRASS_4 = "grass_4"
    ROCK = "rock"
    MUSHROOM = "mushroom"

class StructureManager:
    def __init__(self):
        self.structures = {}  # {StructureType: data_json}

        self.load_structures()

    def load_structures(self):
        self.load_structure(StructureType.SMALL_TREE, "small_tree.json")
        self.load_structure(StructureType.BIG_TREE, "big_tree.json")
        self.load_structure(StructureType.GRASS_1, "grass_1.json")
        self.load_structure(StructureType.GRASS_2, "grass_2.json")
        self.load_structure(StructureType.GRASS_3, "grass_3.json")
        self.load_structure(StructureType.GRASS_4, "grass_4.json")
        self.load_structure(StructureType.ROCK, "rock.json")
        self.load_structure(StructureType.MUSHROOM, "mushroom.json")

    def load_structure(self, struct_type: StructureType, json_path):
        try:
            with open(game_property.get_resource_path(STRUCTURES_DIR + json_path), "r") as f:
                data = json.load(f)
            self.structures[struct_type] = data

        except Exception as e:
            print(f"Erreur en lisant {json_path}: {e}")
            return

    def can_place_structure(self, chunk, data, base_x, base_y):
        origin = data.get("origin", {"x": 0, "y": 0})
        ox, oy = origin.get("x", 0), origin.get("y", 0)

        # 🔹 1. Vérification du block à l'origine
        condition_blocks = data.get("condition_blocks", [])

        if condition_blocks:
            origin_x = base_x
            origin_y = base_y - 1  # Vérifier le block juste en dessous de l'origine

            block = chunk.get_block(origin_x, origin_y)

            if not block or block.block_property.block_name not in condition_blocks:
                print(f"Condition non respectée à ({origin_x}, {origin_y})")
                return False

        # 🔹 2. Vérification des collisions
        for block_data in data.get("blocks", []):
            bx = block_data.get("x", 0) - ox + base_x
            by = block_data.get("y", 0) - oy + base_y

            block = chunk.get_block(bx, by)

            # Autoriser seulement si AIR
            if block is None or block.block_property != game_type.BlockProperty.AIR:
                return False

        return True

    def place_structure(self, chunk, struct_type: StructureType, base_x, base_y):
        data = self.structures.get(struct_type)

        if not data:
            print(f"Structure '{struct_type}' non trouvée !")
            return False

        if not self.can_place_structure(chunk, data, base_x, base_y):
            # Impossible de placer ici
            # print(f"Impossible de placer la structure '{struct_type}' à ({base_x}, {base_y}) - collision détectée.")
            return False

        origin = data.get("origin", {"x": 0, "y": 0})
        ox, oy = origin.get("x", 0), origin.get("y", 0)

        # Placer les blocs
        for block in data.get("blocks", []):
            x = block["x"] - ox + base_x
            y = block["y"] - oy + base_y

            block_name = block["block"]
            chunk.set_block_with_name(x, y, block_name)

        # Placer les entités
        for ent_data in data.get("entities", []):
            type_ = ent_data.get("type")
            ex = ent_data.get("x", 0) - ox + base_x
            ey = ent_data.get("y", 0) - oy + base_y
            if type_:
                entity = None
                if type_ == "Zombie":
                    pass
                elif type_ == "Player":
                    pass
                if entity:
                    entity.rect.x = ex * 32  # TILE_SIZE
                    entity.rect.y = ey * 32
                    chunk.entities.append(entity)
        return True