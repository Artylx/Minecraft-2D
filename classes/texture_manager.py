import pygame
from classes import game_property

BLOCKS_PATH = "blocks/"
ITEMS_PATH = "items/"
TOOLS_PATH = "tools/"
CONSUMABLE_PATH = "consumable/"
ENTITIES_PATH = "entities/"
MOBS_PATH = "mobs/"
PLAYER_PATH = "player/"
OTHERS_PATH = "others/"

class TextureType:
    NONE = ""
    DIRT = "dirt"
    STONE = "stone"
    GRASS = "grass"
    BEDROCK = "bedrock"

    COAL_ORE = "coal_ore"
    IRON_ORE = "iron_ore"
    GOLD_ORE = "gold_ore"

    SAND = "sand"
    WATER = "water"
    SNOW = "snow"
    STONE_SNOW = "stone_snow"
    REDSTONE = "redstone"
    REDSTONE_EMERALD = "redstone_emerald"
    REDSTONE_SAND = "redstone_sand"
    STICK = "stick"

    GRASS_1 = "grass_1"
    GRASS_2 = "grass_2"
    GRASS_3 = "grass_3"
    GRASS_4 = "grass_4"
    GRASS_BROWN = "grass_brown"
    ROCK = "rock"
    MUSHROOM = "mushroom"

    OAK_TRUNK = "oak_trunk"
    OAK_LEAVES = "oak_leaves"
    OAK_TRUNK_BOTTOM = "oak_trunk_bottom"
    OAK_TRUNK_MID = "oak_trunk_mid"
    OAK_PLANK = "oak_plank"
    TNT = "tnt"

    BOW = "bow"
    ARROW = "arrow"
    BOW_ARROW = "bow_arrow"

    CRAFTING_TABLE = "crafting_table"

    DIAMOND_SWORD = "diamond_sword"
    DIAMOND_PICKAXE = "diamond_pickaxe"
    DIAMOND_AXE = "diamond_axe"

    WOODEN_SWORD = "wooden_sword"
    WOODEN_PICKAXE = "wooden_pickaxe"
    WOODEN_AXE = "wooden_axe"

    STONE_SWORD = "stone_sword"
    STONE_PICKAXE = "stone_pickaxe"

    IRON_SWORD = "iron_sword"

    GOLDEN_SWORD = "golden_sword"
    PLAYER_HEAD = "player_head"
    PLAYER_BODY = "player_body"
    PLAYER_LEG = "player_leg"
    PLAYER_ARM = "player_arm"
    ZOMBIE_HEAD = "zombie_head"
    ZOMBIE_BODY = "zombie_body"
    ZOMBIE_ARM = "zombie_arm"
    ZOMBIE_LEG = "zombie_leg"
    
    CHIPS = "chips"
    DEFAULT = "default"

class TextureManager:
    def __init__(self, init_directory="resource_pack/"):
        self.default_texture = self.get_default_texture()
        self.textures = {}
        self.init_directory = init_directory

        self.set_resource_pack("Default")
        #self.set_resource_pack("Named - Cosmos")

    def set_resource_pack(self, name):
        self.resource_pack = name + "/"

    def load_default_textures(self):
        """Charge les textures par défaut. Doit être appelé après pygame.display.set_mode()."""
        try:
            # BLOCK
            self.load_texture(TextureType.DIRT, BLOCKS_PATH + "dirt.png")
            self.load_texture(TextureType.STONE, BLOCKS_PATH + "stone.png")
            self.load_texture(TextureType.GRASS, BLOCKS_PATH + "grass_block.png")
            self.load_texture(TextureType.BEDROCK, BLOCKS_PATH + "bedrock.png")
            self.load_texture(TextureType.COAL_ORE, BLOCKS_PATH + "coal_ore.png")
            self.load_texture(TextureType.IRON_ORE, BLOCKS_PATH + "iron_ore.png")
            self.load_texture(TextureType.GOLD_ORE, BLOCKS_PATH + "gold_ore.png")
            self.load_texture(TextureType.SAND, BLOCKS_PATH + "sand.png")
            self.load_texture(TextureType.WATER, BLOCKS_PATH + "water.png")
            self.load_texture(TextureType.OAK_TRUNK, BLOCKS_PATH + "oak_trunk.png")
            self.load_texture(TextureType.OAK_LEAVES, BLOCKS_PATH + "oak_leaves.png")
            self.load_texture(TextureType.CRAFTING_TABLE, BLOCKS_PATH + "crafting_table.png")
            self.load_texture(TextureType.OAK_TRUNK_BOTTOM, BLOCKS_PATH + "oak_trunk_bottom.png")
            self.load_texture(TextureType.OAK_TRUNK_MID, BLOCKS_PATH + "oak_trunk_mid.png")
            self.load_texture(TextureType.SNOW, BLOCKS_PATH + "snow.png")
            self.load_texture(TextureType.STONE_SNOW, BLOCKS_PATH + "stone_snow.png")
            self.load_texture(TextureType.REDSTONE, BLOCKS_PATH + "redstone.png")
            self.load_texture(TextureType.REDSTONE_EMERALD, BLOCKS_PATH + "redstone_emerald.png")
            self.load_texture(TextureType.REDSTONE_SAND, BLOCKS_PATH + "redstone_sand.png")
            self.load_texture(TextureType.OAK_PLANK, BLOCKS_PATH + "oak_plank.png")
            self.load_texture(TextureType.TNT, BLOCKS_PATH + "tnt.png")

            # VARIATIONS 
            self.load_texture(TextureType.GRASS_1, BLOCKS_PATH + "grass1.png")
            self.load_texture(TextureType.GRASS_2, BLOCKS_PATH + "grass2.png")
            self.load_texture(TextureType.GRASS_3, BLOCKS_PATH + "grass3.png")
            self.load_texture(TextureType.GRASS_4, BLOCKS_PATH + "grass4.png")
            self.load_texture(TextureType.GRASS_BROWN, BLOCKS_PATH + "grass_brown.png")
            self.load_texture(TextureType.ROCK, BLOCKS_PATH + "rock.png")
            self.load_texture(TextureType.MUSHROOM, BLOCKS_PATH + "mushroom_red.png")

            # ITEMS
            self.load_texture(TextureType.DIAMOND_SWORD, ITEMS_PATH + TOOLS_PATH + "diamond_sword.png")
            self.load_texture(TextureType.WOODEN_SWORD, ITEMS_PATH + TOOLS_PATH + "wooden_sword.png")
            self.load_texture(TextureType.STONE_SWORD, ITEMS_PATH + TOOLS_PATH + "stone_sword.png")
            self.load_texture(TextureType.IRON_SWORD, ITEMS_PATH + TOOLS_PATH + "iron_sword.png")
            self.load_texture(TextureType.GOLDEN_SWORD, ITEMS_PATH + TOOLS_PATH + "golden_sword.png")

            self.load_texture(TextureType.DIAMOND_PICKAXE, ITEMS_PATH + TOOLS_PATH + "diamond_pickaxe.png")
            self.load_texture(TextureType.WOODEN_PICKAXE, ITEMS_PATH + TOOLS_PATH + "wooden_pickaxe.png")
            self.load_texture(TextureType.STONE_PICKAXE, ITEMS_PATH + TOOLS_PATH + "stone_pickaxe.png")

            self.load_texture(TextureType.DIAMOND_AXE, ITEMS_PATH + TOOLS_PATH + "diamond_axe.png")
            self.load_texture(TextureType.WOODEN_AXE, ITEMS_PATH + TOOLS_PATH + "wooden_axe.png")

            self.load_texture(TextureType.CHIPS, ITEMS_PATH + CONSUMABLE_PATH + "chips.png")
            self.load_texture(TextureType.STICK, ITEMS_PATH + OTHERS_PATH + "stick.png")

            self.load_texture(TextureType.ARROW, ITEMS_PATH + TOOLS_PATH + "arrow.png")
            self.load_texture(TextureType.BOW, ITEMS_PATH + TOOLS_PATH + "bow.png")
            self.load_texture(TextureType.BOW_ARROW, ITEMS_PATH + TOOLS_PATH + "bow_arrow.png")

            # PLAYER
            self.load_texture(TextureType.PLAYER_HEAD, ENTITIES_PATH + PLAYER_PATH + "male/head.png")
            self.load_texture(TextureType.PLAYER_BODY, ENTITIES_PATH + PLAYER_PATH + "male/body.png")
            self.load_texture(TextureType.PLAYER_ARM, ENTITIES_PATH + PLAYER_PATH + "male/arm.png")
            self.load_texture(TextureType.PLAYER_LEG, ENTITIES_PATH + PLAYER_PATH + "male/leg.png")

            # ZOMBIE
            self.load_texture(TextureType.ZOMBIE_HEAD, ENTITIES_PATH + MOBS_PATH + "zombie/head.png")
            self.load_texture(TextureType.ZOMBIE_ARM, ENTITIES_PATH + MOBS_PATH + "zombie/arm.png")
            self.load_texture(TextureType.ZOMBIE_BODY, ENTITIES_PATH + MOBS_PATH + "zombie/body.png")
            self.load_texture(TextureType.ZOMBIE_LEG, ENTITIES_PATH + MOBS_PATH + "zombie/leg.png")

            #
            self.load_texture(TextureType.DEFAULT, "default.png")
        except Exception as e:
            print(f"Erreur lors du chargement des textures: {e}")

        print(self.textures)
    
    def load_texture(self, texture_type, file_path, size=(game_property.TILE_SIZE, game_property.TILE_SIZE)):
        """Charge une texture depuis un fichier."""
        full_path = self.init_directory + self.resource_pack + "texture/" + file_path

        try:
            texture = pygame.image.load(game_property.get_resource_path(full_path)).convert_alpha()
            texture = pygame.transform.scale(texture, size)

            self.textures[texture_type] = texture

        except Exception as e:
            print(f"Erreur texture {texture_type} ({file_path}): {e}")

    def get_texture(self, texture_type):
        if texture_type in self.textures:
            return self.textures[texture_type]
        
        if texture_type == TextureType.NONE:
            return None

        return self.default_texture
    
    def get_default_texture(self):
        surface = pygame.Surface((game_property.TILE_SIZE, game_property.TILE_SIZE))

        tile = game_property.TILE_SIZE
        half = tile // 2

        pink = (255, 0, 255)
        black = (0, 0, 0)

        # 4 carrés
        pygame.draw.rect(surface, pink,  (0, 0, half, half))
        pygame.draw.rect(surface, black, (half, 0, half, half))
        pygame.draw.rect(surface, black, (0, half, half, half))
        pygame.draw.rect(surface, pink,  (half, half, half, half))

        return surface