UPDATE_RATE = 60

CHUNK_WIDTH = 16
CHUNK_MIN_HEIGHT = -64
CHUNK_MAX_HEIGHT = 128
WATER_Y = 0
TILE_SIZE = 32
RENDER_DISTANCE = 3

SIZE_ITEM = TILE_SIZE // 2

GRAVITY = 80
JUMP_VELOCITY = 23
ACCELERATION = 4000
MAX_SPEED = 400

INVENTORY_SIZE_CASE = 64
MARGIN_UI_SCREEN = 10
MAX_ACTION_DISTANCE = TILE_SIZE * 4

BREAK_COEF = 1/2

def world_to_screen(x, y, h, cam_rect):
    sx = x - cam_rect.x
    sy = cam_rect.height - (y - cam_rect.y) - h
    return sx, sy

def screen_to_world(sx, sy, h, cam_rect):
    x = sx + cam_rect.x
    y = (cam_rect.height - sy - h) + cam_rect.y
    return x, y