from matplotlib.pylab import matrix

from classes.texture_manager import  TextureManager
import pygame
from classes import game_property, game_type
import uuid

class RotationMode:
    NONE = 0          # aucune rotation
    ALL = 1           # 0°, 90°, 180°, 270°
    HALF = 2          # 0° et 180° uniquement

class Recipe():
    def __init__(self, recipe, result, rotation=RotationMode.NONE, mirror=False):
        self.recipe = recipe
        self.result = result
        self.rotation = rotation
        self.mirror = mirror

    def load(self, data):
        mapping = {
            "recipe": "recipe",
            "result": "result",
            "rotation": "rotation",
            "mirror": "mirror",
        }

        # Vérification
        required = list(mapping.keys())
        missing = [k for k in required if k not in data]
        if missing:
            print(f"Champs manquants: {missing}")
            return None

        # Assignation complexe
        for key, target in mapping.items():
            if isinstance(target, tuple):
                obj, attr = target
                setattr(getattr(self, obj), attr, data[key])
            else:
                setattr(self, target, data[key])
        return self
    
    def to_json(self) -> dict:
        return {
            "recipe": self.recipe,
            "result": self.result,
            "rotation": self.rotation,
            "mirror": self.mirror,
        }

RECIPES_ = [
    Recipe((
        ("oak_trunk",),
    ), 
    [(4, "oak_plank")], 
    )
]

RECIPES = {
    (
        ("oak_trunk",),
    ): {
        "result": [(4, "oak_plank")],
        "rotation": RotationMode.NONE,
        "mirror": False
    },

    (
        ("oak_plank","oak_plank",),
        ("oak_plank","oak_plank",),
     
    ): {
        "result": [(1, "crafting_table")],
        "rotation": RotationMode.NONE,
        "mirror": False
    },

    (
        ("oak_plank",),
        ("oak_plank",)
    ): {
        "result": [(2, "stick")],
        "rotation": RotationMode.NONE,
        "mirror": False
    },

    (
        ("oak_plank",),
        ("oak_plank",),
        ("stick",)
    ): {
        "result": [(1, "wooden_sword")],
        "rotation": RotationMode.NONE,
        "mirror": False
    },

    (
        ("oak_plank", "oak_plank", "oak_plank",),
        (None, "stick", None,),
        (None, "stick",None,)
    ): {
        "result": [(1, "wooden_pickaxe")],
        "rotation": RotationMode.NONE,
        "mirror": False
    },

    (
        ("oak_plank", "oak_plank",),
        ("stick", "oak_plank",),
        ("stick",None,)
    ): {
        "result": [(1, "wooden_axe")],
        "rotation": RotationMode.NONE,
        "mirror": True
    },

    (
        ("stone", "stone", "stone",),
        (None, "stick", None,),
        (None, "stick",None,)
    ): {
        "result": [(1, "stone_pickaxe")],
        "rotation": RotationMode.NONE,
        "mirror": False
    },

    (
        ("stone",),
        ("stone",),
        ("stick",)
    ): {
        "result": [(1, "stone_sword")],
        "rotation": RotationMode.NONE,
        "mirror": False
    }
}

class CraftManager():
    def __init__(self, size=(3, 3), current_inv=None):
        self.width = size[0]
        self.height = size[1]
        self.size = self.width * self.height
        self.current_inv = current_inv

        self.items = [None] * self.size

        self.result = None

    def set_item(self, index, item):
        self.items[index] = item
        self.update_result()

    def to_matrix(self):
        return [
            self.items[y * self.width:(y + 1) * self.width]
            for y in range(self.height)
        ]
    
    def mirror_matrix(self, matrix):
        return [row[::-1] for row in matrix]
    
    def trim_matrix(self, matrix):
        rows = len(matrix)
        cols = len(matrix[0])

        min_x, max_x = cols, 0
        min_y, max_y = rows, 0

        for y in range(rows):
            for x in range(cols):
                if matrix[y][x]:
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)

        if min_x > max_x or min_y > max_y:
            return [[]]

        return [
            row[min_x:max_x+1]
            for row in matrix[min_y:max_y+1]
        ]

    def get_item(self, index):
        return self.items[index]

    def matrix_to_key(self, matrix):
        return tuple(
            tuple(
                item.item_property.item_name if item else None
                for item in row
            )
            for row in matrix
        )

    def rotate_matrix(self, matrix):
        return [list(row) for row in zip(*matrix[::-1])]
    
    def get_all_transformations(self, matrix, rotation_mode, allow_mirror):
        results = []

        rotations = self.get_rotations_by_mode(matrix, rotation_mode)

        for rot in rotations:
            results.append(rot)

            if allow_mirror:
                mirrored = self.mirror_matrix(rot)
                results.append(mirrored)

        return results
    
    def get_rotations_by_mode(self, matrix, mode):
        rotations = []

        if mode == RotationMode.NONE:
            return [matrix]

        current = matrix

        for i in range(4):
            if mode == RotationMode.HALF and i >= 2:
                break

            rotations.append(current)
            current = self.rotate_matrix(current)

        return rotations

    def update_result(self):
        base_matrix = self.to_matrix()
        trimmed = self.trim_matrix(base_matrix)

        for recipe_key, recipe_data in RECIPES.items():
            mode = recipe_data.get("rotation", RotationMode.NONE)
            mirror = recipe_data.get("mirror", False)

            for transformed in self.get_all_transformations(trimmed, mode, mirror):
                key = self.matrix_to_key(transformed)

                if key == recipe_key:
                    count, name = recipe_data["result"][0]

                    item_pro = game_type.get_item_type_by_name(name)

                    if item_pro:
                        self.result = ItemStack(
                            game_type.get_item_type_by_name(name),
                            count
                        )
                    else:
                        self.result = ItemStack(
                            game_type.ItemProperty.NONE,
                            0
                        )
                    return

        self.result = None

    def close(self):
        if self.current_inv is not None:

            for item in self.items:

                if item:
                    self.current_inv.add_item(item)

    def craft(self):
        if not self.result:
            return None

        crafted_item = ItemStack(
            self.result.item_property,
            self.result.count
        )

        # consommer uniquement 1 par slot utilisé
        for i in range(self.size):
            item = self.items[i]

            if item:
                if item.count > 1:
                    item.count -= 1
                else:
                    self.items[i] = None
        return crafted_item
    
    def has_result(self):
        return self.result is not None

    def take_result(self):
        if not self.result:
            return None

        crafted = self.craft()

        self.result = None

        self.update_result()
        return crafted


class Inventory():
    def __init__(self, size):
        self.uuid = uuid.uuid4()
        self.size = size

        self.clear()

        self.title = f"Inventory uuid:{self.uuid}"

    def update(self):
        to_remove = []

        for slot, item in self.items.items():
            if not item:
                continue

            if isinstance(item.item_property, game_type.Tool):
                if item.item_property.is_break():
                    to_remove.append(slot)

        # suppression
        for slot in to_remove:
            print(f"Slot : {slot}")
            self.items[slot] = None
        

    def add_item(self, itemStack):
        reste = itemStack.count

        for item in self.items.values():
            if not item:
                continue

            if item.item_property == itemStack.item_property:
                reste = item.add_item(reste)
                if reste == 0:
                    return None  # tout ajouté

        for slot in range(self.size):
            if not self.items.get(slot):
                max_stack = itemStack.item_property.max_stack

                to_add = min(reste, max_stack)
                self.items[slot] = ItemStack(itemStack.item_property, to_add)

                reste -= to_add

                if reste == 0:
                    return None

        if reste > 0:
            self.drop_item(ItemStack(itemStack.item_property, reste))

    def delete_item_property(self, item_property, count):
        reste = count

        for slot in range(self.size):
            item = self.items.get(slot)

            if not item:
                continue

            if item.item_property != item_property:
                continue

            to_remove = min(item.count, reste)

            item.count -= to_remove
            reste -= to_remove

            if item.count <= 0:
                self.items[slot] = None

            if reste <= 0:
                return
            
    def has_item(self, item_property: game_type.ItemProperty, count=1) -> bool:
        total = 0

        for item in self.items.values():
            if item and item.item_property == item_property:
                total += item.count

        return total >= count
            
    def is_full(self):
        for item in self.items.values():
            if item is None:
                return False

            if item.count < item.item_property.max_stack:
                return False

        return True
            
    def drop_item(self, itemStack):
        # drop itemStack in the world
        pass

    def debug_inv(self):
        i = 0
        for item in self.items:
            print(f"[{i}] {str(item)}")
            i += 1

    def get_item(self, index):
        self.update()

        if len(self.items) != 0:
            if index <= len(self.items) - 1:
                return self.items[index]
        return None 
    
    def delete_item(self, index):
        itemStack = self.items[index]

        if itemStack:
            if itemStack.count <= 1:
                self.items[index] = None
            else:
                itemStack.count -= 1
        
        self.update()
    
    def clear(self):
        self.items = {i: None for i in range(self.size)}

    def to_json(self) -> dict:
        items = []
        for slot in self.items.keys():
            if self.items[slot] != None:
                items.append({
                    "slot": slot,
                    "itemStack": self.items[slot].to_json()
                })

        data = {
            "uuid": str(self.uuid),
            "size": self.size,
            "title": self.title,
            "items": items,
        }

        return data

    def load(self, data):
        # champs simples
        simple_fields = [
            "uuid", "size",
            "items", "title"
        ]

        # Vérification
        required = simple_fields
        missing = [k for k in required if k not in data]
        if missing:
            print(f"Champs manquants: {missing}")
            return None

        # Assignation simple
        for attr in simple_fields:
            if attr == "items":
                items = data.get("items", [])
                for dict_item in items:
                    slot = dict_item.get("slot", None)
                    if slot is None:
                        continue

                    item = ItemStack(None)
                    item = item.load(dict_item.get("itemStack", None))

                    if item is None:
                        continue

                    self.items[slot] = item
            else:
                setattr(self, attr, data[attr])
        return self

class Crafting_types:
    CRAFTING_TABLE = (3, 3)
    INV = (2, 2)

class Entity_Inventory(Inventory):
    def __init__(self, owner_entity, size=24):
        super().__init__(size)
        self.owner_uuid = owner_entity.get_uuid()
        self.owner_entity = owner_entity

        self.title = f"Inventory of {owner_entity.name}"
        self.ui = UI_Inventory(self, case_number=6)

        self.craft_manager = None

    def drop_item(self, itemStack):
        self.owner_entity.drop_item(itemStack)
    
    def open_crafting(self, type_: Crafting_types):
        if type_ in Crafting_types.__dict__.values():
            self.craft_manager = CraftManager(size=type_, current_inv=self)
        else:
            self.close_crafting()

    def close_crafting(self):
        self.craft_manager.close()
        self.craft_manager = None

    def to_json(self) -> dict:
        data = super().to_json()
        data["owner_uuid"] = str(self.owner_uuid)
        return data
    
    def load(self, data):
        if "owner_uuid" not in data:
            print("Champs manquant: owner_uuid")
            return None
        self.owner_uuid = uuid.UUID(data["owner_uuid"])
        return super().load(data)

class UI_Inventory():
    def __init__(self, inv, case_number=6):
        self.inv = inv
        self.size = inv.size
        self.case_number = case_number
        self.selected_index = 0

    def move_selected_index(self, move):
        index = (self.selected_index + move) % self.case_number
        self.set_selected_index(index)
        

    def set_selected_index(self, index):
        if len(self.inv.items) == 0:
            self.selected_index = 0
            return

        self.selected_index = max(0, min(index, self.case_number - 1))
        print(f"selected index: {self.selected_index}")

    def get_selected_item(self):
        return self.inv.get_item(self.selected_index)

class ItemStack():
    texture_manager = None

    def __init__(self, item_property, count=1):
        self.item_property = item_property

        if type(count) != int:
            try:
                count = int(count)
            except:
                count = 1
        self.count = count

        self.rect = pygame.Rect(0, 0, game_property.INVENTORY_SIZE_CASE, game_property.INVENTORY_SIZE_CASE)

        self.texture = None
        self.update_texture()
    
    def load(self, data):
        # champs simples
        simple_fields = [
            "item_type_name", "count"
        ]

        # Vérification
        required = simple_fields
        missing = [k for k in required if k not in data]
        if missing:
            print(f"Champs manquants: {missing}")
            return None

        # Assignation simple
        for attr in simple_fields:
            if attr == "item_type_name":
                item_type_name = data["item_type_name"]
                
                item_property = game_type.get_item_type_by_name(item_type_name)
                if item_property:
                    self.item_property = item_property
                else:
                    return None
            else:
                setattr(self, attr, data[attr])
        self.update_texture()
        return self

    def __str__(self):
        return f"ItemStack(type:{self.item_property}, count:{self.count})"
    
    def add_item(self, n):
        if self.item_property:
            if self.count + n > self.item_property.max_stack:
                self.count = self.item_property.max_stack
                return self.count - self.item_property.max_stack + n
            else:
                self.count += n
                return 0
        
    def render(self, screen, pos, texture_size=None, draw_number=True):
        self.update_texture()
        texture = self.texture
        if texture_size and self.texture:
            texture = pygame.transform.scale(self.texture, texture_size)

        self.rect.topleft = pos

        if texture:
            screen.blit(texture, pos)

        if draw_number:
            if self.count > 1 and self.item_property is not None:
                font = pygame.font.SysFont(None, game_property.INVENTORY_SIZE_CASE // 2)
                text = font.render(str(self.count), True, (255, 255, 255))

                text_rect = text.get_rect()
                text_rect.bottomright = self.rect.bottomright
                text_rect.x -= 10
                text_rect.y -= 10

                screen.blit(text, text_rect)

    def update_texture(self):
        if self.item_property is not None:
            self.texture = self.get_texture()

            if (self.texture):
                self.texture = pygame.transform.scale(self.texture, (game_property.INVENTORY_SIZE_CASE, game_property.INVENTORY_SIZE_CASE))

    def get_texture(self):
        return self.item_property.get_texture()
    
    def is_posable(self):
        return self.item_property.placeable
    
    def to_json(self):
        return {
            "item_type_name": self.item_property.item_name, 
            "count": self.count,
        }