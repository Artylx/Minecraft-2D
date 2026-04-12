import pygame
from noise import pnoise1, pnoise2
from classes import inventory
from classes import entity as EntityClass, game_property, game_type
import random
from classes import entity
from classes.struct import StructureManager, StructureType
from classes.game_type import BlockProperty
import json
import os
from classes.biome import BiomeType, BiomeManager
from collections import deque

def load_world_json(world_name):
    """
    Charge le fichier JSON d'un monde à partir de son nom.

    :param world_name: Nom du monde (str)
    :return: dictionnaire Python avec les données du monde ou None si erreur
    """
    # construire le chemin du fichier
    world_path = os.path.join("worlds", f"{world_name}.json")

    if not os.path.isfile(world_path):
        print(f"Le monde '{world_name}' n'existe pas à {world_path}")
        return None

    try:
        with open(world_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Erreur lors du chargement du monde '{world_name}': {e}")
        return None

class World:
    def __init__(self, screen_size, name="Unamed world", seed=None, json_data=None):
        """
        Constructeur unique qui gère soit :
        - la génération d'un monde depuis une seed
        - la reconstruction d'un monde depuis un JSON
        """
        self.screen_size = screen_size
        self.name = name

        if json_data is not None:
            # charger depuis le JSON
            self.set_json(json_data)
        else:
            # générer depuis la seed
            self.seed = seed if seed is not None else random.randint(0, 100000)
            self.random = random.Random(self.seed)

            self.entitys = []  
            self.modified_blocks = {}  
        
        self.structure_manager = StructureManager()
        self.biome_manager = BiomeManager()

        # initialisation commune
        self.init()
        
    def init(self):
        self.hit_box_visible = False

        self.chunks = {}
        

    def save_world(self):
        with open(f"worlds/{self.name}.json", "w") as f:
            json.dump(self.get_json(), f, indent=4, default=str)
        print("Save world in ", f"{self.name}.json")

    def set_json(self, json):
        seed = json.get("seed", None)
        entitys = json.get("entitys", None)
        modified_blocks = json.get("modified_blocks", None)

        if seed is not None and entitys is not None and modified_blocks is not None:
            self.seed = seed
            #print(f"World load with seed: {seed}")
            self.entitys = entity.dict_to_entitys(entitys, self)
            #print(f"World load with entitys: {entitys}")
            self.modified_blocks = modified_blocks
            #print(f"World load with modif_block: {modified_blocks}")

            print("World chargé avec succés")
        else:
            print("World non recevable")
            exit(1)
    
    def get_json(self):
        return {
            "seed": self.seed,
            "entitys": [e.to_json() for e in self.entitys],
            "modified_blocks": self.modified_blocks
        }
    
    def create_entity(self, entity):
        self.entitys.append(entity)

    def add_chunk(self, chunk_x):
        import time
        if chunk_x not in self.chunks:
            
            start = time.time()
            chunk = Chunk(chunk_x, self.seed, self.structure_manager, self.biome_manager)
            print("Chunk gen time:", time.time() - start)
            self.chunks[chunk_x] = chunk

            # appliquer les modifications sauvegardées
            if str(chunk_x) in self.modified_blocks:

                for data in self.modified_blocks[str(chunk_x)]:

                    x = data["x"]
                    y = data["y"]

                    block_name = data["block"].upper()

                    if block_name not in BlockProperty.REGISTRY:
                        raise ValueError(f"Block inconnu: {block_name}")

                    block_type = BlockProperty.REGISTRY[block_name]

                    chunk.set_block(x, y, Block(x, y, block_type))

    def update_chunks(self):
        chunks_to_keep = set()
        player_chunks = []

        chunk_size = game_property.TILE_SIZE * game_property.CHUNK_WIDTH

        for player_ in self.get_entities(EntityClass.Player):
            chunk_x = player_.get_pos()[0] // chunk_size
            player_chunks.append(chunk_x)

            for dx in range(-game_property.PRELOAD_DISTANCE, game_property.PRELOAD_DISTANCE + 1):
                chunks_to_keep.add(chunk_x + dx)

        def distance(cx):
            if not player_chunks:
                return 0
            return min(abs(cx - px) for px in player_chunks)

        sorted_chunks = sorted(chunks_to_keep, key=distance)

        chunks_to_unload = set(self.chunks.keys())

        for chunk_x in sorted_chunks:
            chunks_to_unload.discard(chunk_x)

            if chunk_x not in self.chunks:
                self.add_chunk(chunk_x)
                break

        for chunk_coords in chunks_to_unload:
            self.unload_chunk(chunk_coords)

    def unload_chunk(self, chunk_cord):

        # supprimer les entités dans ce chunk
        to_remove = []

        for entity in self.entitys:

            entity_chunk_x = entity.rect.x // (game_property.TILE_SIZE * game_property.CHUNK_WIDTH)

            if entity_chunk_x == chunk_cord:
                to_remove.append(entity)

        for entity in to_remove:
            self.entitys.remove(entity)

        # supprimer le chunk
        del self.chunks[chunk_cord]

    def update(self, dt):
        self.update_chunks()

        to_remove = []

        for entity in self.get_entities():
            entity.update(dt, self)

            if not entity.is_alive:
                to_remove.append(entity)
                continue

            # si c'est un block item et qu'il touche le joueur
            if isinstance(entity, EntityClass.Item):
                for player in self.get_players():
                    if entity.rect.colliderect(player.rect):

                        to_remove.append(entity)

                        player.inventory.add_item(
                            inventory.ItemStack(entity.item_type, 1)
                        )
            else:
                entity_chunk_x = entity.rect.x // (game_property.TILE_SIZE * game_property.CHUNK_WIDTH)

                # si le chunk n'est plus chargé → suppression
                if entity_chunk_x not in self.chunks:
                    to_remove.append(entity)
                    continue

        # suppression des entités ramassées
        for entity in to_remove:
            self.entitys.remove(entity)

    def render_debug(self, screen):
        font = pygame.font.SysFont(None, 24)

        debug_text = f"Chunks loaded: {len(self.chunks.values())}, {list(self.chunks.keys())}"
        text_surface = font.render(debug_text, True, (0, 0, 0))
        screen.blit(text_surface, (10, 70))

        debug_text = f"Entitys: {len(self.entitys)}"
        text_surface = font.render(debug_text, True, (0, 0, 0))
        screen.blit(text_surface, (10, 90))

        # pygame.draw.rect(screen, (0, 255, 0), (self.screen_size[0] // 2 - 1, 0, 2, self.screen_size[1]))
        # pygame.draw.rect(screen, (0, 255, 0), (0, self.screen_size[1] // 2 - 1, self.screen_size[0], 2))
        pass

    def render(self, screen, cam_rect):
        tile = game_property.TILE_SIZE

        start_x = cam_rect.left // tile
        end_x = cam_rect.right // tile + 1

        start_y = cam_rect.top // tile
        end_y = cam_rect.bottom // tile + 1

        for x in range(start_x, end_x):
            chunk_x = x // game_property.CHUNK_WIDTH

            if chunk_x not in self.chunks:
                continue

            chunk = self.chunks[chunk_x]

            for y in range(start_y, end_y):

                block = chunk.blocks.get((x, y))

                if block:
                    block.render(screen, cam_rect)

    def render_entitys(self, screen, cam_rect):
        for entity in self.entitys:
            entity.render(screen, cam_rect)
            if self.hit_box_visible:
                entity.render_hit_box(screen, cam_rect)
    
    def get_block(self, X, Y):
        chunk_x = X // game_property.CHUNK_WIDTH

        if chunk_x not in self.chunks:
            return None

        chunk = self.chunks[chunk_x]

        return chunk.blocks.get((X, Y))
    
    def set_block(self, X, Y, block):
        # calcul du chunk
        chunk_x = X // game_property.CHUNK_WIDTH
        if chunk_x not in self.chunks:
            return False

        # créer le rectangle du bloc à placer
        block_rect = pygame.Rect(
            X * game_property.TILE_SIZE,
            Y * game_property.TILE_SIZE,
            game_property.TILE_SIZE,
            game_property.TILE_SIZE
        )

        # vérification collision avec toutes les entités
        if block.block_property != BlockProperty.AIR and block.can_collide():
            for entity in self.entitys:
                if block_rect.colliderect(entity.rect):
                    # on refuse de placer le bloc
                    print(f"Impossible de placer {block.block_property.block_name} à {(X,Y)}: collision avec {entity.name}")
                    return False

        # placement du bloc si pas de collision
        chunk = self.chunks[chunk_x]

        chunk.set_block(X, Y, block)

        if str(chunk_x) not in self.modified_blocks:
            self.modified_blocks[str(chunk_x)] = []

        self.modified_blocks[str(chunk_x)].append({
            "x": X,
            "y": Y,
            "block": block.block_property.block_name
        })
        return True

    def is_collide(self, entity):
        return self.is_collide_at(entity.rect)


    def is_collide_at(self, rect):
        """Teste si un rect collide avec les blocs solides"""

        tile = game_property.TILE_SIZE

        # coordonnées des tuiles couvertes par le rect
        start_x = rect.left // tile
        end_x = rect.right // tile

        start_y = rect.top // tile
        end_y = rect.bottom // tile

        for x in range(start_x, end_x + 1):

            chunk_x = x // game_property.CHUNK_WIDTH

            chunk = self.chunks.get(chunk_x)
            if not chunk:
                continue

            for y in range(start_y, end_y + 1):

                block = chunk.blocks.get((x, y))

                if block and block.can_collide():
                    return True

        return False
    
    def destroy_block(self, block_pos, player):
        current_block = self.get_block(block_pos[0], block_pos[1])
        x = block_pos[0]
        y = block_pos[1]

        self.set_block(
            block_pos[0],
            block_pos[1],
            Block(
                x,
                y,
                block_property=BlockProperty.AIR
            )
        )

        item = player.get_selected_item()

        if not item:
            item_pro = None
        else:
            item_pro = item.item_property
        if current_block.block_property.can_drop(item_pro):

            if game_type.get_item_type_by_name(current_block.block_property.item_type) is not None:
                x = x * game_property.TILE_SIZE
                y = y * game_property.TILE_SIZE

                r = random.Random()
                pos = (x + r.randint(0, game_property.SIZE_ITEM - 1), y + r.randint(0, game_property.SIZE_ITEM))

                block_entity = EntityClass.Item(self, game_type.get_item_type_by_name(current_block.block_property.item_type), pos)
                self.create_entity(block_entity)
    
    def try_destroy_block(self, block_pos, player):
        current_block = self.get_block(block_pos[0], block_pos[1])
        if not current_block or not current_block.is_breackable():
            return

        # position centre du bloc
        block_center_x = block_pos[0] * game_property.TILE_SIZE + game_property.TILE_SIZE / 2
        block_center_y = block_pos[1] * game_property.TILE_SIZE + game_property.TILE_SIZE / 2

        # position centre joueur
        player_center_x = player.rect.centerx
        player_center_y = player.rect.centery

        dx = block_center_x - player_center_x
        dy = block_center_y - player_center_y

        distance = (dx*dx + dy*dy) ** 0.5

        if distance > game_property.MAX_ACTION_DISTANCE:
            return
        
        current_block.try_destroy(player.get_force_selected_item(current_block.block_property))
        if current_block.life < 0:
            self.destroy_block(block_pos, player)
    
    def reset_block(self, block_pos):
        current_block = self.get_block(block_pos[0], block_pos[1])
        if not current_block or not current_block.is_breackable():
            return
        
        current_block.life = current_block.max_life

    def attack(self, player, entities):
        pass

    def get_player_by_name(self, player_name):
        for current_entity in self.entitys:
            if current_entity and isinstance(current_entity, EntityClass.Player):
                if current_entity.name == player_name:
                    return current_entity
        return None

    def get_player(self, uuid):
        for current_entity in self.entitys:
            if current_entity and isinstance(current_entity, EntityClass.Player):
                if current_entity.get_uuid() == uuid:
                    return current_entity
        return None
    
    def get_entities(self, class_=None) -> list:
        if class_ is None:
            return self.entitys

        if not isinstance(class_, type):
            raise TypeError("class_ doit être une classe")

        return [e for e in self.entitys if isinstance(e, class_)]
    
    def get_entities_by_pos(self, pos):
        x, y = pos
        result = []

        for e in self.entitys:
            if e is None:
                continue

            # Vérifie si l'entité est dans la case
            if e.rect.collidepoint(x, y):
                result.append(e)

        return result
    
    def get_entities_by_rect(self, rect):
        result = []

        for e in self.entitys:
            if e is None:
                continue

            if e.rect.colliderect(rect):
                result.append(e)

        return result
    
    def get_players(self):
        return self.get_entities(entity.Player)


class Chunk:
    def __init__(self, x, seed, structure_manager, biome_manager):
        self.x = x
        self.seed = abs(hash(seed)) % 1024
        self.structure_manager = structure_manager
        self.biome_manager = biome_manager

        self.blocks = {}
        self.structures = []
        self.generate()
        self.update_light()

    # def generate(self):
    #     for x in range(game_property.CHUNK_WIDTH):
    #         for y in range(game_property.CHUNK_MIN_HEIGHT, game_property.CHUNK_MAX_HEIGHT):
    #             block_x = self.x * game_property.CHUNK_WIDTH + x
    #             block_y = y
    #             block_rect = pygame.Rect(block_x * game_property.TILE_SIZE, block_y * game_property.TILE_SIZE, game_property.TILE_SIZE, game_property.TILE_SIZE)

    #             if block_y < game_property.CHUNK_MAX_HEIGHT // 2:
    #                 block_property = BlockProperty.STONE
    #             else:
    #                 block_property = BlockProperty.DIRT

    #             # if x == 0:
    #             #     block_property = BlockProperty.AIR
    #             block = Block(block_rect, block_property)
    #             self.blocks.append(block)

    def add_structure(self, struct_type: StructureType, base_x, base_y):
        self.structures.append((struct_type, base_x, base_y))

    def generate_structures(self):
        for struct_type, base_x, base_y in self.structures:
            self.structure_manager.place_structure(self, struct_type, base_x, base_y)

    def generate(self):
        terrain_scale = 0.01

        sea_level = game_property.WATER_Y

        for x in range(game_property.CHUNK_WIDTH):
            world_x = self.x * game_property.CHUNK_WIDTH + x

            biome, amplitude, base_height = self.biome_manager.get_biome_generate_values(world_x, self.seed)

            # 🌊 variation locale
            variation = pnoise1(world_x * 0.02, base=self.seed)
            amplitude += variation * 5
            base_height += variation * 3

            terrain_noise = pnoise1(world_x * terrain_scale, base=self.seed)
            surface_height = int(base_height + terrain_noise * amplitude)

            # ⛰️ TERRAIN
            terrain_noise = pnoise1(world_x * terrain_scale, base=self.seed)
            surface_height = int(base_height + terrain_noise * amplitude)

            for y in range(game_property.CHUNK_MIN_HEIGHT, game_property.CHUNK_MAX_HEIGHT):
                world_y = y

                # 🌫️ AIR
                if world_y > max(surface_height, sea_level):
                    block_property = BlockProperty.AIR

                    # 🌱 STRUCTURES
                    if world_y - 1 == surface_height and surface_height >= sea_level:
                        rng = random.Random(self.seed + world_x)
                        r = rng.random()

                        structure_type = self.biome_manager.get_structure(biome, r)
                        if structure_type:
                            self.add_structure(structure_type, world_x, world_y)

                # 🌊 EAU
                elif world_y > surface_height and world_y <= sea_level:
                    block_property = BlockProperty.WATER

                # 🌿 SURFACE (IMPORTANT POUR VISUEL BIOME)
                elif world_y == surface_height:
                    if surface_height <= sea_level:
                        block_property = BlockProperty.SAND
                    else:
                        if surface_height >= game_property.CHUNK_MAX_HEIGHT // 2:
                            block_property = BlockProperty.SNOW
                        else:
                            block_property = BlockProperty.GRASS

                # 🌱 SOUS-SOL
                elif world_y > surface_height - 4:
                    if surface_height <= sea_level:
                        block_property = BlockProperty.SAND
                    else:
                        if surface_height >= game_property.CHUNK_MAX_HEIGHT // 2:
                            if world_y > surface_height - 2:
                                block_property = BlockProperty.STONE_SNOW
                            else:
                                block_property = BlockProperty.STONE
                        else:
                            block_property = BlockProperty.DIRT

                # 🪨 PROFOND
                else:
                    block_property = BlockProperty.STONE

                    # minerais
                    for ore, params in ORE_PARAMS.items():
                        if world_y <= params["min_y"]:
                            offset_x = self.seed * 137.5
                            offset_y = self.seed * 289.3

                            noise_val = pnoise2(
                                world_x * params["scale"] + offset_x,
                                world_y * params["scale"] + offset_y
                            )
                            if noise_val > params["threshold"]:
                                block_property = ore
                                break

                # 🧱 BEDROCK
                if world_y == game_property.CHUNK_MIN_HEIGHT:
                    block_property = BlockProperty.BEDROCK

                block = Block(world_x, world_y, block_property)
                self.blocks[(world_x, world_y)] = block

        self.generate_structures()
    
    def get_block(self, x, y):
        return self.blocks.get((x, y))
    
    def set_block_with_name(self, x, y, block_name):
        block_type = game_type.get_block_property(block_name)
        if block_type is None:
            return False
        self.set_block(x, y, Block(x, y, block_type))
    
    def set_block(self, x, y, block):
        """
        Fonction pour modifier un block dans le chunk:
        - appel du calcul de la lumière.
        """
        self.blocks[(x, y)] = block

        self.update_light()

    def update_light(self):
        for block in self.blocks.values():
            block.light = 15
            
        # self.compute_sky_light()
        # self.update_propaged_light()

    def update_propaged_light(self):
        sources = []

        for (x, y), block in self.blocks.items():
            if block.light == 15:  # sources lumineuses (ciel)
                sources.append((x, y, block.light))

        self.propagate_light(sources)

    def set_blocks(self, list_block):
        """
        Fonction pour modifier une liste de block sous forme (x, y, block):
        - 1 seul appel du calcul de la lumière.
        """
        for x, y, block in list_block:
            self.blocks[(x, y)] = block

        self.update_light()

    def compute_sky_light(self):
        """
        Fonction pour calculer la lumière dans le chunk
        """
        for x in range(game_property.CHUNK_WIDTH):
            world_x = self.x * game_property.CHUNK_WIDTH + x

            light = 15  # max lumière

            for y in reversed(range(game_property.CHUNK_MIN_HEIGHT, game_property.CHUNK_MAX_HEIGHT)):
                block = self.blocks.get((world_x, y))

                if not block:
                    continue

                block.light = light

                if block.can_collide():
                    light -= 2  # absorption

                if light < 0:
                    break
    
    def propagate_light(self, sources):
        queue = deque(sources)

        while queue:
            x, y, light = queue.popleft()

            if light <= 0:
                continue

            block = self.get_block(x, y)
            if not block:
                continue

            if block.light > light:
                continue

            block.light = light

            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                queue.append((x+dx, y+dy, light-1))

# ORE_PARAMS = {
#     BlockProperty.COAL_ORE: {"scale": 0.1, "threshold": 0.55, "min_y": 60},
#     BlockProperty.IRON_ORE: {"scale": 0.08, "threshold": 0.6, "min_y": 40},
#     BlockProperty.GOLD_ORE: {"scale": 0.06, "threshold": 0.65, "min_y": 30},
# }

ORE_PARAMS = {
    BlockProperty.COAL_ORE: {
        "scale": 0.12,
        "threshold": 0.45,
        "min_y": 60
    },
    BlockProperty.IRON_ORE: {
        "scale": 0.10,
        "threshold": 0.50,
        "min_y": 40
    },
    BlockProperty.GOLD_ORE: {
        "scale": 0.08,
        "threshold": 0.55,
        "min_y": 25
    },
}

class Block:
    texture_manager = None

    def __init__(self, x, y, block_property, debug=False):

        rect = pygame.Rect(
            x * game_property.TILE_SIZE,
            y * game_property.TILE_SIZE,
            game_property.TILE_SIZE,
            game_property.TILE_SIZE
        )
        self.rect = rect
        self.block_property = block_property
        self.light = 0

        self.debug = debug
        if self.block_property.life:
            self.life = self.block_property.life
            self.max_life = self.block_property.life
        else:
            self.life = 0
            self.max_life = 0

    def __str__(self):
        return f"Block(x:{self.rect.x // game_property.TILE_SIZE}, y:{self.rect.y // game_property.TILE_SIZE}, width:{self.rect.width // game_property.TILE_SIZE}, height:{self.rect.width // game_property.TILE_SIZE}, BlockProperty:{self.block_property})"

    def render(self, screen, cam_rect):
        
        # try to draw texture if available
        if self.debug:
            print(f"Render block {str(self)}")
        texture = self.get_texture()
        draw_x, draw_y = game_property.world_to_screen(
            self.rect.x, self.rect.y, self.rect.height, cam_rect
        )
        if texture:
            screen.blit(texture, (draw_x, draw_y))

        self.render_darkness(screen, draw_x, draw_y)

        if self.max_life > 0:
            ratio = self.life / self.max_life

            white_height = int(self.rect.height * (1 - ratio))

            if white_height > 0:
                overlay = pygame.Surface((self.rect.width, white_height), pygame.SRCALPHA)

                overlay.fill((255, 255, 255, 180))

                screen.blit(
                    overlay,
                    (draw_x, draw_y + self.rect.height - white_height)
                )

    def render_darkness(self, screen, draw_x, draw_y):
        light = self.light / 15  # normaliser

        darkness = int(255 * (1 - light))

        overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, darkness))

        screen.blit(overlay, (draw_x, draw_y))
        
    def get_texture(self):
        return self.texture_manager.get_texture(self.block_property.texture)
    
    def is_breackable(self) -> bool:
        return self.block_property.breakable
    
    def try_destroy(self, value) -> bool:
        self.life -= value * game_property.BREAK_COEF
        return self.life <= 0
    
    def reset_life(self):
        self.life = self.max_life
        
    def can_collide(self) -> bool:
        return self.block_property.collidable
    
    def to_json(self):
        return {
            "x": self.rect.x // game_property.TILE_SIZE,
            "y": self.rect.y // game_property.TILE_SIZE,
            "block": self.block_property.block_name,
        }