UPDATE_RATE = 60

CHUNK_WIDTH = 16
CHUNK_MIN_HEIGHT = -64
CHUNK_MAX_HEIGHT = 128
WATER_Y = 0
TILE_SIZE = 32

# RENDER_DISTANCE = 3
# PRELOAD_DISTANCE = 6

SIZE_ITEM = TILE_SIZE // 2

GRAVITY = 80
JUMP_VELOCITY = 23
ACCELERATION = 4000
MAX_SPEED = 400
ENTITY_SPEED = TILE_SIZE * 1.3
PLAYER_SPEED = ENTITY_SPEED

INVENTORY_SIZE_CASE = 64
MARGIN_UI_SCREEN = 10
MAX_ACTION_DISTANCE = TILE_SIZE * 4

BREAK_COEF = 1/2
DEFAULT_BREAK_POWER = 10
DAMAGE_COEF = 1/3

MAX_LIGHT = 15
LIGHT_COEF = 1

VERSION = "1.15"

# def world_to_screen(x, y, h, cam_rect):
#     sx = x - cam_rect.x
#     sy = cam_rect.height - (y - cam_rect.y) - h
#     return int(sx), int(sy)

# def screen_to_world(sx, sy, h, cam_rect):
#     x = sx + cam_rect.x
#     y = (cam_rect.height - sy - h) + cam_rect.y
#     return int(x), int(y)

def world_to_screen(x, y, h, cam_rect):
    sx = x - cam_rect.x
    sy = cam_rect.height - (y - cam_rect.y) - h

    return int(sx), int(sy)

def screen_to_world(sx, sy, h, cam_rect):
    x = sx + cam_rect.x
    y = (cam_rect.height - sy - h) + cam_rect.y

    return int(x), int(y)

from pathlib import Path
import sys

def get_resource_path(relative_path: str) -> str:
    """
    Retourne le chemin absolu vers une ressource.
    
    Compatible :
    - exécution normale (dev)
    - exécutable PyInstaller (.exe)
    """

    # Cas PyInstaller (fichier compilé)
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
    else:
        # Cas normal (projet Python)
        base_path = Path(__file__).resolve().parent.parent

    return str(base_path / relative_path)

def safe_div(a, b):
    return a / b if b > 0 else 0