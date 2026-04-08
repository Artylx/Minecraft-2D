from classes.texture_manager import  TextureManager
import pygame
from classes import game_property, game_type
import uuid

RECIPES = {
    ("oak_trunk", None, None, None): [(4, "oak_plank")],
    ("oak_plank", None, "oak_plank", None): [(2, "stick")],
    ("oak_plank", "oak_plank", "oak_plank", "oak_plank"): [(1, "crafting_table")],
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

    def get_item(self, index):
        return self.items[index]

    def get_recipe_key(self):
        key = []
        for item in self.items:
            if item:
                key.append(item.item_property.item_name)
            else:
                key.append(None)
        return tuple(key)

    def update_result(self):
        key = self.get_recipe_key()
        recipe = RECIPES.get(key)

        if recipe:
            count, name = recipe[0]

            self.result = ItemStack(
                game_type.get_item_type_by_name(name),
                count
            )
        else:
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
        for item in self.result:
            if item:
                return True
        return False

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
        if len(self.inv.items) == 0:
            self.selected_index = 0
            return
        self.selected_index = (self.selected_index + move) % self.case_number
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
        return self.texture_manager.get_texture(self.item_property.texture)
    
    def is_posable(self):
        return self.item_property.placeable
    
    def to_json(self):
        return {
            "item_type_name": self.item_property.item_name, 
            "count": self.count,
        }