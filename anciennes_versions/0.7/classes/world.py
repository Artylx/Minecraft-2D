import pygame

from classes.player import Player

class World:
    def __init__(self, seed, name="Unnamed World", render_distance=3, chunk_size=16, HEIGHT_SCREEN=1200, WIDTH_SCREEN=1600):
        self.seed = seed
        self.name = name
        self.render_distance = render_distance
        self.chunk_size = chunk_size
        self.HEIGHT_CHUNK = 32

        self.HEIGHT_SCREEN = HEIGHT_SCREEN
        self.WIDTH_SCREEN = WIDTH_SCREEN

        self.tile_size = 32

        self.cam_x = 0
        self.cam_y = 0

        self.chunks = {}
        self.add_chunk(0)
        self.update_chunks()

        self.player = Player(rect=(0, 0, self.tile_size - 10, (self.tile_size * 1.5) - 10), name="Player")
        # Spawn player above the ground
        self.player.y = 10

    def __str__(self):
        return f"World: {self.name}"
    
    def add_chunk(self, chunk_x):
        chunk = Chunk(chunk_x, self.chunk_size, self.HEIGHT_CHUNK)
        self.chunks[chunk_x] = chunk
        return chunk

    def draw(self, screen):
        # Placeholder for drawing the world
        screen.fill((135, 206, 235))  # Fill the screen with a blue color

        for chunk in self.chunks.values():
            chunk.draw(screen, self.tile_size, self.cam_x, self.cam_y)

        # passer l'offset de la caméra au joueur
        self.player.draw(screen, self.tile_size, self.cam_x, self.cam_y)

        screen.blit(pygame.font.SysFont(None, 24).render(f"Pos player: {self.player.x}, {self.player.y}, on_ground: {self.player.on_ground}", True, (0, 0, 0)), (10, 10))

    def check_collisions_y(self, rect, new_pos):
        # Check if moving to new_pos causes collision on Y axis
        # Only check blocks BELOW the entity (for gravity)
        entity_x = new_pos[0]
        entity_y = new_pos[1]
        entity_width = rect[2] / self.tile_size  # Convert pixels to tiles
        entity_height = rect[3] / self.tile_size  # Convert pixels to tiles

        # Get the block tiles at the bottom of the entity
        tile_left = int(entity_x)
        tile_right = int(entity_x + entity_width)
        # Check blocks just below the entity
        tile_below = int(entity_y) - 1
        
        # Check all blocks directly below the entity
        for x in range(tile_left, tile_right + 1):
            chunk_x = x // self.chunk_size
            block_x = x % self.chunk_size
            y = tile_below
            
            if chunk_x not in self.chunks:
                continue
            
            chunk = self.chunks[chunk_x]
            if 0 <= block_x < chunk.WIDTH_CHUNK and 0 <= y < chunk.HEIGHT_CHUNK:
                block = chunk.blocks[block_x][y]
                if block is not None and block.block_type != BlockType.AIR:
                    return True  # Collision detected with ground
        
        return False
    
    def check_collisions_x(self, rect, new_pos):
        # Check if moving to new_pos causes collision on X axis
        entity_x = new_pos[0]
        entity_y = new_pos[1]
        entity_width = rect[2] / self.tile_size  # Convert pixels to tiles
        entity_height = rect[3] / self.tile_size  # Convert pixels to tiles
        
        # Get the block tiles the entity occupies vertically
        tile_top = int(entity_y)
        tile_bottom = int(entity_y + entity_height)
        
        # Check blocks at the sides depending on direction
        tile_left = int(entity_x)
        tile_right = int(entity_x + entity_width)
        
        # Check all blocks in the entity's horizontal path
        for y in range(tile_top, tile_bottom + 1):
            for x in range(tile_left, tile_right + 1):
                chunk_x = x // self.chunk_size
                block_x = x % self.chunk_size
                
                if chunk_x not in self.chunks:
                    continue
                
                chunk = self.chunks[chunk_x]
                if 0 <= block_x < chunk.WIDTH_CHUNK and 0 <= y < chunk.HEIGHT_CHUNK:
                    block = chunk.blocks[block_x][y]
                    if block is not None and block.block_type != BlockType.AIR:
                        return True  # Collision detected
        
        return False

    def move_cam(self, x, y):
        self.cam_x += x
        self.cam_y += y

        self.update_chunks()
        print(f"Camera moved to ({self.cam_x}, {self.cam_y})")

    def move_player(self, direction_x, direction_y):
        # When controls give a desired offset, apply to position directly
        self.player.set_direction(direction_x, direction_y)
        
    def update(self, dt):
        # update player first
        self.player.apply_gravity(dt)
        self.player.update(dt, self)

        # recalc camera based on updated player position
        self.cam_x = -self.player.x * self.tile_size + self.WIDTH_SCREEN // 2
        self.cam_y = self.player.y * self.tile_size + self.HEIGHT_SCREEN // 2

        self.update_chunks()

    def update_chunks(self):
        # Calculer le chunk actuel basé sur la position de la caméra
        cam_chunk_x = -(self.cam_x // (self.tile_size * self.chunk_size))
        
        # Charger les chunks dans le render_distance sur l'axe X uniquement
        chunks_to_unload = set(self.chunks.keys())
        
        for dx in range(-self.render_distance, self.render_distance + 1):
            chunk_x = cam_chunk_x + dx
            chunk_coords = chunk_x
            
            if chunk_coords not in self.chunks:
                self.add_chunk(chunk_x)
            
            chunks_to_unload.discard(chunk_coords)
        
        # Décharger les chunks trop loin
        for chunk_coords in chunks_to_unload:
            del self.chunks[chunk_coords]

class Chunk:
    def __init__(self, chunk_x, chunk_size=16, height_chunk=10):
        self.HEIGHT_CHUNK = height_chunk
        self.WIDTH_CHUNK = chunk_size

        self.chunk_x = chunk_x
        self.blocks = [[None for _ in range(self.HEIGHT_CHUNK)] for _ in range(self.WIDTH_CHUNK)]

        self.load_blocks()
        
    def __str__(self):
        return f"Chunk: ({self.chunk_x}), with {self.WIDTH_CHUNK}x{self.HEIGHT_CHUNK} blocks, total {sum(1 for row in self.blocks for block in row if block is not None)}"
    
    def add_block(self, block_x, block_y, block_type):
        self.blocks[block_x][block_y] = Block(block_type)

    def load_blocks(self):
        for x in range(self.WIDTH_CHUNK):
            for y in range(self.HEIGHT_CHUNK):
                if (y < self.HEIGHT_CHUNK // 2):
                    if (x == 0):
                        self.add_block(x, y, BlockType.STONE)
                        continue
                    self.add_block(x, y, BlockType.DIRT)
                else:
                    self.add_block(x, y, BlockType.AIR)
    
    def draw(self, screen, tile_size, cam_x, cam_y):
        for x in range(self.WIDTH_CHUNK):
            for y in range(self.HEIGHT_CHUNK):
                block = self.blocks[x][y]
                if block is None:
                    continue
                
                # Position globale du bloc dans le monde
                world_x = (self.chunk_x * self.WIDTH_CHUNK + x) * tile_size + cam_x
                world_y = (self.HEIGHT_CHUNK - 1 - y) * tile_size + cam_y
                
                block.draw(screen, world_x, world_y, tile_size)

class Block:
    texture_manager = None  # Sera initialisé globalement
    
    def __init__(self, block_type):
        self.block_type = block_type

    def __str__(self):
        return f"Block: {self.block_type}"
    
    def draw(self, screen, x, y, tile_size):
        if self.block_type == BlockType.AIR:
            return  # Les blocs air ne sont pas affichés
        
        if Block.texture_manager is None:
            # Fallback si TextureManager n'est pas initialisé
            pygame.draw.rect(screen, (139, 69, 19), (x, y, tile_size, tile_size))
            return
        
        texture = Block.texture_manager.get_texture(self.block_type)
        if texture:
            # Redimensionner la texture à la taille du tile
            scaled_texture = pygame.transform.scale(texture, (tile_size, tile_size))
            screen.blit(scaled_texture, (x, y))
        else:
            # Fallback avec couleur si texture non disponible
            pygame.draw.rect(screen, (139, 69, 19), (x, y, tile_size, tile_size))

class BlockType:
    DIRT = "dirt"
    AIR = "air"
    STONE = "stone"

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


# Initialisation du TextureManager (chargement des textures se fera dans Game.__init__)
texture_manager = TextureManager()
Block.texture_manager = texture_manager