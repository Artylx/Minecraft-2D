import pygame
from classes import game_property

BLOCKS_PATH = "blocks/"
ITEMS_PATH = "items/"
TOOLS_PATH = "tools/"
CONSUMABLE_PATH = "consumable/"
ENTITIES_PATH = "entities/"
MOBS_PATH = "mobs/"
PLAYER_PATH = "player/"

class TextureType:
    NONE = ""
    DIRT = "dirt"
    STONE = "stone"
    GRASS = "grass"
    BEDROCK = "bedrock"
    COAL = "coal"
    IRON = "iron"
    GOLD = "gold"
    SAND = "sand"
    WATER = "water"
    DIAMOND_SWORD = "diamond_sword"
    PLAYER_HEAD = "player_head"
    PLAYER_BODY = "player_body"
    PLAYER_LEG = "player_leg"
    PLAYER_ARM = "player_arm"
    ZOMBIE_HEAD = "zombie_head"
    ZOMBIE_BODY = "zombie_body"
    ZOMBIE_ARM = "zombie_arm"
    ZOMBIE_LEG = "zombie_leg"
    DIAMOND_PICKAXE = "diamond_pickaxe"
    CHIPS = "chips"

class TextureManager:
    def __init__(self, init_directory="textures/"):
        self.textures = {}
        self.init_directory = init_directory

    def load_default_textures(self):
        """Charge les textures par défaut. Doit être appelé après pygame.display.set_mode()."""
        try:
            # BLOCK
            self.load_texture(TextureType.DIRT, BLOCKS_PATH + "dirt.png")
            self.load_texture(TextureType.STONE, BLOCKS_PATH + "stone.png")
            self.load_texture(TextureType.GRASS, BLOCKS_PATH + "grass_block.png")
            self.load_texture(TextureType.BEDROCK, BLOCKS_PATH + "bedrock.png")
            self.load_texture(TextureType.COAL, BLOCKS_PATH + "coal_ore.png")
            self.load_texture(TextureType.IRON, BLOCKS_PATH + "iron_ore.png")
            self.load_texture(TextureType.GOLD, BLOCKS_PATH + "gold_ore.png")
            self.load_texture(TextureType.SAND, BLOCKS_PATH + "sand.png")
            self.load_texture(TextureType.WATER, BLOCKS_PATH + "water.png")

            # ITEMS
            self.load_texture(TextureType.DIAMOND_SWORD, ITEMS_PATH + TOOLS_PATH + "diamond_sword.png")
            self.load_texture(TextureType.DIAMOND_PICKAXE, ITEMS_PATH + TOOLS_PATH + "diamond_pickaxe.png")

            self.load_texture(TextureType.CHIPS, ITEMS_PATH + CONSUMABLE_PATH + "chips.png")

            # PLAYER
            self.load_texture(TextureType.PLAYER_HEAD, ENTITIES_PATH + PLAYER_PATH + "head.png")
            self.load_texture(TextureType.PLAYER_BODY, ENTITIES_PATH + PLAYER_PATH + "body.png")
            self.load_texture(TextureType.PLAYER_ARM, ENTITIES_PATH + PLAYER_PATH + "arm.png")
            self.load_texture(TextureType.PLAYER_LEG, ENTITIES_PATH + PLAYER_PATH + "leg.png")

            # ZOMBIE
            self.load_texture(TextureType.ZOMBIE_HEAD, ENTITIES_PATH + MOBS_PATH + "zombie/head.png")
            self.load_texture(TextureType.ZOMBIE_ARM, ENTITIES_PATH + MOBS_PATH + "zombie/arm.png")
            self.load_texture(TextureType.ZOMBIE_BODY, ENTITIES_PATH + MOBS_PATH + "zombie/body.png")
            self.load_texture(TextureType.ZOMBIE_LEG, ENTITIES_PATH + MOBS_PATH + "zombie/leg.png")
        except Exception as e:
            print(f"Erreur lors du chargement des textures: {e}")
    
    def load_texture(self, texture_type, file_path, size=(game_property.TILE_SIZE, game_property.TILE_SIZE)):
        """Charge une texture depuis un fichier."""
        full_path = self.init_directory + file_path

        try:
            texture = pygame.image.load(self.get_resource_path(full_path)).convert_alpha()
            texture = pygame.transform.scale(texture, size)

            self.textures[texture_type] = texture

        except Exception as e:
            print(f"Erreur texture {texture_type} ({file_path}): {e}")

    def get_texture(self, texture_type):
        if texture_type in self.textures:
            return self.textures[texture_type]

        # fallback visuel (important pour debug)
        print(f"Texture manquante: {texture_type}")

        surface = pygame.Surface((game_property.TILE_SIZE, game_property.TILE_SIZE))
        surface.fill((255, 0, 255))  # rose debug

        return surface