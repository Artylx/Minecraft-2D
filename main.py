from importlib.resources import path

import pygame
from tomlkit import value
from classes import game_property, entity, interface, world, tchat, game_type, ui
from classes.texture_manager import TextureManager
from classes.inventory import Crafting_types
import random
import os
import shutil

from classes import debug

class Game:
    def __init__(self):
        self.title = "TeraCraft"

        pygame.init()
        pygame.display.set_caption(self.title)
        self.info = pygame.display.Info()

        self.WIDTH, self.HEIGHT = 1800, 1000

        self.HEIGHT_SCREEN = self.HEIGHT
        self.WIDTH_SCREEN = self.WIDTH

        self.screen = pygame.display.set_mode((self.WIDTH_SCREEN, self.HEIGHT_SCREEN), pygame.RESIZABLE)

        # ICON
        icon = pygame.image.load(game_property.get_resource_path("resource_pack/Default/texture/blocks/grass_block.png")).convert_alpha()
        pygame.display.set_icon(icon)

        self.clock = pygame.time.Clock()
        self.running = True
        self.update_rate = game_property.UPDATE_RATE
        self.game_manager = None
        self.game_name = ""

        self.fps_history = []

        self.full_screen = False

        self.press_reset()

        self.menu = interface.MainMenu(self)

        self.load_texture()

        if debug.AUTO_START["enable"]:
            self.select_world(debug.AUTO_START["world_name"])
            self.load_game(debug.AUTO_START["player_name"])

    def select_world(self, game_name):
        self.press_reset()
        self.menu.set_menu(interface.MenusCollection.PSEUDO)

        self.game_name = game_name

    def load_game(self, pseudo):
        self.press_reset()
        self.menu.set_loading("On s'occupe de poser les blocks...", 10)

        self.game_manager = Game_manager(self.game_name, self.game_manager, self.WIDTH_SCREEN, self.HEIGHT_SCREEN, callback=self.end_loading, game=self, player_name=pseudo)

    def end_loading(self, message="", value=0):
        self.menu.set_loading(message, value)

        if value >= 100:
            print(f"Value {value}")
            self.menu.set_menu(interface.MenusCollection.GAME)

    def select_tuto(self):
        world_name = "Monde tutoriel"

        self.delete_world(world_name)

        os.makedirs("worlds\\" + world_name)
        self.select_world(world_name)

    def create_world(self):
        obj_lst = self.menu.menus[interface.MenusCollection.CREATE_WORLD]

        name = None
        seed = None

        for obj in obj_lst:
            if isinstance(obj, interface.TextBox):

                # TextBox
                if obj.is_ref("world_name"):
                    if obj.text.strip() != "":
                        name = obj.text
        path = game_property.get_resource_path(f"worlds\\{name}")

        if not os.path.exists(path):
            os.makedirs(path)
            self.select_world(name)
        else:
            print("Le nom du monde existe déjà")

    def stop_game(self):
        if self.game_is_start():
            self.game_manager.running = False

            self.game_manager.World.stop()

            print("Saving world...")
            print("Path: ", self.game_manager.world_path, "Name: ", self.game_manager.world_name)

            world.save_world_json(self.game_manager.World, self.game_manager.world_path, "world")
            self.game_manager = None

            self.press_reset()
            self.menu.set_menu(interface.MenusCollection.MAIN)

    def game_is_start(self):
        return self.game_manager is not None

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

        from classes.interface import MainMenu
        MainMenu.texture_manager = self.texture_manager
        self.menu.reload()

    def update_full_screen(self):
        if self.full_screen:
            self.screen = pygame.display.set_mode(
                (self.info.current_w, self.info.current_h),
                pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(
                (self.WIDTH, self.HEIGHT),
                pygame.RESIZABLE
            )

        self.update_screen_size(self.screen.get_width(), self.screen.get_height())

    def update_screen_size(self, width, height):
        self.WIDTH_SCREEN = width
        self.HEIGHT_SCREEN = height

        self.menu.update_screen_size(width, height)

        if self.game_is_start():
            self.game_manager.update_screen_size(width, height)

    def quit(self):
        self.running = False

    def run(self):
        dt = 1 / self.update_rate

        accumulator = 0
        previous_time = pygame.time.get_ticks() / 1000

        while self.running:
            current_time = pygame.time.get_ticks() / 1000
            frame_time = current_time - previous_time
            previous_time = current_time

            accumulator += frame_time

            # --- Update ---
            max_updates = 5
            updates = 0

            while accumulator >= dt and updates < max_updates:
                self.handle_events()

                self.update(dt)
                accumulator -= dt
                updates += 1

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

    def handle_events(self):    
        self.prev_keys_ = self.keys_.copy()
        self.mouse_scroll(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.event_keydown(pygame.QUIT)

                if self.game_is_start():
                    self.stop_game()
                self.running = False

            if event.type == pygame.KEYDOWN:
                self.event_keydown(event.key)

                if self.game_is_start() and self.game_manager.tchat.oppened:
                    self.game_manager.tchat.key_down(event, self.game_manager.player)

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

            if not self.menu.is_menu(interface.MenusCollection.GAME):
                self.menu.handle_events(event)

        if self.menu.is_menu(interface.MenusCollection.GAME) and self.game_is_start():
            self.game_manager.handle_events()

    def delete_world_func(self, world_name):
        self.delete_world(world_name)

        self.menu.reload()
        self.menu.set_menu(interface.MenusCollection.SINGLEPLAYER)

    def delete_world(self, world_name):
        path = game_property.get_resource_path(f"worlds\\{world_name}")

        if os.path.exists(path):
            shutil.rmtree(path)
    
    def is_press(self, key):
        return self.keys_.get(key) and not self.prev_keys_.get(key)
    
    def is_holding(self, key):
        return self.keys_.get(key) and self.prev_keys_.get(key)

    def is_release(self, key):
        return not self.keys_.get(key) and self.prev_keys_.get(key)

    def press_reset(self):
        self.keys_ = {}
        self.prev_keys_ = {}
        self.toogle_ = {}
    
    def mouse_scroll(self, y):
        self.mouse_scroll_y = y
    
    def event_keyup(self, key):
        self.keys_[key] = False
    
    def event_mouse_get(self, button):
        return f"mouse{button}"

    def event_keydown(self, key):
        self.keys_[key] = True
        self.toogle_[key] = not self.toogle_.get(key, False)

    def update(self, dt):
        if self.is_press(pygame.K_F11):
            self.full_screen = not self.full_screen
            self.update_full_screen()
            print("Update full screen")

        if self.menu.is_menu(interface.MenusCollection.GAME) or self.menu.is_menu(interface.MenusCollection.LOADING_WORLD) and self.game_is_start():
            self.game_manager.update(dt, self)
        else:
            self.menu.update(dt)

    def render(self):
        if self.game_is_start():
            if not self.menu.is_menu(interface.MenusCollection.LOADING_WORLD):
                self.game_manager.render(self, self.screen)

            #Couche d'opacité
            if self.menu.menus[self.menu.menu] != [] and not self.menu.is_menu(interface.MenusCollection.LOADING_WORLD):
                overlay = pygame.Surface((self.WIDTH_SCREEN, self.HEIGHT_SCREEN), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 120))

                self.screen.blit(overlay, (0, 0))

            self.menu.render(self.screen)
        else:
            self.screen.fill((135, 206, 235))
            self.menu.render(self.screen)
        pygame.display.flip()


class Game_manager:
    def __init__(self, world_path, world_name, width, height, callback, game, player_name):
        self.width_screen = width
        self.height_screen = height
        self.cam_rect = pygame.Rect(0, 0, self.width_screen, self.height_screen)

        self.tchat = tchat.Tchat((self.width_screen, self.height_screen))
        tchat.CommandManager.game = self
        self.tchat.send_message("", "Bienvenue sur le serveur de TeraCraft")

        self.clock = pygame.time.Clock()
        self.running = True
        self.update_rate = game_property.UPDATE_RATE
        self.highlight = True

        self.debug_font = pygame.font.SysFont(None, 24)
        self.fps_history = []
        self.debug_timer = 0
        self.debug_surface = None

        self.old_current_bock_pos = None
        self.current_block_pos = None
        self.mouse_pos_world = None

        seed = random.randint(100000, 999999)

        self.world_name = world_name
        self.world_path = world_path
        self.game = game

        json = None
        if self.world_path:
            json = world.load_world_json(self.world_path)
            
        self.World = world.World((self.width_screen, self.height_screen), name=self.world_name, json_data=json, seed=seed, callback_loading=callback)

        self.player = self.World.player_join(player_name)

        self.UI = ui.UI((self.width_screen, self.height_screen), self.player.inventory, self.tchat)

        self.update_screen_size(self.width_screen, self.height_screen)
        print(f"Seed {self.World.seed}")

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

        return False

    # EVENT PYGAME
    def handle_events(self):
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
        self.width_screen = width
        self.height_screen = height

        screen_size = (self.width_screen, self.height_screen)

        self.cam_rect.width = width
        self.cam_rect.height = height

        self.update_cam_rect()

        self.UI.update_screen_size(screen_size)
        self.World.update_screen_size(screen_size)

    # UPDATE
    def update(self, dt, game):
        if game.toogle_.get(pygame.K_F3):
            self.update_debug(dt)
        else:
            self.update_debug(0)

        if not self.tchat.oppened and not self.UI.is_open_inv():
            # horizontal movement: adjust velocity directly
            if (game.keys_.get(pygame.K_d) and not game.keys_.get(pygame.K_q)) or (game.keys_.get(pygame.K_RIGHT) and not game.keys_.get(pygame.K_LEFT)):
                self.player.add_velocity(1, 0)
            elif game.keys_.get(pygame.K_q) and not game.keys_.get(pygame.K_d) or (game.keys_.get(pygame.K_LEFT) and not game.keys_.get(pygame.K_RIGHT)):
                self.player.add_velocity(-1, 0)

            if (game.keys_.get(pygame.K_SPACE) or game.keys_.get(pygame.K_UP)) and self.player.on_ground:
                self.player.jump(game_property.JUMP_VELOCITY)

            # Breaking
            selected_item = self.player.inventory.ui.get_selected_item()
            if selected_item is None or not isinstance(selected_item.item_property, game_type.Attack_tool):
                if game.is_holding(self.event_mouse_get(1)):
                    # Try break
                    if self.old_current_bock_pos == self.current_block_pos:
                        self.World.try_destroy_block(self.current_block_pos, self.player)
                    else:
                        self.World.reset_block(self.old_current_bock_pos)
                else:
                    if game.prev_keys_.get(self.event_mouse_get(1)):
                        self.World.reset_block(self.current_block_pos)
            
            # Attacking
            if game.is_press(self.event_mouse_get(1)):

                self.player.try_attack(self.cam_rect)
                        
            # Pos or other
            if game.is_press(self.event_mouse_get(3)):
                self.click_on_block(self.current_block_pos, self.player)
                self.player.use_selected_item(self.cam_rect)    
            else:
                if game.is_release(self.event_mouse_get(3)):
                    self.player.stop_use_selected_item(self.cam_rect)

            if game.is_press(pygame.K_t):
                self.tchat.oppened = True

            # Index selected hotbar
            if game.is_press(pygame.K_1):
                self.player.inventory.ui.set_selected_index(0)
            if game.is_press(pygame.K_2):
                self.player.inventory.ui.set_selected_index(1)
            if game.is_press(pygame.K_3):
                self.player.inventory.ui.set_selected_index(2)
            if game.is_press(pygame.K_4):
                self.player.inventory.ui.set_selected_index(3)
            if game.is_press(pygame.K_5):
                self.player.inventory.ui.set_selected_index(4)
            if game.is_press(pygame.K_6):
                self.player.inventory.ui.set_selected_index(5)

            # Spawning for debug
            if game.is_press(pygame.K_m):
                z = entity.Zobmie(self.World)
                z.tp(self.player.get_pos()[0], self.player.get_pos()[1] + 1000)
                self.World.create_entity(z)
            if game.is_press(pygame.K_p):
                p = entity.Player(self.World, "Player2")
                p.tp(self.player.get_pos()[0], self.player.get_pos()[1] + 1000)
                self.World.create_entity(p)

                self.tchat.send_message(p.name, "Salut les gens !")
            
            if game.is_press(pygame.K_e):
                self.UI.open_inv(self.player.inventory)
            
            if game.is_press(pygame.K_a):
                self.player.drop_item()

            if game.is_press(pygame.K_ESCAPE):
                game.menu.set_menu(interface.MenusCollection.GAME_PAUSED)

        elif self.UI.is_open_inv():
            if game.is_press(pygame.K_ESCAPE) or game.is_press(pygame.K_e):
                self.UI.close_inv()

        if game.keys_.get(game.event_mouse_get(1)):
            if not game.prev_keys_.get(game.event_mouse_get(1)):
                self.UI.mouse_down(1)
        else:
            if game.prev_keys_.get(game.event_mouse_get(1)):
                self.UI.mouse_up(1)
        
        if game.keys_.get(game.event_mouse_get(3)):
            if not game.prev_keys_.get(game.event_mouse_get(3)):
                self.UI.mouse_down(3)
        else:
            if game.prev_keys_.get(game.event_mouse_get(3)):
                self.UI.mouse_up(3)
            

        # forward world update handles gravity and actual movement
        self.World.update(dt)
        self.update_cam_rect()
        self.UI.update_pos_cam_rect(self.player.get_pos())

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
            return False
        
        old_block = self.World.get_block(pos_block[0], pos_block[1])

        if old_block:
            if old_block.block_property == game_type.BlockProperty.AIR:
                self.pos_block(pos_block, player)
            else:
                if old_block.block_property == game_type.BlockProperty.CRAFTING_TABLE:
                    
                    self.UI.open_inv(player.inventory, Crafting_types.CRAFTING_TABLE)
                    return True
                elif old_block.block_property == game_type.BlockProperty.FURNACE:

                    self.UI.open_furnace(player.inventory, old_block)
                    return True
                elif old_block.block_property == game_type.BlockProperty.CHEST:

                    self.UI.open_chest(player.inventory, old_block)
                    return True
        return False

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
                    if self.World.modif_block(
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
    def render(self, game, screen):
        pygame.draw.rect(screen, (135, 206, 235), (0, 0, self.width_screen, self.height_screen))

        self.World.render(screen, self.cam_rect)

        if game.toogle_.get(pygame.K_F3):
            self.World.hit_box_visible = True
            self.render_debug(screen)
            self.World.render_debug(screen, self.cam_rect)
        else:
            self.World.hit_box_visible = False

        if self.highlight and not self.tchat.oppened and not self.UI.is_open_inv():
            self.UI.highlight_block(screen, self.current_block_pos, self.cam_rect, self.player)

        self.World.render_entitys(screen, self.cam_rect)

        self.UI.render(screen, self.player)

    def update_debug(self, dt):
        self.debug_timer += dt

        if self.debug_timer > 0.10:
            self.debug_timer = 0

            player_block_x = int(self.player.rect.x / game_property.TILE_SIZE)

            biome = self.World.biome_manager.get_biome_at(player_block_x, abs(hash(self.World.seed)) % 1024)

            if biome is None:
                biome_name = "Unknown"
            else:
                biome_name = biome.name

            # première lettre majuscule
            biome_name = biome_name[0].upper() + biome_name[1:].lower()

            debug_text = (
                f"FPS: {int(self.game.fps)}\n"
                f"X: {(self.player.rect.x / game_property.TILE_SIZE):.1f}, "
                f"Y: {(self.player.rect.y / game_property.TILE_SIZE):.1f}\n"
                f"Biome: {biome_name}"
            )

            lines = debug_text.split("\n")
            self.debug_surface = [
                self.debug_font.render(line, True, (255, 255, 255))
                for line in lines
            ]

    def render_debug(self, screen):
        if not self.debug_surface:
            return

        y = 10
        for surf in self.debug_surface:
            screen.blit(surf, (10, y))
            y += 20
    

if __name__ == "__main__": 
    try: 
        game = Game()
        game.run()
        
    except Exception as e: 
        import traceback 
        traceback.print_exc() 
        input("Crash - press enter")