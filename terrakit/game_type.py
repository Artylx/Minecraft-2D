from terrakit.texture_manager import TextureType
import copy
from terrakit import context

class BlockProperty:
    REGISTRY = {}

    def __init__(self, name, block_id, collidable, texture, breakable, item_type, life, weakness=None, need_to_drop=None, light_emission=0, container=(0, 0)):
        self.block_name = name
        self.block_id = block_id
        self.texture = texture
        self.collidable = collidable
        self.breakable = breakable
        self.item_type = item_type
        self.life = life
        self.weakness = weakness
        self.need_to_drop = need_to_drop
        self.light_emission = light_emission

        self.container = container

        BlockProperty.REGISTRY[name.upper()] = self

    def can_drop(self, tool) -> bool:
        if not self.need_to_drop:
            return True
        else:
            if not tool:
                return False
            if isinstance(tool, self.need_to_drop):
                return True
        return False

    def __str__(self):
        return f"BlockProperty(name:{self.block_name}, block_id:{self.block_id}, collidable:{self.collidable}, breakable:{self.breakable}, item_type:{self.item_type})"


class ItemProperty:
    REGISTRY = {}

    def __init__(self, name=None, texture=None, max_stack=None, 
                 placeable=None, block_type=None, description="Materiaux", 
                 heatable=False, warmer_item=None, fuel_level=0, electricity=0):
        self.description = description + '\n'
        self.item_name = name
        self.texture = texture
        self.max_stack = max_stack
        self.placeable = placeable
        self.block_type = block_type
        self.description = description

        # POWER OF BLOCKS
        self.electricity = electricity

        # FURNACE
        self.heatable = heatable
        self.warmer_item = warmer_item
        self.fuel_level = fuel_level
        
        self.register()

    def is_fuel(self):
        if self.fuel_level > 0:
            return True
        else:
            return

    def add_description(self, text, end='\n'):
        self.description = self.description + text + end

    def register(self):
        if self.item_name:
            ItemProperty.REGISTRY[self.item_name.upper()] = self

    def __str__(self):
        return f"ItemProperty(name:{self.item_name}, texture:{str(self.texture)}, max_stack:{self.max_stack}, placeable:{self.placeable}, block_type:{self.block_type})"

    def to_json(self, add_data=None):
        data = {
            "name": self.item_name,
            "max_stack": self.max_stack,
            "placeable": self.placeable,
            "block_type": self.block_type
        }

        if add_data is None:
            add_data = {}

        data.update(add_data)
        return data
    
    def load(self, data): 
        mapping = { "name": "item_name", "max_stack": "max_stack", "placeable": "placeable", "block_type": "block_type", } 
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
                self.register()
        return self
    
    def get_texture(self):
        if context.get_resource_pack().texture_manager() is None:
            print("TextureManager non défini")
            return None

        return context.get_resource_pack().texture_manager().get_texture(self.texture)
    
    @staticmethod
    def from_dict(data):
        name = data["name"].upper()
        item = ItemProperty.REGISTRY.get(name)

        if not item:
            print(f"Item inconnu: {name}")
            return None

        return item
    
    def __eq__(self, other):
        if not isinstance(other, ItemProperty):
            return False

        return self.item_name == other.item_name and self.description == other.description


class Tool(ItemProperty):
    def __init__(self, name, texture, durability, description=None):
        if not description:
            description = "Outils"
        super().__init__(name, texture, 1, False, None, description)
        self.durability = durability
        self.max_durability = durability
    
    def load(self, data):
        print("Load Tool")

        mapping = { "durability": "durability", "max_durability": "max_durability", } 
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
                self.register()
        
        return super().load(data)
    
    def to_json(self, add_data=None):
        data = {
            "durability": self.durability,
            "max_durability": self.max_durability,
        }

        if add_data is None:
            add_data = {}

        data.update(add_data)

        return super().to_json(data)

class Attack_tool(Tool):
    def __init__(self, name, texture, materialTool, description=None):
        power, durability = 0, 0
        if materialTool == MaterialTool.WOODEN:
            power, durability = 7, 110
        elif materialTool == MaterialTool.STONE:
            power, durability = 9, 240
        elif materialTool == MaterialTool.IRON:
            power, durability = 12, 523
        elif materialTool == MaterialTool.GOLDEN:
            power, durability = 14, 432
        elif materialTool == MaterialTool.DIAMOND:
            power, durability = 19, 1561
        
        if not description:
            description = "Points de dégats: &c" + str(power)
        super().__init__(name, texture, durability, description)
        self.power = power
    
    def get_attack_damage(self):
        return self.power
    
class Bow_tool(Tool):
    def __init__(self, name, texture, use_texture, durability=None, power=11, description=None):
        if not durability:
            durability = 10

        if not description:
            description = "Dégats de l'Arc: &c" + str(power)
        super().__init__(name, texture, durability, description)
        self.power = power
        self.use_texture = use_texture

    def get_texture_used(self):
        if context.get_resource_pack().texture_manager() is None:
            print("TextureManager non défini")
            return None
        
        return context.get_resource_pack().texture_manager().get_texture(self.use_texture)

class MaterialTool:
    WOODEN = 0
    STONE = 1
    IRON = 2
    GOLDEN = 3
    DIAMOND = 4

class Pickaxe_tool(Tool):
    def __init__(self, name, texture, materialTool, description=None):
        power, durability = 0, 0
        if materialTool == MaterialTool.WOODEN:
            power, durability = 15, 110
        elif materialTool == MaterialTool.STONE:
            power, durability = 18, 240
        elif materialTool == MaterialTool.IRON:
            power, durability = 21, 523
        elif materialTool == MaterialTool.GOLDEN:
            power, durability = 24, 432
        elif materialTool == MaterialTool.DIAMOND:
            power, durability = 28, 1561

        if not description:
            description = "Puissance de pioche: &c" + str(power)
        super().__init__(name, texture, durability, description)
        self.power = power
    
class Axe_tool(Tool):
    def __init__(self, name, texture, materialTool, description=None):
        power, durability = 0, 0
        if materialTool == MaterialTool.WOODEN:
            power, durability = 15, 110
        elif materialTool == MaterialTool.STONE:
            power, durability = 18, 240
        elif materialTool == MaterialTool.IRON:
            power, durability = 21, 523
        elif materialTool == MaterialTool.GOLDEN:
            power, durability = 24, 432
        elif materialTool == MaterialTool.DIAMOND:
            power, durability = 28, 1561

        if not description:
            description = "Puissance de hache: &c" + str(power)
        super().__init__(name, texture, durability, description)
        self.power = power

class Consumable(ItemProperty):
    def __init__(self, name, texture, max_stack, description=None):
        if not description:
            description = "Consommable"
        super().__init__(name, texture, max_stack, False, None, description)

class Hanger_consumable(Consumable):
    def __init__(self, name, texture, max_stack, life_regen, description=None):

        if not description:
            description = "Régénération de vie: &a" + str(life_regen)

        super().__init__(name, texture, max_stack, description)
        self.life_regen = life_regen

class Shovel_tool(Tool):
    def __init__(self, name, texture, materialTool, description=None):
        power, durability = 0, 0
        if materialTool == MaterialTool.WOODEN:
            power, durability = 15, 110
        elif materialTool == MaterialTool.STONE:
            power, durability = 18, 240
        elif materialTool == MaterialTool.IRON:
            power, durability = 21, 523
        elif materialTool == MaterialTool.GOLDEN:
            power, durability = 24, 432
        elif materialTool == MaterialTool.DIAMOND:
            power, durability = 28, 1561

        if not description:
            description = "Puissance de pelle: &c" + str(power)
        super().__init__(name, texture, durability, description)
        self.power = power

ItemProperty.DIRT = ItemProperty("dirt", TextureType.DIRT, 100, True, "DIRT")
ItemProperty.GRASS = ItemProperty("grass", TextureType.GRASS, 100, True, "GRASS")
ItemProperty.STONE = ItemProperty("stone", TextureType.STONE, 100, True, "STONE")


ItemProperty.COAL_ORE = ItemProperty("coal_ore", TextureType.COAL_ORE, 100, True, "COAL_ORE", heatable=True, warmer_item="COAL_INGOT")
ItemProperty.IRON_ORE = ItemProperty("iron_ore", TextureType.IRON_ORE, 100, True, "IRON_ORE", heatable=True, warmer_item="IRON_INGOT")
ItemProperty.GOLD_ORE = ItemProperty("gold_ore", TextureType.GOLD_ORE, 100, True, "GOLD_ORE", heatable=True, warmer_item="GOLD_INGOT")


ItemProperty.COAL = ItemProperty("coal_ingot", TextureType.COAL, 100, False, None, fuel_level=10)
ItemProperty.IRON = ItemProperty("iron_ingot", TextureType.IRON, 100, False, None)
ItemProperty.GOLD = ItemProperty("gold_ingot", TextureType.GOLD, 100, False, None)


ItemProperty.OAK_TRUNK = ItemProperty("oak_trunk", TextureType.OAK_TRUNK, 100, True, "OAK_TRUNK", heatable=True, warmer_item="COAL_INGOT", fuel_level=5)
ItemProperty.OAK_LEAVES = ItemProperty("oak_leaves", TextureType.OAK_LEAVES, 100, True, "OAK_LEAVES")
ItemProperty.OAK_TRUNK_BOTTOM = ItemProperty("oak_trunk_bottom", TextureType.OAK_TRUNK_BOTTOM, 100, True, "OAK_TRUNK_BOTTOM")
ItemProperty.OAK_TRUNK_MID = ItemProperty("oak_trunk_mid", TextureType.OAK_TRUNK_MID, 100, True, "OAK_TRUNK_MID")
ItemProperty.CRAFTING_TABLE = ItemProperty("crafting_table", TextureType.CRAFTING_TABLE, 100, True, "CRAFTING_TABLE")
ItemProperty.FURNACE = ItemProperty("furnace", TextureType.FURNACE, 100, True, "FURNACE", "Permet de cuir les objets")
ItemProperty.CHEST = ItemProperty("chest", TextureType.CHEST, 100, True, "CHEST", "Permet de stocker des objets")
ItemProperty.IRON_CHEST = ItemProperty("iron_chest", TextureType.IRON_CHEST, 100, True, "IRON_CHEST", "Permet de stocker des objets")
ItemProperty.STONE_SNOW = ItemProperty("stone_snow", TextureType.STONE_SNOW, 100, True, "STONE_SNOW")
ItemProperty.SNOW = ItemProperty("snow", TextureType.SNOW, 100, True, "SNOW")
ItemProperty.BEDROCK = ItemProperty("bedrock", TextureType.BEDROCK, 100, True, "BEDROCK")
ItemProperty.REDSTONE = ItemProperty("redstone", TextureType.REDSTONE, 100, True, "REDSTONE")
ItemProperty.REDSTONE_EMERALD = ItemProperty("redstone_emerald", TextureType.REDSTONE_EMERALD, 100, True, "REDSTONE_EMERALD")
ItemProperty.REDSTONE_SAND = ItemProperty("redstone_sand", TextureType.REDSTONE_SAND, 100, True, "REDSTONE_SAND")
ItemProperty.OAK_PLANK = ItemProperty("oak_plank", TextureType.OAK_PLANK, 100, True, "OAK_PLANK", fuel_level=4)
ItemProperty.TNT = ItemProperty("tnt", TextureType.TNT, 100, True, "TNT")

ItemProperty.GRASS_1 = ItemProperty("grass_1", TextureType.GRASS_1, 100, True, "GRASS_1")
ItemProperty.GRASS_2 = ItemProperty("grass_2", TextureType.GRASS_2, 100, True, "GRASS_2")
ItemProperty.GRASS_3 = ItemProperty("grass_3", TextureType.GRASS_3, 100, True, "GRASS_3")
ItemProperty.GRASS_4 = ItemProperty("grass_4", TextureType.GRASS_4, 100, True, "GRASS_4")
ItemProperty.GRASS_BROWN = ItemProperty("grass_brown", TextureType.GRASS_BROWN, 100, True, "GRASS_BROWN")
ItemProperty.ROCK = ItemProperty("rock", TextureType.ROCK, 100, True, "ROCK")
ItemProperty.MUSHROOM = ItemProperty("mushroom", TextureType.MUSHROOM, 100, True, "MUSHROOM")
ItemProperty.TORCH = ItemProperty("torch", TextureType.TORCH, 100, True, "TORCH", "Produit de la lumière.")

# EPE
ItemProperty.DIAMOND_SWORD = Attack_tool("diamond_sword", TextureType.DIAMOND_SWORD, MaterialTool.DIAMOND)
ItemProperty.WOODEN_SWORD = Attack_tool("wooden_sword", TextureType.WOODEN_SWORD, MaterialTool.WOODEN)
ItemProperty.STONE_SWORD = Attack_tool("stone_sword", TextureType.STONE_SWORD, MaterialTool.STONE)
ItemProperty.IRON_SWORD = Attack_tool("iron_sword", TextureType.IRON_SWORD, MaterialTool.IRON)
ItemProperty.GOLDEN_SWORD = Attack_tool("golden_sword", TextureType.GOLDEN_SWORD, MaterialTool.GOLDEN)

# PIOCHE
ItemProperty.DIAMOND_PICKAXE = Pickaxe_tool("diamond_pickaxe", TextureType.DIAMOND_PICKAXE, MaterialTool.DIAMOND)
ItemProperty.WOODEN_PICKAXE = Pickaxe_tool("wooden_pickaxe", TextureType.WOODEN_PICKAXE, MaterialTool.WOODEN)
ItemProperty.STONE_PICKAXE = Pickaxe_tool("stone_pickaxe", TextureType.STONE_PICKAXE, MaterialTool.STONE)
ItemProperty.IRON_PICKAXE = Pickaxe_tool("iron_pickaxe", TextureType.IRON_PICKAXE, MaterialTool.IRON)
ItemProperty.GOLDEN_PICKAXE = Pickaxe_tool("golden_pickaxe", TextureType.GOLDEN_PICKAXE, MaterialTool.GOLDEN)

# HACHE
ItemProperty.DIAMOND_AXE = Axe_tool("diamond_axe", TextureType.DIAMOND_AXE, MaterialTool.DIAMOND)
ItemProperty.WOODEN_AXE = Axe_tool("wooden_axe", TextureType.WOODEN_AXE, MaterialTool.WOODEN)
ItemProperty.STONE_AXE = Axe_tool("stone_axe", TextureType.STONE_AXE, MaterialTool.STONE)
ItemProperty.IRON_AXE = Axe_tool("iron_axe", TextureType.IRON_AXE, MaterialTool.IRON)
ItemProperty.GOLDEN_AXE = Axe_tool("golden_axe", TextureType.GOLDEN_AXE, MaterialTool.GOLDEN)

# ARC
ItemProperty.BOW = Bow_tool("bow", TextureType.BOW, TextureType.BOW_ARROW)
ItemProperty.ARROW = ItemProperty("arrow", TextureType.ARROW, 100, False, None)

# CONSUMABLE
ItemProperty.CHIPS = Hanger_consumable("chips", TextureType.CHIPS, 10, 40)
ItemProperty.EGG = ItemProperty("egg", TextureType.EGG, 100, False, None, "Peut être cuit", True, warmer_item="COOKED_EGG")
ItemProperty.COOKED_EGG = Hanger_consumable("cooked_egg", TextureType.COOKED_EGG, 10, 20)

ItemProperty.STICK = ItemProperty("stick", TextureType.STICK, 100, False, None)

ItemProperty.NONE = ItemProperty("none", TextureType.DEFAULT, 0, False, None, "&cItem non utilisable")

# BLOCKS
BlockProperty.STONE = BlockProperty("stone", 1, True, TextureType.STONE, True, "STONE", 300, Pickaxe_tool, Pickaxe_tool)
BlockProperty.DIRT = BlockProperty("dirt", 2, True, TextureType.DIRT, True, "DIRT", 60)
BlockProperty.AIR = BlockProperty("air", 3, False, TextureType.NONE, False, None, None)
BlockProperty.GRASS = BlockProperty("grass", 4, True, TextureType.GRASS, True, "DIRT", 60)
BlockProperty.BEDROCK = BlockProperty("bedrock", 5, True, TextureType.BEDROCK, False, "BEDROCK", None)

BlockProperty.COAL_ORE = BlockProperty("coal_ore", 6, True, TextureType.COAL_ORE, True, "COAL_INGOT", 360, Pickaxe_tool, Pickaxe_tool)
BlockProperty.IRON_ORE = BlockProperty("iron_ore", 7, True, TextureType.IRON_ORE, True, "IRON_ORE", 540, Pickaxe_tool, Pickaxe_tool)
BlockProperty.GOLD_ORE = BlockProperty("gold_ore", 8, True, TextureType.GOLD_ORE, True, "GOLD_ORE", 800, Pickaxe_tool, Pickaxe_tool)

BlockProperty.SAND = BlockProperty("sand", 9, True, TextureType.SAND, True, "SAND", 70)
BlockProperty.WATER = BlockProperty("water", 10, False, TextureType.WATER, False, None, None)
BlockProperty.CRAFTING_TABLE = BlockProperty("crafting_table", 18, True, TextureType.CRAFTING_TABLE, True, "CRAFTING_TABLE", 200, Axe_tool)
BlockProperty.FURNACE = BlockProperty("furnace", 30, True, TextureType.FURNACE, True, "FURNACE", 200, Pickaxe_tool, Pickaxe_tool)
BlockProperty.CHEST = BlockProperty("chest", 31, True, TextureType.CHEST, True, "CHEST", 200, Axe_tool)
BlockProperty.IRON_CHEST = BlockProperty("iron_chest", 32, True, TextureType.IRON_CHEST, True, "IRON_CHEST", 300, Pickaxe_tool)
BlockProperty.STONE_SNOW = BlockProperty("stone_snow", 19, True, TextureType.STONE_SNOW, True, "STONE", 300, Pickaxe_tool)
BlockProperty.SNOW = BlockProperty("snow", 20, True, TextureType.SNOW, True, "SNOW", 30)
BlockProperty.REDSTONE = BlockProperty("redstone", 21, True, TextureType.REDSTONE, True, "REDSTONE", 50, Pickaxe_tool)
BlockProperty.REDSTONE_EMERALD = BlockProperty("redstone_emerald", 22, True, TextureType.REDSTONE_EMERALD, True, "REDSTONE_EMERALD", 50, Pickaxe_tool)
BlockProperty.REDSTONE_SAND = BlockProperty("redstone_sand", 23, True, TextureType.REDSTONE_SAND, True, "REDSTONE_SAND", 70)    
BlockProperty.TNT = BlockProperty("tnt", 28, True, TextureType.TNT, True, "TNT", 20)

BlockProperty.OAK_TRUNK = BlockProperty("oak_trunk", 11, True, TextureType.OAK_TRUNK, True, "OAK_TRUNK", 100, Axe_tool)
BlockProperty.OAK_LEAVES = BlockProperty("oak_leaves", 12, False, TextureType.OAK_LEAVES, True, None, 60, Axe_tool)
BlockProperty.OAK_TRUNK_BOTTOM = BlockProperty("oak_trunk_bottom", 13, False, TextureType.OAK_TRUNK_BOTTOM, True, "OAK_TRUNK", 100, Axe_tool)
BlockProperty.OAK_TRUNK_MID = BlockProperty("oak_trunk_mid", 13, False, TextureType.OAK_TRUNK_MID, True, "OAK_TRUNK", 100, Axe_tool)
BlockProperty.OAK_PLANK = BlockProperty("oak_plank", 27, True, TextureType.OAK_PLANK, True, "OAK_PLANK", 100, Axe_tool)

BlockProperty.GRASS_1 = BlockProperty("grass_1", 14, False, TextureType.GRASS_1, True, None, 30)
BlockProperty.GRASS_2 = BlockProperty("grass_2", 15, False, TextureType.GRASS_2, True, None, 30)
BlockProperty.GRASS_3 = BlockProperty("grass_3", 16, False, TextureType.GRASS_3, True, None, 30)
BlockProperty.GRASS_4 = BlockProperty("grass_4", 17, False, TextureType.GRASS_4, True, None, 30)
BlockProperty.GRASS_BROWN = BlockProperty("grass_brown", 24, False, TextureType.GRASS_BROWN, True, None, 30)
BlockProperty.ROCK = BlockProperty("rock", 25, False, TextureType.ROCK, True, "STONE", 150, Pickaxe_tool)
BlockProperty.MUSHROOM = BlockProperty("mushroom", 26, False, TextureType.MUSHROOM, True, "MUSHROOM", 20)

BlockProperty.TORCH = BlockProperty("torch", 29, False, TextureType.TORCH, True, "TORCH", 1, light_emission=15)

def get_item_type_by_name(name: str):
    if not name:
        return None

    return ItemProperty.REGISTRY.get(name.upper())

def get_block_property(name: str):
    if not name:
        return None
    return BlockProperty.REGISTRY.get(name.upper())