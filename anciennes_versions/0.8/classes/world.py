import pygame
import terrakit.game_property as game_property

class World:
    def __init__(self, seed, name, width=800, height=600):
        self.seed = seed
        self.name = name

        # camera rectangle is stored in world coordinates (origin bottom-left)
        # its x,y represent the bottom-left corner of the visible area
        self.cam_rect = pygame.Rect(0, 0, width, height)
        self.current_chunk_x = 0

        self.init()

    def init(self):
        self.chunks = {}

        self.generate_chunks()
        pass

    def generate_chunks(self):
        for i in range(-game_property.RENDER_DISTANCE, game_property.RENDER_DISTANCE + 1):
            self.add_chunk(i)

    def add_chunk(self, chunk_x):
        if chunk_x not in self.chunks:
            self.chunks[chunk_x] = Chunk(chunk_x)

    def update_chunks(self):
        # Calculer le chunk actuel basé sur la position de la caméra
        cam_chunk_x = (self.cam_rect.x + self.cam_rect.width // 2) // (game_property.TILE_SIZE * game_property.CHUNK_WIDTH)
        
        # Charger les chunks dans le render_distance sur l'axe X uniquement
        chunks_to_unload = set(self.chunks.keys())
        
        for dx in range(-game_property.RENDER_DISTANCE, game_property.RENDER_DISTANCE + 1):
            chunk_x = cam_chunk_x + dx
            chunk_coords = chunk_x
            
            if chunk_coords not in self.chunks:
                self.add_chunk(chunk_x)
            
            chunks_to_unload.discard(chunk_coords)
        
        # Décharger les chunks trop loin
        for chunk_coords in chunks_to_unload:
            del self.chunks[chunk_coords]

    def unload_chunks(self):
        pass

    def update(self, dt):
        
        
        self.update_chunks()

    def render(self, screen):
        # draw every chunk (blocks handle their own visibility)
        for chunk in self.chunks.values():
            chunk.draw(screen, self.cam_rect)


    def world_to_screen(self, rect: pygame.Rect) -> pygame.Rect:
        """Convert a world-space rectangle (y up) into pygame screen coords (y down).
        The returned rect is relative to the top-left of the window (0,0).
        """
        # x translation is straightforward
        screen_x = rect.x - self.cam_rect.x
        # compute y from bottom: camera origin is bottom-left
        # world y increases up; screen y increases down
        screen_y = self.cam_rect.height - (rect.y - self.cam_rect.y) - rect.height
        return pygame.Rect(screen_x, screen_y, rect.width, rect.height)

    def rect_in_camera(self, rect: pygame.Rect) -> bool:
        """Return True if the world-space rect is (at least partially) visible in the camera."""
        screen_rect = self.world_to_screen(rect)
        return screen_rect.colliderect(pygame.Rect(0, 0, self.cam_rect.width, self.cam_rect.height))

    def move_camera(self, direction_x, direction_y, dt):
        # directions are given in logical world coordinates
        if direction_x == "right":
            dx = 1
        elif direction_x == "left":
            dx = -1
        else:
            dx = 0

        # y movement positive = up in world space
        if direction_y == "down":
            dy = -1
        elif direction_y == "up":
            dy = 1
        else:
            dy = 0

        self.cam_rect.x += dx * 100 * dt
        self.cam_rect.y += dy * 100 * dt

        # prevent camera from going below the world origin
        if self.cam_rect.x < 0:
            self.cam_rect.x = 0
        if self.cam_rect.y < 0:
            self.cam_rect.y = 0


class Chunk:
    def __init__(self, x):
        self.x = x
        self.blocks = []
        
        self.generate_blocks()

    def draw(self, screen, cam_rect):
        for block in self.blocks:
            block.draw(screen, cam_rect)

    def generate_blocks(self):
        for x in range(game_property.CHUNK_WIDTH):
            for y in range(game_property.CHUNK_HEIGHT):
                block_x = self.x * game_property.CHUNK_WIDTH + x
                block_y = y
                block_rect = pygame.Rect(block_x * game_property.TILE_SIZE, block_y * game_property.TILE_SIZE, game_property.TILE_SIZE, game_property.TILE_SIZE)
                if block_y > game_property.CHUNK_HEIGHT // 2:
                    block_type = BlockType.DIRT
                else:
                    block_type = BlockType.STONE

                block = Block(block_type, block_rect)
                self.blocks.append(block)
        pass

class BlockType:
    DIRT = ("dirt", 0)
    AIR = ("air", 1)
    STONE = ("stone", 2)

class TextureType:
    DIRT = "dirt"
    STONE = "stone"


class TextureManager:
    def __init__(self, init_directory="textures/"):
        self.textures = {}
        self.init_directory = init_directory

    def load_default_textures(self):
        """Charge les textures par défaut. Doit être appelé après pygame.display.set_mode()."""
        try:
            self.load_texture(TextureType.DIRT, "blocks/dirt.png")
            self.load_texture(TextureType.STONE, "blocks/stone.png")
        except Exception as e:
            print(f"Erreur lors du chargement des textures: {e}")
    
    def load_texture(self, texture_type, file_path):
        """Charge une texture depuis un fichier."""
        full_path = self.init_directory + file_path
        texture = pygame.image.load(get_resource_path(full_path)).convert_alpha()
        self.textures[texture_type] = texture
        print(f"Texture chargée: {texture_type}")

    def get_texture(self, texture_type):
        """Retourne la texture ou None si non disponible."""
        return self.textures.get(texture_type, None)


from pathlib import Path
import sys

def get_resource_path(relative_path):
    """Retourne le chemin absolu de la ressource embarquée ou locale."""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent.parent / relative_path


class Block:
    texture_manager = TextureManager()

    def __init__(self, block_type, rect, can_collide=True):
        self.block_type = block_type
        self.rect = rect
        self.can_collide = can_collide

    def draw(self, screen, cam_rect):
        """Render block accounting for inverted Y axis and camera position.
        The block rectangle is defined in world coordinates where y=0 is bottom.
        """
        # convert world coords -> screen coords
        screen_x = self.rect.x - cam_rect.x
        screen_y = cam_rect.height - (self.rect.y - cam_rect.y) - self.rect.height
        screen_rect = pygame.Rect(screen_x, screen_y, self.rect.width, self.rect.height)

        # if not visible on screen, nothing to draw
        if not screen_rect.colliderect(pygame.Rect(0, 0, cam_rect.width, cam_rect.height)):
            return

        # try to draw texture if available
        if self.block_type[0] == TextureType.DIRT:
            texture = self.texture_manager.get_texture(TextureType.DIRT)
            if texture:
                scaled = pygame.transform.scale(texture, (game_property.TILE_SIZE, game_property.TILE_SIZE))
                screen.blit(scaled, screen_rect)
                return
        elif self.block_type[0] == TextureType.STONE:
            texture = self.texture_manager.get_texture(TextureType.STONE)
            if texture:
                scaled = pygame.transform.scale(texture, (game_property.TILE_SIZE, game_property.TILE_SIZE))
                screen.blit(scaled, screen_rect)
                return

        # fallback if no texture or unknown type
        pygame.draw.rect(screen, (255, 0, 0), screen_rect)