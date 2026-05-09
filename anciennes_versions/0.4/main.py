import pygame
import sys

# --- Constantes ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 40
GRAVITY = -0.4  # Négatif car axe Y inversé
MAX_Y = 120  # Haut de l'écran (dans notre repère)
MIN_Y = 0    # Bas de l'écran

# --- Initialisation ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# --- Charger textures ---
textures = {
    'grass': pygame.image.load('Teraria V2/textures/blocks/grass_block.png').convert_alpha(),
    'dirt': pygame.image.load('Teraria V2/textures/blocks/dirt.png').convert_alpha(),
    'player': pygame.image.load('Teraria V2/textures/player/head.png').convert_alpha()
}

# --- Carte de blocs (10x5) ---
world_data = [
    ['grass'] * 25,
    ['dirt'] * 25,
    ['dirt'] * 25,
    ['dirt'] * 25,
    [None] * 25
]

# --- Caméra ---
camera_offset = pygame.Vector2(0, 0)

# --- Joueur ---
player_pos = pygame.Vector2(5 * TILE_SIZE, 3 * TILE_SIZE)
player_vel = pygame.Vector2(0, 0)
on_ground = False


def world_to_screen(pos):
    """Transforme les coordonnées monde (avec Y inversé) en écran."""
    return (pos.x - camera_offset.x, SCREEN_HEIGHT - (pos.y - camera_offset.y))


def draw_world():
    for y, row in enumerate(world_data):
        for x, tile in enumerate(row):
            if tile:
                world_x = x * TILE_SIZE
                world_y = y * TILE_SIZE
                screen_pos = world_to_screen(pygame.Vector2(world_x, world_y))
                screen.blit(textures[tile], screen_pos)


def draw_player():
    screen_pos = world_to_screen(player_pos)
    screen.blit(textures['player'], screen_pos)


def is_on_ground():
    future_y = player_pos.y + player_vel.y - 1
    tile_x = int(player_pos.x // TILE_SIZE)
    tile_y = int(future_y // TILE_SIZE)
    if 0 <= tile_y < len(world_data) and 0 <= tile_x < len(world_data[0]):
        return world_data[tile_y][tile_x] is not None
    return False


# --- Boucle principale ---
while True:
    # --- Événements ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # --- Contrôles ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_vel.x = -4
    elif keys[pygame.K_RIGHT]:
        player_vel.x = 4
    else:
        player_vel.x = 0

    if keys[pygame.K_SPACE] and on_ground:
        player_vel.y = 10  # vers le haut (car Y inversé)
        on_ground = False

    # --- Physique ---
    player_vel.y += GRAVITY
    if player_vel.y < -10:
        player_vel.y = -10

    next_pos = player_pos + player_vel

    # Collision sol
    if is_on_ground():
        player_vel.y = 0
        on_ground = True
        next_pos.y = (int(player_pos.y // TILE_SIZE)) * TILE_SIZE
    else:
        on_ground = False

    # Appliquer le déplacement
    player_pos = next_pos

    # Empêcher de tomber sous la map
    if player_pos.y < MIN_Y:
        player_pos.y = MIN_Y
        player_vel.y = 0

    # --- Caméra ---
    camera_offset.x = player_pos.x - SCREEN_WIDTH // 2
    camera_offset.y = player_pos.y - SCREEN_HEIGHT // 2

    # --- Rendu ---
    screen.fill((100, 150, 255))  # ciel bleu
    draw_world()
    draw_player()
    pygame.display.flip()
    clock.tick(60)
