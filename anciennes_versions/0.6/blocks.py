import pygame

class Blocks:
    def __init__(self, GameProperty):
        self.GameProperty = GameProperty
        self.BLOCKS = {
            "air": 0,
            "grass_block": 1,
            "dirt": 2,
            "stone": 3,
            "bedrock": 4,
            "iron_ore": 5,
            "coal_ore": 6,
            "gold_ore": 7
        }

        self.ID_TO_NAME = {v: k for k, v in self.BLOCKS.items()}

        self.textures = {
            self.BLOCKS["grass_block"]: pygame.transform.scale(pygame.image.load("textures/blocks/grass_block.png").convert_alpha(), (self.GameProperty.TILE_SIZE, self.GameProperty.TILE_SIZE)),
            self.BLOCKS["dirt"]: pygame.transform.scale(pygame.image.load("textures/blocks/dirt.png").convert_alpha(), (self.GameProperty.TILE_SIZE, self.GameProperty.TILE_SIZE)),
            self.BLOCKS["stone"]: pygame.transform.scale(pygame.image.load("textures/blocks/stone.png").convert_alpha(), (self.GameProperty.TILE_SIZE, self.GameProperty.TILE_SIZE)),
            self.BLOCKS["bedrock"]: pygame.transform.scale(pygame.image.load("textures/blocks/bedrock.png").convert_alpha(), (self.GameProperty.TILE_SIZE, self.GameProperty.TILE_SIZE)),
            self.BLOCKS["iron_ore"]: pygame.transform.scale(pygame.image.load("textures/blocks/iron_ore.png").convert_alpha(), (self.GameProperty.TILE_SIZE, self.GameProperty.TILE_SIZE)),
            self.BLOCKS["coal_ore"]: pygame.transform.scale(pygame.image.load("textures/blocks/coal_ore.png").convert_alpha(), (self.GameProperty.TILE_SIZE, self.GameProperty.TILE_SIZE)),
            self.BLOCKS["gold_ore"]: pygame.transform.scale(pygame.image.load("textures/blocks/gold_ore.png").convert_alpha(), (self.GameProperty.TILE_SIZE, self.GameProperty.TILE_SIZE)),
        }

    def get_number(self, name):
        """Retourne l'ID d'un bloc à partir de son nom."""
        return self.BLOCKS.get(name)

    def get_name(self, number):
        """Retourne le nom d'un bloc à partir de son ID."""
        return self.ID_TO_NAME.get(number)

    def get_texture(self, number):
        """Retourne la texture associée à un ID de bloc."""
        return self.textures.get(number)
    
class Block:
    def __init__(self, blocks, number, tile_size, x=None, y=None, Collision=True):
        self.number = number
        self.name = blocks.get_name(number)
        self.texture = blocks.get_texture(number)
        self.number_x = x
        self.number_y = y
        self.Collision = Collision
        self.tile_size = tile_size

    def get_rect(self):
        """Retourne un pygame.Rect en pixels basé sur la position en tuiles."""
        return pygame.Rect(
            self.number_x * self.tile_size,
            self.number_y * self.tile_size,
            self.tile_size,
            self.tile_size
        )
    
    def draw(self, screen, screen_x=0, screen_y=0):
        """Dessine le bloc à l'écran en tenant compte de la caméra."""
        info = pygame.display.Info()
        HEIGHT = info.current_h

        rect = self.get_rect()
        draw_pos = (screen_x, screen_y)
        if self.texture:
            screen.blit(self.texture, draw_pos)
        outline_rect = pygame.Rect(draw_pos[0], draw_pos[1], rect.width, rect.height)
        pygame.draw.rect(screen, (0, 0, 0), outline_rect, 1)