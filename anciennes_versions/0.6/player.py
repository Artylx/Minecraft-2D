import pygame
import blocks

class Player:
    def __init__(self, GameProperty, name, x=0, y=0):
        self.GameProperty = GameProperty
        self.name = name

        self.blocks = blocks.Blocks(GameProperty)

        self.PLAYER_HEIGHT = int(1.7 * GameProperty.TILE_SIZE)
        self.PLAYER_WIDTH = int(0.8 * GameProperty.TILE_SIZE)

        self.HEAD_SIZE = (self.PLAYER_WIDTH, self.PLAYER_WIDTH)
        self.BODY_SIZE = (self.PLAYER_WIDTH, self.PLAYER_HEIGHT // 3)
        self.LEG_SIZE = (self.PLAYER_WIDTH // 2, self.PLAYER_HEIGHT // 3)
        self.ARM_SIZE = (self.PLAYER_WIDTH // 3, self.PLAYER_HEIGHT // 3)

        self.player_images = {
            "head": pygame.transform.scale(pygame.image.load("textures/player/head.png").convert_alpha(), self.HEAD_SIZE),
            "body": pygame.transform.scale(pygame.image.load("textures/player/body.png").convert_alpha(), self.BODY_SIZE),
            "left_arm": pygame.transform.scale(pygame.image.load("textures/player/arm.png").convert_alpha(), self.ARM_SIZE),
            "right_arm": pygame.transform.scale(pygame.image.load("textures/player/arm.png").convert_alpha(), self.ARM_SIZE),
            "left_leg": pygame.transform.scale(pygame.image.load("textures/player/leg.png").convert_alpha(), self.LEG_SIZE),
            "right_leg": pygame.transform.scale(pygame.image.load("textures/player/leg.png").convert_alpha(), self.LEG_SIZE),
        }

        self.inventory = {}
        self.pos = pygame.Vector2(x, y)
        self.rect = pygame.Rect(x, y, self.PLAYER_WIDTH, self.PLAYER_HEIGHT)
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False

    def get_inventory(self):
        pass

    def handle_input(self, keys):
        self.vel.x = 0
        if keys[pygame.K_q] or keys[pygame.K_LEFT]:
            self.vel.x = -self.GameProperty.MOVE_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel.x = self.GameProperty.MOVE_SPEED
        if (keys[pygame.K_w] or keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vel.y = self.GameProperty.JUMP_SPEED
            self.on_ground = False

    def apply_gravity(self, dt):
        self.vel.y += self.GameProperty.GRAVITY * dt

    def move(self, dt, tiles):
        # --- Déplacement horizontal ---
        new_x = self.pos.x + self.vel.x * dt
        test_rect = self.rect.copy()
        test_rect.x = round(new_x)

        collided = False
        for tile in tiles:
            if not tile.Collision or tile.number == self.blocks.BLOCKS["air"]:
                continue

            tile_rect = tile.get_rect()
            if tile_rect and test_rect.colliderect(tile_rect):
                collided = True
                if self.vel.x > 0:
                    self.rect.right = tile_rect.left
                    self.pos.x = self.rect.x
                elif self.vel.x < 0:
                    self.rect.left = tile_rect.right
                    self.pos.x = self.rect.x
                break
        
        if not collided:
            self.pos.x = new_x
            self.rect.x = test_rect.x

        # --- Déplacement vertical ---
        new_y = self.pos.y + self.vel.y * dt
        test_rect = self.rect.copy()
        test_rect.y = round(new_y)

        self.on_ground = False
        collided = False
        for tile in tiles:
            if not tile.Collision or tile.number == self.blocks.BLOCKS["air"]:
                continue

            tile_rect = tile.get_rect()
            if tile_rect and test_rect.colliderect(tile_rect):
                collided = True
                if self.vel.y > 0:  # Descente (tombe vers le bas)
                    self.rect.bottom = tile_rect.top
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0:  # Montée (saute vers le haut)
                    self.rect.top = tile_rect.bottom
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                break
        
        if not collided:
            self.pos.y = new_y
            self.rect.y = test_rect.y

    
    def update(self, dt, tiles):
        keys = pygame.key.get_pressed()
        self.handle_input(keys)
        self.apply_gravity(dt)
        self.move(dt, tiles)

    def draw(self, surface, camera_x, camera_y):
        x = self.rect.x - camera_x
        y = self.rect.y - camera_y
        center_x = x + self.PLAYER_WIDTH // 2

        surface.blit(self.player_images["left_leg"], (center_x - self.LEG_SIZE[0], y + self.PLAYER_HEIGHT - self.LEG_SIZE[1]))
        surface.blit(self.player_images["right_leg"], (center_x, y + self.PLAYER_HEIGHT - self.LEG_SIZE[1]))
        surface.blit(self.player_images["body"], (center_x - self.BODY_SIZE[0] // 2, y + self.HEAD_SIZE[1]))
        surface.blit(self.player_images["left_arm"], (center_x - self.BODY_SIZE[0] // 2 - self.ARM_SIZE[0], y + self.HEAD_SIZE[1]))
        surface.blit(self.player_images["right_arm"], (center_x + self.BODY_SIZE[0] // 2, y + self.HEAD_SIZE[1]))
        surface.blit(self.player_images["head"], (center_x - self.HEAD_SIZE[0] // 2, y))