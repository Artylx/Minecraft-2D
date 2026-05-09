import pygame
import sys
import random
from noise import pnoise1, pnoise2
import math

class DroppedItem:
    def __init__(self, pos, block_type):
        self.base_pos = pygame.Vector2(pos)
        self.rect = pygame.Rect(pos[0], pos[1], TILE_SIZE // 2, TILE_SIZE // 2)
        self.type = block_type
        self.vel = pygame.Vector2(0, -200)  # uniquement vers le haut

        self.image = pygame.transform.scale(textures[block_type], (TILE_SIZE // 2, TILE_SIZE // 2))
        self.time = 0

    def update(self, dt, tiles):
        self.time += dt

        # Gravité
        self.vel.y -= GRAVITY * dt
        # self.base_pos.x += self.vel.x * dt  # supprimé car on veut éviter le déplacement horizontal
        self.base_pos.y += self.vel.y * dt

        # Collision verticale (simplifiée)
        self.rect.topleft = (round(self.base_pos.x), round(self.base_pos.y))
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel.y > 0:
                    self.rect.bottom = tile.top
                    self.base_pos.y = self.rect.y
                    self.vel.y = 0

        # Oscillation verticale
        float_offset = 5 * math.sin(self.time * 2)
        self.rect.y = int(self.base_pos.y + float_offset)

    def draw(self, surface, camera_x, camera_y):
        surface.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))

class Player:
    def __init__(self, x, y):
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False

    def handle_input(self, keys):
        self.vel.x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel.x = -MOVE_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel.x = MOVE_SPEED
        if (keys[pygame.K_w] or keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vel.y = JUMP_SPEED  # saut vers le haut logique
            self.on_ground = False

    def apply_gravity(self, dt):
        self.vel.y -= GRAVITY * dt  # gravité vers le bas logique (diminue y)

    def move(self, dt, tiles):
        # Déplacement horizontal
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel.x > 0:
                    self.rect.right = tile.left
                    self.pos.x = self.rect.x
                elif self.vel.x < 0:
                    self.rect.left = tile.right
                    self.pos.x = self.rect.x

        # Déplacement vertical (repère inversé)
        self.pos.y += self.vel.y * dt
        self.rect.y = round(self.pos.y)
        self.on_ground = False
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel.y < 0:  # vers le bas logique
                    self.rect.top = tile.bottom
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                elif self.vel.y > 0:  # vers le haut logique
                    self.rect.bottom = tile.top
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                    self.on_ground = True

    def update(self, dt, tiles):
        keys = pygame.key.get_pressed()
        self.handle_input(keys)
        self.apply_gravity(dt)
        self.move(dt, tiles)

    def draw(self, surface, camera_x, camera_y):
        x = self.rect.x - camera_x
        y = self.rect.y - camera_y
        center_x = x + self.width // 2

        surface.blit(player_images["left_leg"], (center_x - LEG_SIZE[0], y + self.height - LEG_SIZE[1]))
        surface.blit(player_images["right_leg"], (center_x, y + self.height - LEG_SIZE[1]))
        surface.blit(player_images["body"], (center_x - BODY_SIZE[0] // 2, y + HEAD_SIZE[1]))
        surface.blit(player_images["left_arm"], (center_x - BODY_SIZE[0] // 2 - ARM_SIZE[0], y + HEAD_SIZE[1]))
        surface.blit(player_images["right_arm"], (center_x + BODY_SIZE[0] // 2, y + HEAD_SIZE[1]))
        surface.blit(player_images["head"], (center_x - HEAD_SIZE[0] // 2, y))

# Init
pygame.init()
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 40
CHUNK_WIDTH = 16
MAP_HEIGHT = 255

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# Couleurs
BLUE = (50, 50, 255)
WHITE = (255, 255, 255)

show_fps = False
font_f3 = pygame.font.SysFont(None, 30)

place_msg = ""
place_msg_end_time  = 0

# Joueur
PLAYER_HEIGHT = int(1.7 * TILE_SIZE)
PLAYER_WIDTH = int(0.8 * TILE_SIZE)

player = Player(100, 100)

GRAVITY = 1200
JUMP_SPEED = -600
MOVE_SPEED = 300

camera_x = 0
camera_y = 0

# Types de blocs
BLOCKS = {
    "AIR": 0,
    "HERBE": 1,
    "TERRE": 2,
    "PIERRE": 3,
    "BEDROCK": 4,
    "FER": 5,
    "CHARBON": 6,
    "OR": 7
}


dropped_items = []

# Chargement des images et redimensionnement
textures = {
    BLOCKS["HERBE"]: pygame.transform.scale(pygame.image.load("Teraria/textures/blocks/grass_block.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    BLOCKS["TERRE"]: pygame.transform.scale(pygame.image.load("Teraria/textures/blocks/dirt.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    BLOCKS["PIERRE"]: pygame.transform.scale(pygame.image.load("Teraria/textures/blocks/stone.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    BLOCKS["BEDROCK"]: pygame.transform.scale(pygame.image.load("Teraria/textures/blocks/bedrock.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    BLOCKS["FER"]: pygame.transform.scale(pygame.image.load("Teraria/textures/blocks/iron_ore.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    BLOCKS["CHARBON"]: pygame.transform.scale(pygame.image.load("Teraria/textures/blocks/coal_ore.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    BLOCKS["OR"]: pygame.transform.scale(pygame.image.load("Teraria/textures/blocks/gold_ore.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
}

player_width_collision = PLAYER_WIDTH  # 32 px (corps + jambes)
player_height_collision = PLAYER_HEIGHT  # 68 px (tête + corps + jambes)

HEAD_SIZE = (PLAYER_WIDTH, PLAYER_WIDTH)
BODY_SIZE = (PLAYER_WIDTH, PLAYER_HEIGHT // 3)
LEG_SIZE = (PLAYER_WIDTH // 2, PLAYER_HEIGHT // 3)
ARM_SIZE = (PLAYER_WIDTH // 3, PLAYER_HEIGHT // 3)

INVENTORY_SIZE = 9
inventory = [{"type": BLOCKS["AIR"], "count": 0} for _ in range(INVENTORY_SIZE)]
selected_slot = 0

# Charger les images des parties du joueur (taille adaptée)
player_images = {
    "head": pygame.transform.scale(pygame.image.load("Teraria/textures/player/head.png").convert_alpha(), HEAD_SIZE),
    "body": pygame.transform.scale(pygame.image.load("Teraria/textures/player/body.png").convert_alpha(), BODY_SIZE),
    "left_arm": pygame.transform.scale(pygame.image.load("Teraria/textures/player/arm.png").convert_alpha(), ARM_SIZE),
    "right_arm": pygame.transform.scale(pygame.image.load("Teraria/textures/player/arm.png").convert_alpha(), ARM_SIZE),
    "left_leg": pygame.transform.scale(pygame.image.load("Teraria/textures/player/leg.png").convert_alpha(), LEG_SIZE),
    "right_leg": pygame.transform.scale(pygame.image.load("Teraria/textures/player/leg.png").convert_alpha(), LEG_SIZE),
}

def draw_player(x, y):
    # x, y = coin haut-gauche du Rect collision (corps + jambes + tête)

    center_x = x + PLAYER_WIDTH // 2

    # Jambes
    screen.blit(player_images["left_leg"], (center_x - LEG_SIZE[0], y + PLAYER_HEIGHT - LEG_SIZE[1]))
    screen.blit(player_images["right_leg"], (center_x, y + PLAYER_HEIGHT - LEG_SIZE[1]))

    # Corps
    screen.blit(player_images["body"], (center_x - BODY_SIZE[0] // 2, y + HEAD_SIZE[1]))

    # Bras (hors collision, plus à gauche/droite)
    screen.blit(player_images["left_arm"], (center_x - BODY_SIZE[0] // 2 - ARM_SIZE[0], y + HEAD_SIZE[1]))  # décale bras gauche plus à gauche
    screen.blit(player_images["right_arm"], (center_x + BODY_SIZE[0] // 2, y + HEAD_SIZE[1]))  # décale bras droit plus à droite

    # Tête
    screen.blit(player_images["head"], (center_x - HEAD_SIZE[0] // 2, y))


# Dictionnaire monde {(x, y): bloc_type}
world_data = {}

SEED = 123456
CHUNK_WIDTH_OFFSET = 10000  # un grand offset pour "décaler" les chunks dans l'espace bruit

def generate_chunk(chunk_x):
    for x in range(CHUNK_WIDTH):
        global_x = chunk_x * CHUNK_WIDTH + x

        # Génération de relief
        low_freq = pnoise1(global_x * 0.005 + SEED * 1000)
        high_freq = pnoise1(global_x * 0.02 + SEED * 5000)
        mountain_noise = pnoise1(global_x * 0.002 + SEED * 2000)

        base_height = MAP_HEIGHT * 0.15
        amplitude = 25
        ground_height = MAP_HEIGHT - int(
            base_height +
            low_freq * 12 +
            high_freq * 3 +
            max(0, mountain_noise) * amplitude
        )

        for y in range(MAP_HEIGHT):  # du haut vers le bas
            noise_val = octave_noise(global_x, y, octaves=5, persistence=0.5, scale=0.08)
            cave_noise = (noise_val + 1) / 2

            # Air au-dessus du sol
            if y > ground_height - 40:
                world_data[(global_x, y)] = BLOCKS["AIR"]
                continue

            # Bedrock en bas
            if y == 0:
                world_data[(global_x, y)] = BLOCKS["BEDROCK"]
                continue

            threshold = 0.65 if y > ground_height - 45 else 0.55

            if cave_noise > threshold:
                world_data[(global_x, y)] = BLOCKS["AIR"]
            else:
                block = BLOCKS["PIERRE"]
                if is_surface(global_x, y):
                    block = BLOCKS["HERBE"]
                elif is_surface(global_x, y + 1):
                    block = BLOCKS["TERRE"]
                world_data[(global_x, y)] = block

    generate_ore_clusters(chunk_x)
    clean_caves(min_cave_size=20)

def is_surface(x, y):
    return (x, y + 1) in world_data and world_data[(x, y + 1)] == BLOCKS["AIR"]

def clean_caves(min_cave_size=5):
    # On cherche les régions d'air connectées et on supprime seulement les trop petites

    visited = set()
    air_regions = []

    directions = [(-1,0),(1,0),(0,-1),(0,1), (-1,-1), (-1,1), (1,-1), (1,1)]

    def flood_fill(start):
        queue = [start]
        region = []
        while queue:
            pos = queue.pop()
            if pos in visited:
                continue
            visited.add(pos)
            if world_data.get(pos) == BLOCKS["AIR"]:
                region.append(pos)
                x,y = pos
                for dx, dy in directions:
                    neighbor = (x + dx, y + dy)
                    if neighbor not in visited:
                        queue.append(neighbor)
        return region

    # Trouver toutes les régions d'air
    for pos, block in world_data.items():
        if block == BLOCKS["AIR"] and pos not in visited:
            region = flood_fill(pos)
            air_regions.append(region)

    # Supprimer les petites régions d'air (les remplir en pierre)
    for region in air_regions:
        if len(region) < min_cave_size:
            for pos in region:
                world_data[pos] = BLOCKS["PIERRE"]

def octave_noise(x, y, octaves=4, persistence=0.5, scale=0.1):
    total = 0
    frequency = scale
    amplitude = 1
    max_value = 0

    for _ in range(octaves):
        # Sans repeat
        total += pnoise2(x * frequency, y * frequency) * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= 2

    return total / max_value

def generate_ore_clusters(chunk_x):
    ores = [
        {"type": "CHARBON", "min_y": MAP_HEIGHT - 150, "max_y": MAP_HEIGHT, "density": 0.02, "cluster_size": (3, 5)},
        {"type": "FER",     "min_y": MAP_HEIGHT - 120, "max_y": MAP_HEIGHT, "density": 0.012, "cluster_size": (2, 4)},
        {"type": "OR",      "min_y": MAP_HEIGHT - 90,  "max_y": MAP_HEIGHT, "density": 0.006, "cluster_size": (2, 3)},
    ]

    for ore in ores:
        for x in range(CHUNK_WIDTH):
            global_x = chunk_x * CHUNK_WIDTH + x
            for y in range(ore["min_y"], min(MAP_HEIGHT - 1, ore["max_y"])):
                # Utiliser un bruit cohérent plutôt qu'un pur random
                noise = pnoise2(global_x * 0.1, y * 0.1, repeatx=999999, repeaty=999999)
                if 0.3 < noise < 0.3 + ore["density"] or random.random() < ore["density"] * 0.5:  # densité = fenêtre de bruit
                    size = random.randint(*ore["cluster_size"])
                    place_ore_cluster(global_x, y, BLOCKS[ore["type"]], size)

def place_ore_cluster(cx, cy, block_type, size):
    visited = set()
    to_process = [(cx, cy)]
    
    while to_process and len(visited) < size:
        x, y = to_process.pop()
        key = (x, y)
        
        if key in visited:
            continue
        visited.add(key)
        
        if key in world_data and world_data[key] == BLOCKS["PIERRE"]:
            world_data[key] = block_type

            # Ajoute des voisins avec une chance aléatoire de croissance
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if random.random() < 0.7:  # Réglage du taux de propagation
                    to_process.append((x + dx, y + dy))

def get_tile_rects(camera_x, camera_y):
    visible_tiles = []
    start_x = (camera_x) // TILE_SIZE - 1
    end_x = (camera_x + WIDTH) // TILE_SIZE + 1
    start_y = (camera_y) // TILE_SIZE - 1
    end_y = (camera_y + HEIGHT) // TILE_SIZE + 1

    for x in range(start_x, end_x + 1):
        for y in range(start_y, end_y + 1):
            if (x, y) in world_data and world_data[(x, y)] != BLOCKS["AIR"]:
                visible_tiles.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    return visible_tiles

def draw_inventory(selected_slot):
    slot_size = 50
    margin = 10
    hotbar_width = INVENTORY_SIZE * (slot_size + margin) - margin
    start_x = WIDTH // 2 - hotbar_width // 2
    y = HEIGHT - slot_size - 20
    font = pygame.font.SysFont(None, 24)

    for i in range(INVENTORY_SIZE):
        x = start_x + i * (slot_size + margin)
        rect = pygame.Rect(x, y, slot_size, slot_size)
        
        # Slot sélectionné = cadre blanc plus épais
        if i == selected_slot:
            pygame.draw.rect(screen, (255, 255, 255), rect, 4)
        else:
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)

        item = inventory[i]
        if item["type"] != BLOCKS["AIR"] and item["type"] in textures:
            icon = pygame.transform.scale(textures[item["type"]], (slot_size - 8, slot_size - 8))
            screen.blit(icon, (x + 4, y + 4))

            # Afficher la quantité si > 1
            if item["count"] > 1:
                count_surf = font.render(str(item["count"]), True, (255, 255, 255))
                screen.blit(count_surf, (x + 7, y + slot_size - 20))

def move(rect, pos, vel, dt, tiles):
    pos.x += vel.x * dt
    rect.x = round(pos.x)
    for tile in tiles:
        if rect.colliderect(tile):
            if vel.x > 0:
                rect.right = tile.left
                pos.x = rect.x
            elif vel.x < 0:
                rect.left = tile.right
                pos.x = rect.x

    pos.y += vel.y * dt
    rect.y = round(pos.y)
    on_ground = False
    for tile in tiles:
        if rect.colliderect(tile):
            if vel.y > 0:
                rect.bottom = tile.top
                pos.y = rect.y
                vel.y = 0
                on_ground = True
            elif vel.y < 0:
                rect.top = tile.bottom
                pos.y = rect.y
                vel.y = 0
    return on_ground

def draw_world(camera_x, camera_y):
    count = 0
    for (x, y), tile in world_data.items():
        if tile != BLOCKS["AIR"]:
            screen_x = x * TILE_SIZE - camera_x
            screen_y = y * TILE_SIZE - camera_y
            if (-TILE_SIZE < screen_x < WIDTH + TILE_SIZE) and (-TILE_SIZE < screen_y < HEIGHT + TILE_SIZE):
                screen.blit(textures[tile], (screen_x, screen_y))
                count += 1
    print("Blocs dessinés :", count)

def break_tile_at(mouse_pos, camera_x, camera_y):
    world_x = (mouse_pos[0] + camera_x) // TILE_SIZE
    world_y = (mouse_pos[1] + camera_y) // TILE_SIZE
    key = (int(world_x), int(world_y))

    player_tile_x = int(player.pos.x // TILE_SIZE)
    player_tile_y = int(player.pos.y // TILE_SIZE)

    # Calcul distance manhattan ou euclidienne (ici euclidienne)chunk_left 
    dist = ((player_tile_x - world_x)**2 + (player_tile_y - world_y)**2)**0.5

    r = random.Random()

    if dist <= 4:  # limite à 4 tuiles
        if key in world_data and world_data[key] not in (BLOCKS["AIR"], BLOCKS["BEDROCK"]):
            dropped_items.append(DroppedItem(
                (world_x * TILE_SIZE + TILE_SIZE // 3 + r.randint(-15, 5), world_y * TILE_SIZE + TILE_SIZE // 2),
                world_data[key]
            ))
            world_data[key] = BLOCKS["AIR"]

def place_tile_at(mouse_pos, camera_x, camera_y):
    global place_msg, place_msg_end_time

    world_x = (mouse_pos[0] + camera_x) // TILE_SIZE
    world_y = (mouse_pos[1] + camera_y) // TILE_SIZE
    key = (int(world_x), int(world_y))

    player_tile_x = int(player.pos.x // TILE_SIZE)
    player_tile_y = int(player.pos.y // TILE_SIZE)

    # Distance max pour poser un bloc (par exemple 4)
    dist = ((player_tile_x - world_x)**2 + (player_tile_y - world_y)**2)**0.5

    if dist <= 4:
        # Ne pas placer sur le joueur (au moins une tuile de buffer)
        if player.rect.collidepoint(world_x * TILE_SIZE + TILE_SIZE // 2, world_y * TILE_SIZE + TILE_SIZE // 2):
            return

        # Case vide (AIR)
        if key in world_data and world_data[key] == BLOCKS["AIR"]:
            # Vérifie que l'inventaire a le bloc sélectionné et une quantité > 0
            if inventory[selected_slot]["type"] != BLOCKS["AIR"] and inventory[selected_slot]["count"] > 0:
                # Place le bloc
                world_data[key] = inventory[selected_slot]["type"]
                # Décrémente l’inventaire
                inventory[selected_slot]["count"] -= 1
                if inventory[selected_slot]["count"] == 0:
                    inventory[selected_slot]["type"] = BLOCKS["AIR"]
    else:
        if key in world_data and world_data[key] == BLOCKS["AIR"]:
            if inventory[selected_slot]["type"] != BLOCKS["AIR"] and inventory[selected_slot]["count"] > 0:
                place_msg = "Trop loin pour placer un bloc !"
                place_msg_end_time = pygame.time.get_ticks() + 2000  # 2 secondes à 60 FPS

# Boucle principale
while True:
    dt = clock.tick() / 1000.0
    if dt > 0.05: dt = 0.05

    # Générer les chunks autour du joueur
    player_tile_x = int(player.pos.x // TILE_SIZE)
    chunk_left = (player_tile_x - 3 * CHUNK_WIDTH) // CHUNK_WIDTH
    chunk_right = (player_tile_x + 3 * CHUNK_WIDTH) // CHUNK_WIDTH

    for chunk_x in range(chunk_left, chunk_right + 1):
        if all((chunk_x * CHUNK_WIDTH + x, y) not in world_data
               for x in range(CHUNK_WIDTH) for y in range(MAP_HEIGHT)):
            generate_chunk(chunk_x)

    # Mouvements
    keys = pygame.key.get_pressed()
    player.handle_input(keys)
    player.apply_gravity(dt)

    tile_rects = get_tile_rects(camera_x, camera_y)
    on_ground = player.move(dt, tile_rects)

    if keys[pygame.K_SPACE] and on_ground:
        player.vel.y = JUMP_SPEED

    # Caméra centrée
    camera_x = player.rect.centerx - WIDTH // 2
    camera_y = player.rect.centery - HEIGHT // 2

    # Gestion des événements
    for event in pygame.event.get():
        if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                show_fps = not show_fps
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # clic gauche : casser
                break_tile_at(event.pos, camera_x, camera_y)
            elif event.button == 3:  # clic droit : placer
                place_tile_at(event.pos, camera_x, camera_y)
            elif event.button == 4:  # Molette haut
                selected_slot = (selected_slot - 1) % INVENTORY_SIZE
            elif event.button == 5:  # Molette bas
                selected_slot = (selected_slot + 1) % INVENTORY_SIZE

    for item in dropped_items[:]:
        item.update(dt, tile_rects)
        if player.rect.colliderect(item.rect.inflate(10, 10)):
            for i in range(INVENTORY_SIZE):
                if inventory[i]["type"] == item.type:
                    inventory[i]["count"] += 1
                    break
                elif inventory[i]["type"] == BLOCKS["AIR"]:
                    inventory[i]["type"] = item.type
                    inventory[i]["count"] = 1
                    break
            dropped_items.remove(item)

    # Affichage
    screen.fill(BLUE)
    draw_world(camera_x, camera_y)

    mouse_x, mouse_y = pygame.mouse.get_pos()
    tile_x = (mouse_x + camera_x) // TILE_SIZE
    tile_y = (mouse_y + camera_y) // TILE_SIZE
    key = (tile_x, tile_y)

    if key in world_data:
        rect_x = tile_x * TILE_SIZE - camera_x
        rect_y = tile_y * TILE_SIZE - camera_y
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        s.fill((0, 0, 0, 100))  # gris semi-transparent (dernier param = alpha)
        screen.blit(s, (rect_x, rect_y))

    draw_x = player.pos.x - (PLAYER_WIDTH - player.width) // 2 - camera_x
    draw_y = player.pos.y - (PLAYER_HEIGHT - player.height) - camera_y

    for item in dropped_items:
        item.draw(screen, camera_x, camera_y)

    player.draw(screen, camera_x, camera_y)

    current_time = pygame.time.get_ticks()
    if current_time < place_msg_end_time:
        font = pygame.font.SysFont(None, 36)
        text_surface = font.render(place_msg, True, (255, 0, 0))  # rouge
        text_rect = text_surface.get_rect()

        # Centre horizontalement
        x = (screen.get_width() - text_rect.width) // 2

        # Juste au-dessus de la hotbar (par exemple hotbar_height = 80 px)
        hotbar_height = 80
        y = screen.get_height() - hotbar_height - text_rect.height - 10  # 10 px de marge au-dessus hotbar

        screen.blit(text_surface, (x, y))
    
    draw_inventory(selected_slot)

    pygame.display.set_caption(f"OwerCube")

    if show_fps:
        fps_text = font_f3.render(f"FPS: {clock.get_fps():.2f}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))
        pos_text = font_f3.render(f"Position: ({int(player.pos.x)}, {int(player.pos.y)})", True, (255, 255, 255))
        screen.blit(pos_text, (10, 40)) 
    
    pygame.display.flip()
