import pygame
import sys

import world
import player
import game_property

GameProperty = game_property.GameProperty("world_test", TILE_SIZE=40)

pygame.init()
info = pygame.display.Info()

WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()

World = world.World(GameProperty, 123456)

Player = player.Player(GameProperty, "Player 1", x=10 * GameProperty.TILE_SIZE, y=10 * GameProperty.TILE_SIZE)
World.add_player(Player)

camera_x = 0
camera_y = 0

while True:
    dt = clock.tick() / 1000.0
    if dt > 0.05: dt = 0.05

    WIDTH, HEIGHT = info.current_w, info.current_h
    camera_x = int(Player.pos.x - WIDTH // 2)
    camera_y = int(Player.pos.y - HEIGHT // 2)

    keys = pygame.key.get_pressed()
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()

    screen.fill((100, 180, 255))

    World.event(events, keys)
    World.update()
    World.draw(screen, camera_x, camera_y)

    Player.update(dt, World.world_data.values())
    Player.draw(screen, camera_x, camera_y)

    font = pygame.font.SysFont(None, 36)
    pos_text = font.render(f"Player pos: ({int(Player.pos.x)}, {int(Player.pos.y)}), On ground: {Player.on_ground}, Rect: ({Player.rect.x}, {Player.rect.y}, {Player.rect.width}, {Player.rect.height}), dt: {dt:.2f}", True, (0, 0, 0))
    screen.blit(pos_text, (20, 20))

    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, (0, 0, 0))
    screen.blit(fps_text, (20, 50))

    debug_text = font.render(f"Debug cam_y: {camera_y}, cam_x: {camera_x}", True, (0, 0, 0))
    screen.blit(debug_text, (20, 80))

    pygame.draw.rect(screen, (0, 0, 0), (Player.rect.x - camera_x, -Player.rect.y - camera_y, Player.rect.width, Player.rect.height), 2)

    pygame.display.set_caption(f"OwerCube")
    pygame.display.flip()