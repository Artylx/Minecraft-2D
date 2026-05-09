import pygame

class Player:
    def __init__(self, rect=(0, 0, 32, 32), name="Player"):
        self.rect = rect
        self.x = 0
        self.y = 0
        self.name = name
        # velocities in tiles per second
        self.vx = 0.0
        self.vy = 0.0

        self.speed = 100
        self.on_ground = False
        self.speed = 100

        self.direction = None

    def set_direction(self, direction_x, direction_y):
        self.direction = (direction_x, direction_y)

    def update(self, dt, world):
        # apply gravity and update position

        self.apply_gravity(dt)

        if self.direction[0] == "right":
            self.vx += self.speed * dt
        elif self.direction[0] == "left":
            self.vx -= self.speed * dt
            
        if self.direction[1] == "down":
            self.vy -= self.speed * dt
        elif self.direction[1] == "up":
            self.vy += self.speed * dt

        # check collisions with world (not implemented here)
        # self.check_collisions(world)
        
        self.vx *= 0.9
        self.vy *= 0.9

        new_pos = (self.x + self.vx * dt, self.y + self.vy * dt)

        if world.check_collisions_y(self.rect, new_pos):
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False
            self.y = new_pos[1]

        if world.check_collisions_x(self.rect, new_pos):
            self.vx = 0
        else:
            self.x = new_pos[0]

    def apply_gravity(self, dt, gravity=200):
        # gravity pulls downward (negative y).

        if self.on_ground == True:
            self.vy = 0
        else:
            self.vy -= gravity * dt  # Apply full gravity acceleration

    def draw(self, screen, tile_size, cam_x=0, cam_y=0):
        # Appliquer l'offset de la caméra et inverser Y pour que positif = vers le haut
        draw_x = self.x * tile_size + cam_x
        draw_y = -self.y * tile_size + cam_y
        pygame.draw.rect(screen, (255, 0, 0), (draw_x, draw_y, self.rect[2], self.rect[3]))