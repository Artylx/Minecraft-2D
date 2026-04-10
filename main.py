import pygame
from classes import game_property, entity, world, tchat, game_type, ui
from classes.texture_manager import TextureManager
from classes.inventory import Crafting_types
import random

PLAYER_NAME = "Player1"

class Game:
    pass

class World_manager:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("TeraCraft")
        info = pygame.display.Info()

        WIDTH, HEIGHT = 1800, 1000 # info.current_w, info.current_h

        self.HEIGHT_SCREEN = HEIGHT
        self.WIDTH_SCREEN = WIDTH

        self.screen = pygame.display.set_mode((self.WIDTH_SCREEN, self.HEIGHT_SCREEN), pygame.RESIZABLE)
        self.cam_rect = pygame.Rect(0, 0, self.WIDTH_SCREEN, self.HEIGHT_SCREEN)
        
        self.load_texture()

        self.tchat = tchat.Tchat((self.WIDTH_SCREEN, self.HEIGHT_SCREEN))
        tchat.CommandManager.game = self
        self.tchat.send_message("", "Bienvenue sur le serveur de TeraCraft")

        self.clock = pygame.time.Clock()
        self.running = True
        self.update_rate = game_property.UPDATE_RATE
        self.highlight = True

        self.keys_ = {}
        self.prev_keys_ = {}
        self.toogle_ = {}

        self.debug_font = pygame.font.SysFont(None, 24)
        self.fps_history = []
        self.debug_timer = 0
        self.debug_surface = None

        self.old_current_bock_pos = None
        self.current_block_pos = None
        self.mouse_pos_world = None

        seed = random.randint(100000, 999999)

        json = world.load_world_json("world_saved")
        print(json)

        # self.World = world.World(seed=seed, screen_size=(self.WIDTH_SCREEN, self.HEIGHT_SCREEN), name="world_saved")

        self.World = world.World((WIDTH, HEIGHT), name="world_saved", json_data=json)

        player = self.World.get_player_by_name(PLAYER_NAME)
        if player:
            self.player = player
        else:
            self.player = entity.Player(self.World, name=PLAYER_NAME)
            self.World.create_entity(self.player)

        self.UI = ui.UI((WIDTH, HEIGHT), self.player.inventory, self.tchat)

        self.update_screen_size(WIDTH, HEIGHT)
        print(f"Seed {self.World.seed}")

    def load_texture(self):
        self.texture_manager = TextureManager()
        self.texture_manager.load_default_textures()

        from classes.world import Block
        Block.texture_manager = self.texture_manager

        from classes.inventory import ItemStack
        ItemStack.texture_manager = self.texture_manager

        from classes.entity import Entity
        Entity.texture_manager = self.texture_manager

        from classes.game_type import ItemProperty
        ItemProperty.texture_manager = self.texture_manager

    # START GAME
    def run(self):
        dt = 1 / self.update_rate

        accumulator = 0
        previous_time = pygame.time.get_ticks() / 1000

        while self.running:
            current_time = pygame.time.get_ticks() / 1000
            frame_time = current_time - previous_time
            previous_time = current_time

            accumulator += frame_time

            # --- Update (fixed) ---
            max_updates = 5
            updates = 0

            while accumulator >= dt and updates < max_updates:
                self.handle_events()

                self.update(dt)
                accumulator -= dt
                updates += 1

            # --- Render (free) ---

            # compute current frame rate from measured frame_time for an unconstrained loop
            if frame_time > 0:
                self.frame_rate = 1.0 / frame_time
            else:
                self.frame_rate = 0.0

            self.fps_history.append(self.frame_rate)
            if len(self.fps_history) > 60:
                self.fps_history.pop(0)

            self.fps = sum(self.fps_history) / len(self.fps_history)

            self.render()

        pygame.quit()

    # EVENT PYGAME
    def handle_events(self):    
        self.prev_keys_ = self.keys_.copy()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.World.save_world()
            if event.type == pygame.KEYDOWN:
                self.event_keydown(event.key)

                if self.tchat.oppened:
                    self.tchat.key_down(event, self.player)
                elif self.UI.is_open_inv():
                    self.UI.key_down(event)
                else:
                    if self.keys_.get(pygame.K_ESCAPE):
                        self.running = False
            if event.type == pygame.KEYUP:
                self.event_keyup(event.key)
            if event.type == pygame.VIDEORESIZE:
                self.update_screen_size(event.w, event.h)
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.event_keydown(self.event_mouse_get(event.button))
            if event.type == pygame.MOUSEBUTTONUP:
                self.event_keyup(self.event_mouse_get(event.button))
            if event.type == pygame.MOUSEWHEEL:
                self.mouse_scroll(event.y)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x, world_y = game_property.screen_to_world(mouse_x, mouse_y, 0, self.cam_rect)

        tile_x = int(world_x // game_property.TILE_SIZE)
        tile_y = int(world_y // game_property.TILE_SIZE)

        self.old_current_bock_pos = self.current_block_pos
        self.current_block_pos = (tile_x, tile_y)
        self.mouse_pos_world = (world_x, world_y)

    def event_mouse_get(self, button):
        return f"mouse{button}"

    def update_cam_rect(self):
        self.cam_rect.centerx = self.player.rect.centerx
        self.cam_rect.centery = self.player.rect.centery

    def update_screen_size(self, width, height):
        self.WIDTH_SCREEN = width
        self.HEIGHT_SCREEN = height

        screen_size = (self.WIDTH_SCREEN, self.HEIGHT_SCREEN)

        self.screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)

        self.cam_rect.width = width
        self.cam_rect.height = height

        self.update_cam_rect()

        self.UI.update_screen_size(screen_size)

    def event_keydown(self, key):
        self.keys_[key] = True
        self.toogle_[key] = not self.toogle_.get(key, False)

    def mouse_scroll(self, y):
        if not self.tchat.oppened and not self.UI.is_open_inv():
            if y < 0:
                self.player.inventory.ui.move_selected_index(1)
            elif y > 0:
                self.player.inventory.ui.move_selected_index(-1)
        else:
            if self.tchat.oppened:
                if y < 0:
                    self.tchat.offset_msg_index_move(-1)
                elif y > 0:
                    self.tchat.offset_msg_index_move(1)

    def event_keyup(self, key):
        self.keys_[key] = False

    # UPDATE
    def update(self, dt):
        if self.toogle_.get(pygame.K_F3):
            self.update_debug(dt)

        if not self.tchat.oppened and not self.UI.is_open_inv():
            # horizontal movement: adjust velocity directly
            if self.keys_.get(pygame.K_d) and not self.keys_.get(pygame.K_q):
                self.player.add_velocity(1, 0)
            elif self.keys_.get(pygame.K_q) and not self.keys_.get(pygame.K_d):
                self.player.add_velocity(-1, 0)

            # jump input: only apply when player is on ground
            if self.keys_.get(pygame.K_SPACE) and self.player.on_ground:
                self.player.add_velocity(0, game_property.JUMP_VELOCITY)
                self.player.on_ground = False

            # Breaking
            selected_item = self.player.inventory.ui.get_selected_item()
            if selected_item is None or not isinstance(selected_item.item_property, game_type.Attack_tool):
                if self.keys_.get(self.event_mouse_get(1)):
                    # Try break
                    if self.old_current_bock_pos == self.current_block_pos:
                        self.World.try_destroy_block(self.current_block_pos, self.player)
                    else:
                        self.World.reset_block(self.old_current_bock_pos)
                else:
                    if self.prev_keys_.get(self.event_mouse_get(1)):
                        self.World.reset_block(self.current_block_pos)
            
            # Attacking
            if self.keys_.get(self.event_mouse_get(1)):
                if not self.prev_keys_.get(self.event_mouse_get(1)):
                    # ATTACK
                    
                    self.player.try_attack(self.cam_rect)
                        

            if self.keys_.get(self.event_mouse_get(3)):
                self.click_on_block(self.current_block_pos, self.player)
                self.pos_block(self.current_block_pos, self.player)

            if self.keys_.get(pygame.K_t):
                self.tchat.oppened = True

            # Spawning for debug
            if self.keys_.get(pygame.K_m) and not self.prev_keys_.get(pygame.K_m):
                z = entity.Zobmie(self.World)
                z.tp(self.player.get_pos()[0], self.player.get_pos()[1] + 1000)
                self.World.create_entity(z)
            if self.keys_.get(pygame.K_p) and not self.prev_keys_.get(pygame.K_p):
                p = entity.Player(self.World, "Player2")
                p.tp(self.player.get_pos()[0], self.player.get_pos()[1] + 1000)
                self.World.create_entity(p)

                self.tchat.send_message(p.name, "Salut les gens !")
            
            if self.keys_.get(pygame.K_e):
                self.UI.open_inv(self.player.inventory)
            
            if self.keys_.get(pygame.K_a):
                self.player.drop_item()

        elif self.UI.is_open_inv():
            if self.keys_.get(self.event_mouse_get(1)):
                if not self.prev_keys_.get(self.event_mouse_get(1)):
                    self.UI.mouse_down(1)
            else:
                if self.prev_keys_.get(self.event_mouse_get(1)):
                    self.UI.mouse_up(1)
            
            if self.keys_.get(self.event_mouse_get(3)):
                if not self.prev_keys_.get(self.event_mouse_get(3)):
                    self.UI.mouse_down(3)
            else:
                if self.prev_keys_.get(self.event_mouse_get(3)):
                    self.UI.mouse_up(3)
            

        # forward world update handles gravity and actual movement
        self.World.update(dt)
        self.update_cam_rect()
        self.UI.update_pos_cam_rect(self.player.get_pos())
    
    def mouse_up(self, button):
        if self.UI.is_open_inv():
            self.UI.mouse_up(button)

    def click_on_block(self, pos_block, player):
        # centre du bloc
        block_center_x = pos_block[0] * game_property.TILE_SIZE + game_property.TILE_SIZE / 2
        block_center_y = pos_block[1] * game_property.TILE_SIZE + game_property.TILE_SIZE / 2

        # centre du joueur
        player_center_x = player.rect.centerx
        player_center_y = player.rect.centery

        dx = block_center_x - player_center_x
        dy = block_center_y - player_center_y

        if dx*dx + dy*dy > game_property.MAX_ACTION_DISTANCE**2:
            return
        
        old_block = self.World.get_block(pos_block[0], pos_block[1])

        if old_block:
            if old_block.block_property == game_type.BlockProperty.AIR:
                self.pos_block(pos_block, player)
            else:
                if old_block.block_property == game_type.BlockProperty.CRAFTING_TABLE:
                    
                    self.UI.open_inv(player.inventory, Crafting_types.CRAFTING_TABLE)

    def pos_block(self, pos_block, player):
        current_item = player.inventory.ui.get_selected_item()
        if current_item and current_item.is_posable():

            old_block = self.World.get_block(pos_block[0], pos_block[1])

            if pos_block[1] > game_property.CHUNK_MAX_HEIGHT:
                self.tchat.send_message("", f"&4Couche maximal {game_property.CHUNK_MAX_HEIGHT}")
                return

            if old_block and old_block.block_property == world.BlockProperty.AIR:

                block_property = game_type.get_block_property(current_item.item_property.item_name)

                if block_property:
                    if self.World.set_block(
                        pos_block[0],
                        pos_block[1],
                        world.Block(
                            pos_block[0],
                            pos_block[1],
                            block_property,
                        )
                    ):

                        player.inventory.delete_item(player.inventory.ui.selected_index)

    # RENDER
    def render(self):
        pygame.draw.rect(self.screen, (135, 206, 235), (0, 0, self.WIDTH_SCREEN, self.HEIGHT_SCREEN))  # Fond bleu ciel

        self.World.render(self.screen, self.cam_rect)

        if self.toogle_.get(pygame.K_F3):
            self.World.hit_box_visible = True
            self.render_debug()
            self.World.render_debug(self.screen)
        else:
            self.World.hit_box_visible = False

        if self.highlight and not self.tchat.oppened and not self.UI.is_open_inv():
            self.UI.highlight_block(self.screen, self.current_block_pos, self.cam_rect)

        self.World.render_entitys(self.screen, self.cam_rect)

        self.UI.render(self.screen, self.player)
        
        pygame.display.flip()

    def update_debug(self, dt):
        self.debug_timer += dt

        if self.debug_timer > 0.10:
            self.debug_timer = 0

            player_block_x = int(self.player.rect.x / game_property.TILE_SIZE)

            biome = self.World.biome_manager.get_biome_at(player_block_x, abs(hash(self.World.seed)) % 1024)

            # ✅ conversion sûre en nom
            if biome is None:
                biome_name = "Unknown"
            else:
                biome_name = biome.name

            # première lettre majuscule
            biome_name = biome_name[0].upper() + biome_name[1:].lower()

            debug_text = (
                f"FPS: {int(self.fps)}\n"
                f"X: {(self.player.rect.x / game_property.TILE_SIZE):.1f}, "
                f"Y: {(self.player.rect.y / game_property.TILE_SIZE):.1f}\n"
                f"Biome: {biome_name}"
            )

            lines = debug_text.split("\n")
            self.debug_surface = [
                self.debug_font.render(line, True, (0, 0, 0))
                for line in lines
            ]

    def render_debug(self):
        if not self.debug_surface:
            return

        y = 10
        for surf in self.debug_surface:
            self.screen.blit(surf, (10, y))
            y += 20
    

if __name__ == "__main__": 
    try: 
        world_manager = World_manager() 
        world_manager.run()
    except Exception as e: 
        import traceback 
        traceback.print_exc() 
        input("Crash - press enter")