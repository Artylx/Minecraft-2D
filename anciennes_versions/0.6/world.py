import math
import random
from noise import pnoise1, pnoise2
import blocks

CHUNK_SIZE = 2
RENDER_DISTANCE = 5

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

class World:
    def __init__(self, GameProperty, seed):
        self.player_list = []
        random.seed(seed)
        self.GameProperty = GameProperty
        self.blocks = blocks.Blocks(GameProperty)

        self.loaded_chunks = set()
        self.world_data = {}

    def add_player(self, player):
        if (self.player_list.__contains__(player)):
            print("PLAYER ALREADY ADDED")
        else:
            self.player_list.append(player)

    def get_chunk_coords(self, x, y):
        return int(math.floor(x / CHUNK_SIZE)), int(math.floor(y / CHUNK_SIZE))

    def event(self, events, keys):
        pass

    def generate_chunk(self, chunk_x, chunk_y):
        
        for x in range(chunk_x * CHUNK_SIZE, (chunk_x + 1) * CHUNK_SIZE):
            amplitude_mountain = 25
            amplitude_plain = 8
            freq_mountain = 0.012
            freq_plain = 0.04

            # Hauteur du sol (vers le bas)
            base_height = 15
            mountain_height = octave_noise(x, 0, octaves=4, persistence=0.5, scale=0.01) * amplitude_mountain
            plain_height = octave_noise(x, 0, octaves=2, persistence=0.7, scale=0.05) * amplitude_plain
            height = int(base_height + mountain_height + plain_height)

            for y in range(self.GameProperty.MIN_HEIGHT, self.GameProperty.MAX_HEIGHT):

                if y >= height:
                    block_num = self.blocks.BLOCKS["stone"]
                    if y < height + 4:
                        block_num = self.blocks.BLOCKS["dirt"]
                    if y == height:
                        block_num = self.blocks.BLOCKS["grass_block"]
                elif y == self.GameProperty.MIN_HEIGHT:
                    block_num = self.blocks.BLOCKS["bedrock"]
                else:
                    block_num = self.blocks.BLOCKS["air"]

                self.world_data[(x, y)] = blocks.Block(self.blocks, block_num, self.GameProperty.TILE_SIZE, x, y)
        self.loaded_chunks.add((chunk_x, chunk_y))

    def update_chunks_around_player(self, player):
        px_chunk, py_chunk = self.get_chunk_coords(
            int(player.pos.x // self.GameProperty.TILE_SIZE),
            int(player.pos.y // self.GameProperty.TILE_SIZE)
        )
        for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            for dy in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
                coords = (px_chunk + dx, py_chunk + dy)
                if coords not in self.loaded_chunks:
                    self.generate_chunk(*coords)
    
    def update(self):
        for player in self.player_list:
            self.update_chunks_around_player(player)
            #self.unload_distant_chunks(player.pos)

    def draw(self, screen, camera_x, camera_y):
        tile_size = self.GameProperty.TILE_SIZE
        width, height = screen.get_size()

        for (x, y), block in self.world_data.items():
            if block.number == self.blocks.BLOCKS["air"]:
                continue

            screen_y = y * tile_size - camera_y
            screen_x = x * tile_size - camera_x
            if -tile_size <= screen_x < width and -tile_size <= screen_y < height:
                block.draw(screen, screen_x , screen_y)