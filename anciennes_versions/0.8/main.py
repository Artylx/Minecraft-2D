import pygame
from terrakit.world import World
import terrakit.game_property as game_property

SCREEN_SIZE = (800, 600)

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("2D Block Game")

        self.HEIGHT_SCREEN = 1200
        self.WIDTH_SCREEN = 1600

        self.screen = pygame.display.set_mode((self.WIDTH_SCREEN, self.HEIGHT_SCREEN))
        self.clock = pygame.time.Clock()
        self.running = True
        self.update_rate = game_property.UPDATE_RATE

        from terrakit.world import Block
        Block.texture_manager.load_default_textures()

        self.WORLD = World(seed=12345, name="My World", width=self.WIDTH_SCREEN, height=self.HEIGHT_SCREEN)

        self.keys_ = {}

    def run(self):
        dt = 1 / self.update_rate

        accumulator = 0
        previous_time = pygame.time.get_ticks() / 1000

        while self.running:
            current_time = pygame.time.get_ticks() / 1000
            frame_time = current_time - previous_time
            previous_time = current_time

            accumulator += frame_time

            # --- Events ---
            self.handle_events()

            # --- Update (fixed) ---
            while accumulator >= dt:
                self.update(dt)
                accumulator -= dt

            # --- Render (free) ---
            self.render()

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.keys_["right"] = True
                elif event.key == pygame.K_LEFT:
                    self.keys_["left"] = True
                elif event.key == pygame.K_DOWN:
                    self.keys_["down"] = True
                elif event.key == pygame.K_UP:
                    self.keys_["up"] = True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    self.keys_["right"] = False
                elif event.key == pygame.K_LEFT:
                    self.keys_["left"] = False
                elif event.key == pygame.K_DOWN:
                    self.keys_["down"] = False
                elif event.key == pygame.K_UP:
                    self.keys_["up"] = False

    def update(self, dt):
        direction_x = None
        if self.keys_.get("right") and not self.keys_.get("left"):
            direction_x = "right"
        elif self.keys_.get("left") and not self.keys_.get("right"):
            direction_x = "left"
        else:
            direction_x = None

        direction_y = None
        if self.keys_.get("down") and not self.keys_.get("up"):
            direction_y = "down"
        elif self.keys_.get("up") and not self.keys_.get("down"):
            direction_y = "up"
        else:
            direction_y = None
        self.WORLD.move_camera(direction_x, direction_y, dt)
        
        self.WORLD.update(dt)

    def render(self):
        pygame.draw.rect(self.screen, (135, 206, 235), (0, 0, self.WIDTH_SCREEN, self.HEIGHT_SCREEN))  # Fond bleu ciel

        self.WORLD.render(self.screen)
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()