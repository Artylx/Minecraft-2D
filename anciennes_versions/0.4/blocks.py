import pygame

class Blocks:
    def __init__(self):
        self.blocks = {}

    def add_block(self, block_id, texture):
        self.blocks[block_id] = texture

    def get_texture(self, block_id):
        return self.blocks.get(block_id, None)