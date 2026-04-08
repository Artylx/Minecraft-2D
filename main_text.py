from classes import entity
import pygame

pygame.init()

WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

entity.Entity.texture_manager.load_default_textures()

zombie = entity.Zobmie()

print(zombie.to_json())