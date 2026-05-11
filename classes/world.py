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
from classes import debug

def load_world_json(world_path):
    """
    Charge le fichier JSON d'un monde à partir de son nom.

    :param world_name: Nom du monde (str)
    :return: dictionnaire Python avec les données du monde ou None si erreur
    """
    world_path = os.path.join("worlds", world_path, "world.json")

    if not os.path.isfile(world_path):
        print(f"Le monde '{world_path}' n'existe pas à {world_path}")
        return None

    try:
        with open(world_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Erreur lors du chargement du monde '{world_path}': {e}")
        return None
    
def save_world_json(world, world_path, world_name):
    """
    Sauvegarde les données d'un monde dans un fichier JSON.

    :param world: instance de la classe World à sauvegarder
    :param world_name: Nom du monde (str)
    :return: None
    """
    try:
        with open(os.path.join("worlds", world_path, f"{world_name}.json"), "w") as f:
            json.dump(world.get_json(), f, indent=4, default=str)
        print(f"Monde sauvegardé avec succès dans {world_path}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du monde '{world_path}': {e}")

class World:
    def __init__(self, screen_size, name="Unamed world", seed=None, json_data=None, callback_loading=None):
        """
        Constructeur unique qui gère soit :
        - la génération d'un monde depuis une seed
        - la reconstruction d'un monde depuis un JSON
        """
        self.screen_size = screen_size
        self.name = name
        self.callback_loading = callback_loading
        self.is_loaded = False

        if json_data is not None:
            # charger depuis le JSON
            self.set_json(json_data)
        else:
            # générer depuis la seed
            self.seed = seed if seed is not None else random.randint(10000, 99999)
            self.random = random.Random(self.seed)

            self.entitys = []  
            self.offline_entitys = []
            self.modified_blocks = {}  
        
        self.structure_manager = StructureManager()
        self.biome_manager = BiomeManager()

        # initialisation commune
        self.init()
        
    def init(self):
        self.hit_box_visible = False

        self.chunks = {}
        self.light_map = {} 
        self.block_light_queue = deque()
        self.sky_light_queue = deque()
        self.sky_column_queue = deque()

        self.block_light = {}
        self.light_sources = set()
        self.dirty_chunks = set()

        self.total_chunks_to_load = 0
        self.loaded_chunks = 0

        self.total_columns = 0
        self.done_columns = 0

        self.total_light_steps = 0
        self.done_light_steps = 0

    def set_json(self, json):
        seed = json.get("seed", None)
        entitys = json.get("entitys", None)
        modified_blocks = json.get("modified_blocks", None)

        if seed is not None and entitys is not None and modified_blocks is not None:
            self.seed = seed
            self.entitys = []
            self.offline_entitys = []

            for e in entity.dict_to_entitys(entitys, self):
                if isinstance(e, EntityClass.Player):
                    self.add_offline_entity(e)
                else:
                    self.create_entity(e)
            
            self.modified_blocks = modified_blocks

            print("World chargé avec succés")
        else:
            print("World non recevable")
            exit(1)
    
    def get_json(self):
        entitys_json = [e.to_json() for e in self.entitys]
        for e in self.offline_entitys:
            entitys_json.append(e.to_json())

        return {
            "seed": self.seed,
            "entitys": entitys_json,
            "modified_blocks": self.modified_blocks
        }
    
    def stop(self):
        for player in self.get_entities(EntityClass.Player):
            self.player_quit(player.name)


    def player_join(self, player_name):
        player = self.get_player_by_name(player_name)

        if player:
            return player
        else:
            player = self.get_player_offline(player_name)
            if player:
                self.create_entity(player)
                self.remove_offline_entity(player)
                return player
            else:
                player = entity.Player(self, name=player_name)

                self.create_entity(player)
                return player

    def player_quit(self, player_name):
        player = self.get_player_by_name(player_name)

        if player:
            self.remove_entity(player)
            self.add_offline_entity(player)
    
    def get_player_offline(self, player_name):
        for e in self.offline_entitys:
            if isinstance(e, EntityClass.Player):

                if e.name == player_name:
                    return e
        return None

    def create_entity(self, entity):
        self.entitys.append(entity)

    def remove_entity(self, entity):
        if entity in self.entitys:
            self.entitys.remove(entity)

    def add_offline_entity(self, entity):
        self.offline_entitys.append(entity)

    def remove_offline_entity(self, entity):
        if entity in self.offline_entitys:
            self.offline_entitys.remove(entity)

    def add_chunk(self, chunk_x):
        if chunk_x not in self.chunks:

            import time
            start = time.time()

            chunk = Chunk(chunk_x, self.seed, self.structure_manager, self.biome_manager)
            self.chunks[chunk_x] = chunk

            # appliquer les modifications sauvegardées
            blc = 0
            list_blocks = []
            if str(chunk_x) in self.modified_blocks:

                for data in self.modified_blocks[str(chunk_x)]:

                    x = data["x"]
                    y = data["y"]

                    block_name = data["block"].upper()

                    if block_name not in BlockProperty.REGISTRY:
                        raise ValueError(f"Block inconnu: {block_name}")

                    block_type = BlockProperty.REGISTRY[block_name]

                    list_blocks.append((x, y, Block(x, y, block_type)))
                    blc += 1
            
            self.set_blocks(list_blocks, update_range=0)
            
            for x in range(chunk_x * game_property.CHUNK_WIDTH, (chunk_x+1)*game_property.CHUNK_WIDTH):
                self.sky_column_queue.append(x)

                for y in range(game_property.CHUNK_MIN_HEIGHT, game_property.CHUNK_MAX_HEIGHT):
                    self.sky_light_queue.append((x, y))

            end = time.time()
            print(f"Chunk {chunk_x} loaded in {end - start:.2f}s => Modified blocks: {blc}")
            self.loaded_chunks += 1

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

        self.total_chunks_to_load = len(chunks_to_keep)
        self.total_columns = self.total_chunks_to_load * game_property.CHUNK_WIDTH
        self.total_light_steps = self.total_columns * (game_property.CHUNK_MAX_HEIGHT - game_property.CHUNK_MIN_HEIGHT)

        chunks_to_unload = set(self.chunks.keys())

        end_loading = True

        for chunk_x in sorted_chunks:
            chunks_to_unload.discard(chunk_x)

            if chunk_x not in self.chunks:
                self.add_chunk(chunk_x)
                end_loading = False
                break

        for chunk_coords in chunks_to_unload:
            self.unload_chunk(chunk_coords)

        if not end_loading:
            if not self.is_loaded:
                self.callback_loading("Chargement des chunks...", 20)

        return end_loading

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
        end_loading = self.update_chunks()

        if end_loading:
            self.compute_sky_column()
            if not self.is_loaded:
                self.callback_loading("Calcul de la lumière...", 30)

            if not self.sky_column_queue:
                self.propagate_sky_light()
                if not self.is_loaded:
                    self.callback_loading("Calcul de la lumière...", 80)

        to_remove = []

        for entity in self.get_entities():
            entity.update(dt)

            if not entity.is_alive:
                to_remove.append(entity)
                continue

            entity_chunk_x = entity.rect.x // (game_property.TILE_SIZE * game_property.CHUNK_WIDTH)
            if entity_chunk_x not in self.chunks or entity.rect.y < -20000:
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
                

        # suppression des entités ramassées
        for entity in to_remove:
            self.remove_entity(entity)

        if not self.is_loaded and end_loading and not self.sky_column_queue and not self.sky_light_queue:
            self.callback_loading("C'est fini", 100)
            self.is_loaded = True

    def update_screen_size(self, screen_size):
        self.screen_size = screen_size

    def render_debug(self, screen, cam_rect):
        font = pygame.font.SysFont(None, 24)

        debug_text = f"Chunks loaded: {len(self.chunks.values())}, {list(self.chunks.keys())}"
        text_surface = font.render(debug_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 70))

        debug_text = f"Entitys: {len(self.entitys)}"
        text_surface = font.render(debug_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 90))

        # pygame.draw.rect(screen, (0, 255, 0), (self.screen_size[0] // 2 - 1, 0, 2, self.screen_size[1]))
        # pygame.draw.rect(screen, (0, 255, 0), (0, self.screen_size[1] // 2 - 1, self.screen_size[0], 2))
        for chunk_x in self.chunks.keys():
            # position monde du début du chunk
            world_x = chunk_x * game_property.CHUNK_WIDTH * game_property.TILE_SIZE

            # conversion écran
            screen_x = world_x - cam_rect.x

            pygame.draw.line(
                screen,
                (255, 0, 0),
                (screen_x, 0),
                (screen_x, self.screen_size[1]),
                1
            )

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
    
    def update_light_area(self):
        self.block_light_queue.clear()

        for chunk in self.chunks.values():
            for block in chunk.blocks.values():
                block.block_light = 0

        for x, y in self.light_sources:
            block = self.get_block(x, y)
            if block:
                block.block_light = block.block_property.light_emission
                self.block_light_queue.append((x, y))

        self.propagate_block_light()
    
    def set_block(self, X, Y, block, update_range=1):
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

        if block.block_property.light_emission > 0:
            self.light_sources.add((X, Y))

        self.update_light_area()
        for dx in range(-10, 10):
            self.sky_column_queue.append(X + dx)

        for x in range(X - update_range, X + update_range):
            for y in range(game_property.CHUNK_MIN_HEIGHT, game_property.CHUNK_MAX_HEIGHT):
                self.sky_light_queue.append((x, y))

        return True

    def modif_block(self, X, Y, block):
        self.add_modified_block(X, Y, block)
        return self.set_block(X, Y, block, update_range=15)

    def add_modified_block(self, x, y, block):
        chunk_x = x // game_property.CHUNK_WIDTH
        if str(chunk_x) not in self.modified_blocks:
            self.modified_blocks[str(chunk_x)] = []

        self.modified_blocks[str(chunk_x)].append({
            "x": x,
            "y": y,
            "block": block.block_property.block_name
        })
        return
    
    def set_blocks(self, list_block, update_range=1):
        """
        Modifier tous les blocks et actualiser la limière une fois

        :param list_block: liste de tuples (x, y, block)
        """

        for x, y, block in list_block:
            
            chunk_x = x // game_property.CHUNK_WIDTH
            if chunk_x not in self.chunks:
                return False

            chunk = self.chunks[chunk_x]

            chunk.set_block(x, y, block)

            if block.block_property.light_emission > 0:
                self.light_sources.add((x, y))
        
            self.sky_column_queue.append(x)
            for x in range(x - update_range, x + update_range):
                for y in range(game_property.CHUNK_MIN_HEIGHT, game_property.CHUNK_MAX_HEIGHT):
                    self.sky_light_queue.append((x, y))

        self.update_light_area()
        return True
    
    def seed_block_light(self, cx, cy, radius):
        for x in range(cx-radius, cx+radius+1):
            for y in range(cy-radius, cy+radius+1):
                block = self.get_block(x, y)
                if not block:
                    continue

                # SAFE CHECK
                if block.block_property.light_emission > 0:
                    block.block_light = block.block_property.light_emission
                    self.block_light_queue.append((x, y))
    
    def compute_sky_column(self, max_steps=10):
        for _ in range(max_steps):
            if not self.sky_column_queue:
                return
            
            x = self.sky_column_queue.popleft()

            self.done_columns += 1

            light = 15

            for y in reversed(range(game_property.CHUNK_MIN_HEIGHT, game_property.CHUNK_MAX_HEIGHT)):
                block = self.get_block(x, y)
                if not block:
                    continue

                block.sky_light = light

                if block.can_collide():
                    light = max(light - 2, 0)

    # def reset_light_area(self, cx, cy, radius):
    #     for x in range(cx-radius, cx+radius+1):
    #         for y in range(cy-radius, cy+radius+1):
    #             block = self.get_block(x, y)
    #             if block:
    #                 block.block_light = 0
    
    def propagate_sky_light(self, max_steps=1000):
        for _ in range(max_steps):
            if not self.sky_light_queue:
                return

            x, y = self.sky_light_queue.popleft()
            block = self.get_block(x, y)

            self.done_light_steps += 1

            if not block:
                continue

            current = block.sky_light

            for dx, dy in [(1,0), (-1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                neighbor = self.get_block(nx, ny)

                if not neighbor:
                    continue

                absorb = self.get_propagate_value(neighbor)

                new_light = current - absorb

                if new_light <= 0:
                    continue

                if new_light > neighbor.sky_light:
                    neighbor.sky_light = new_light
                    self.sky_light_queue.append((nx, ny))
    
    def propagate_block_light(self):
        while self.block_light_queue:
            x, y = self.block_light_queue.popleft()
            block = self.get_block(x, y)

            if not block:
                continue

            current = block.block_light

            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                nx, ny = x + dx, y + dy
                neighbor = self.get_block(nx, ny)

                if not neighbor:
                    continue

                absorb = self.get_propagate_value(neighbor)
                new_light = current - absorb

                if new_light <= 0:
                    continue

                if new_light > neighbor.block_light:
                    neighbor.block_light = new_light
                    self.block_light_queue.append((nx, ny))

    def get_propagate_value(self, block):
        if block.can_collide():
            return 4
        return 0.8
    
    def get_light_absorption(block):
        if block.can_collide():
            return 4
        return 0

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

        self.modif_block(
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
        if not block_pos:
            return
        
        current_block = self.get_block(block_pos[0], block_pos[1])
        if not current_block or not current_block.is_breackable():
            return
        
        current_block.life = current_block.max_life

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
        self.seed = abs(hash(seed))
        self.noise_seed = self.seed & 0xff
        self.structure_manager = structure_manager
        self.biome_manager = biome_manager

        self.blocks = {}
        self.structures = []
        self.generate()

    def add_structure(self, struct_type: StructureType, base_x, base_y):
        self.structures.append((struct_type, base_x, base_y))

    def generate_structures(self):
        for struct_type, base_x, base_y in self.structures:
            self.structure_manager.place_structure(self, struct_type, base_x, base_y)

    def generate_vein(self, start_x, start_y, ore, max_size):
        vein_blocks = []
        to_process = [(start_x, start_y)]
        visited = set()

        rng = random.Random(self.seed + start_x * 9182 + start_y * 1237)

        while to_process and len(vein_blocks) < max_size:
            x, y = to_process.pop(0)

            if (x, y) in visited:
                continue
            visited.add((x, y))

            block = self.get_block(x, y)

            if not block or block.block_property != BlockProperty.STONE:
                continue

            self.set_block(x, y, Block(x, y, ore))
            vein_blocks.append((x, y))

            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                if rng.random() < 0.7:
                    nx, ny = x + dx, y + dy

                    if nx < self.x * game_property.CHUNK_WIDTH or nx >= (self.x + 1) * game_property.CHUNK_WIDTH:
                        continue

                    if ny < game_property.CHUNK_MIN_HEIGHT or ny >= game_property.CHUNK_MAX_HEIGHT:
                        continue

                    to_process.append((nx, ny))

    def generate(self):
        terrain_scale = 0.01

        sea_level = game_property.WATER_Y

        for x in range(game_property.CHUNK_WIDTH):
            world_x = self.x * game_property.CHUNK_WIDTH + x

            biome, amplitude, base_height = self.biome_manager.get_biome_generate_values(world_x, self.noise_seed)

            # 🌊 variation locale
            variation = pnoise1(world_x * 0.02, base=self.noise_seed)
            amplitude += variation * 5
            base_height += variation * 3

            terrain_noise = pnoise1(world_x * terrain_scale, base=self.noise_seed)
            surface_height = int(base_height + terrain_noise * amplitude)

            # ⛰️ TERRAIN
            terrain_noise = pnoise1(world_x * terrain_scale, base=self.noise_seed)
            surface_height = int(base_height + terrain_noise * amplitude)

            for y in range(game_property.CHUNK_MIN_HEIGHT, game_property.CHUNK_MAX_HEIGHT):
                world_y = y

                # EAU
                if world_y > surface_height and world_y <= sea_level:
                    block_property = BlockProperty.WATER

                # SURFACE (IMPORTANT POUR VISUEL BIOME)
                elif world_y == surface_height:
                    if surface_height <= sea_level:
                        block_property = BlockProperty.SAND
                    else:
                        if surface_height >= game_property.CHUNK_MAX_HEIGHT // 2:
                            block_property = BlockProperty.SNOW
                        else:
                            block_property = BlockProperty.GRASS

                # SOUS-SOL
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

                # PROFOND
                else:
                    block_property = BlockProperty.STONE

                # GROTTE (carving)
                cave_noise = pnoise2(
                    world_x * 0.05,
                    world_y * 0.05,
                    octaves=3,
                    base=self.noise_seed
                )

                cave_noise2 = pnoise2(
                    world_x * 0.1,
                    world_y * 0.1,
                    octaves=2,
                    base=self.noise_seed + 42
                )

                cave = (cave_noise + 1) / 2
                cave2 = (cave_noise2 + 1) / 2

                combined = (cave + cave2) / 2  # fusion des bruits

                depth_factor = (surface_height - world_y) / 50
                threshold = 0.55 - depth_factor * 0.02

                horizontal_factor = abs(pnoise1(world_x * 0.02, base=self.noise_seed))
                threshold += horizontal_factor * 0.05

                if combined > threshold and world_y <= surface_height - 3:
                    block_property = BlockProperty.AIR
                
                # SURFACE
                if world_y > max(surface_height, sea_level):
                    block_property = BlockProperty.AIR

                    # STRUCTURES
                    if world_y - 1 == surface_height and surface_height >= sea_level:
                        rng = random.Random(self.seed + world_x)
                        r = rng.random()

                        structure_type = self.biome_manager.get_structure(biome, r)
                        if structure_type:
                            self.add_structure(structure_type, world_x, world_y)

                # BEDROCK
                if world_y == game_property.CHUNK_MIN_HEIGHT:
                    block_property = BlockProperty.BEDROCK

                block = Block(world_x, world_y, block_property)
                self.blocks[(world_x, world_y)] = block

        for ore, params in ORE_PARAMS.items():
            rng = random.Random(self.seed + hash(ore) + self.x)

            for _ in range(params["max_chunks"]):  # nombre de filons par chunk
                x = rng.randint(
                    self.x * game_property.CHUNK_WIDTH,
                    (self.x + 1) * game_property.CHUNK_WIDTH - 1
                )
                y = rng.randint(game_property.CHUNK_MIN_HEIGHT, params["min_y"])

                self.generate_vein(x, y, ore, params["max_size"])

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
        Fonction pour modifier un block dans le chunk
        """
        self.blocks[(x, y)] = block

    def set_blocks(self, list_block):
        """
        Fonction pour modifier une liste de block sous forme (x, y, block)
        """
        for x, y, block in list_block:
            self.blocks[(x, y)] = block


ORE_PARAMS = {
    BlockProperty.COAL_ORE: {
        "scale": 0.12,
        "threshold": 0.45,
        "min_y": 40,
        "max_size": 13,
        "max_chunks": 6
    },
    BlockProperty.IRON_ORE: {
        "scale": 0.10,
        "threshold": 0.50,
        "min_y": 10,
        "max_size": 7,
        "max_chunks": 5
    },
    BlockProperty.GOLD_ORE: {
        "scale": 0.08,
        "threshold": 0.55,
        "min_y": -10,
        "max_size": 6,
        "max_chunks": 4
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

        self.sky_light = 0
        self.block_light = 0

        self.item_contain = []

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
        light = max(self.sky_light, self.block_light)

        if not debug.LIGHT:
            light = game_property.MAX_LIGHT

        light = light / game_property.MAX_LIGHT

        if light == 1:
            return

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