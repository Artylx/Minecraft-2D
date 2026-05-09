class GameProperty:
    def __init__(self, name, TILE_SIZE=40, MOVE_SPEED=300, JUMP_SPEED=-600, GRAVITY=1200):
        self.name = name
        self.TILE_SIZE = TILE_SIZE
        self.MOVE_SPEED = MOVE_SPEED
        self.JUMP_SPEED = JUMP_SPEED
        self.GRAVITY = GRAVITY
        self.MIN_HEIGHT = 0
        self.MAX_HEIGHT = 30
