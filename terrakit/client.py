import pygame
import random, json
from terrakit import tchat, world, game_property, game_type, entity, ui, interface
from server import ServerConnection

class GameClient:
    def __init__(self, world_path, world_name, width, height, callback, game, player_name, texture_manager):
        self.width_screen = width
        self.height_screen = height
        self.cam_rect = pygame.Rect(0, 0, self.width_screen, self.height_screen)
        self.texture_manager = texture_manager

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
            
        self.World = world.WorldSolo(name=self.world_name, json_data=json, seed=seed, callback_loading=callback)

        self.player_name = player_name

        self.player = None
        self.UI = None
        if self.World.player_is_offline(self.player_name):
            self.spawn_player()
        else:
            game.died()

        self.update_screen_size(self.width_screen, self.height_screen)
        print(f"Seed {self.World.seed}")

    def spawn_player(self):
        self.player = self.World.player_join(self.player_name)
        self.UI = ui.UI((self.width_screen, self.height_screen), self.player.inventory, self.tchat, self.texture_manager)

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
        if self.player:
            self.cam_rect.center = (
                int(self.player.rect.centerx),
                int(self.player.rect.centery)
            )

    def update_screen_size(self, width, height):
        self.width_screen = width
        self.height_screen = height

        screen_size = (self.width_screen, self.height_screen)

        self.cam_rect.width = width
        self.cam_rect.height = height

        self.update_cam_rect()

        if self.UI:
            self.UI.update_screen_size(screen_size)

    # UPDATE
    def update(self, dt, game):

        if not self.player.is_alive:
            game.died()
            return

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
                z = entity.Zombie(world=self.World)
                z.tp(self.player.get_pos()[0], self.player.get_pos()[1] + 1000)
                self.World.create_entity(z)

            if game.is_press(pygame.K_l):
                z = entity.Alien(world=self.World)
                z.tp(self.player.get_pos()[0], self.player.get_pos()[1] + 1000)
                self.World.create_entity(z)
                
            if game.is_press(pygame.K_p):
                p = entity.Player(world=self.World, name="Player2")
                p.tp(self.player.get_pos()[0], self.player.get_pos()[1] + 1000)
                self.World.create_entity(p)

                self.tchat.send_message(p.name, "Salut les gens !")

            if game.is_press(pygame.K_o):
                p = entity.Npc(world=self.World, name="Armurier")
                p.tp(self.player.get_pos()[0], self.player.get_pos()[1] + 1000)
                self.World.create_entity(p)
            
            if game.is_press(pygame.K_e):
                self.UI.open_crafting(self.player.inventory)
            
            if game.is_press(pygame.K_a):
                self.player.drop_item_index()

            if game.is_press(pygame.K_ESCAPE):
                game.menu.set_menu(interface.MenusCollection.GAME_PAUSED)

            if game.mouse_scroll_y != 0:
                if game.mouse_scroll_y > 0:
                    self.player.inventory.ui.move_selected_index(1)
                else:
                    self.player.inventory.ui.move_selected_index(-1)

        elif self.UI.is_open_inv():
            if game.is_press(pygame.K_ESCAPE) or game.is_press(pygame.K_e):
                self.UI.close_inv()

        elif self.tchat.oppened:

            if game.mouse_scroll_y != 0:
                if game.mouse_scroll_y > 0:
                    self.tchat.offset_msg_index_move(1)
                else:
                    self.tchat.offset_msg_index_move(-1)

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
        self.UI.update(dt)

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
                self.World.add_modified_block(old_block.get_pos()[0], old_block.get_pos()[1])

                if old_block.block_property == game_type.BlockProperty.CRAFTING_TABLE:
                    
                    self.UI.open_crafting(player.inventory, ui.Crafting_types.CRAFTING_TABLE)
                    return True
                elif old_block.block_property == game_type.BlockProperty.FURNACE:

                    self.UI.open_furnace(player.inventory, old_block)
                    return True
                elif old_block.block_property == game_type.BlockProperty.CHEST or old_block.block_property == game_type.BlockProperty.IRON_CHEST:

                    self.UI.open_inv(player.inventory, old_block)
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

        if self.player:
            self.World.render(screen, self.cam_rect)

            if game.toogle_.get(pygame.K_F3):
                self.World.hit_box_visible = True
                self.render_debug(screen)
                #self.World.render_debug(screen, self.cam_rect)
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
                f"Biome: {biome_name}\n"
                f"Entitys: {len(self.World.get_entities())}\n"
                f"Seed: {self.World.seed}\n"
                f"World: {self.World.name}\n"
                f"Player: {self.player.name}\n"
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

        pygame.draw.line(
            screen,
            (0, 255, 0),
            (0, self.height_screen // 2),
            (self.width_screen, self.height_screen // 2),
            1
        )

        pygame.draw.line(
            screen,
            (0, 255, 0),
            (self.width_screen // 2, 0),
            (self.width_screen // 2, self.height_screen),
            1
        )


class MultiplayerClient():
    def __init__(self, game, player_name, server_ip, server_port, width_screen, height_screen):
        self.width_screen = width_screen
        self.height_screen = height_screen
        self.cam_rect = pygame.Rect(0, 0, self.width_screen, self.height_screen)

        self.clock = pygame.time.Clock()
        self.running = True
        self.update_rate = game_property.UPDATE_RATE
        self.highlight = True

        self.server_ip = server_ip
        self.server_port = server_port
        self.server_connection = ServerConnection(self.server_ip, self.server_port)

        self.server_connection.send_join(player_name)

        self.player_name = player_name
        self.world = None
        self.game = game
        self.player = None

        self.debug_font = pygame.font.SysFont(None, 24)
        self.fps_history = []
        self.debug_timer = 0
        self.debug_surface = None

        self.old_current_bock_pos = None
        self.current_block_pos = None
        self.mouse_pos_world = None

        self.tchat = tchat.Tchat((self.width_screen, self.height_screen))
        tchat.CommandManager.game = self
        self.tchat.send_message("", "Bienvenue sur le serveur de TeraCraft")

    def is_connected(self):
        return not self.server_connection.disconnected

    def update(self, dt, game):

        if self.world and self.player:
            inputs = {
                "action": "input",
                "left": game.keys_.get(pygame.K_q) or game.keys_.get(pygame.K_LEFT),
                "right": game.keys_.get(pygame.K_d) or game.keys_.get(pygame.K_RIGHT),
                "up": game.keys_.get(pygame.K_SPACE) or game.keys_.get(pygame.K_UP),
            }

            self.world.update(dt)

            self.apply_inputs_locally(inputs, dt)

            # 2. SEND TO SERVER
            self.server_connection.send_inputs(inputs)

            state = self.server_connection.get_state()

            if state:
                if state.get("type") == "snapshot":
                    self.apply_server_state(state)
                    

            if not self.tchat.oppened and not self.UI.is_open_inv():
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
                
                if game.is_press(pygame.K_e):
                    self.UI.open_crafting(self.player.inventory)

                if game.is_press(pygame.K_ESCAPE):
                    game.menu.set_menu(interface.MenusCollection.GAME_PAUSED)

                if game.mouse_scroll_y != 0:
                    if game.mouse_scroll_y > 0:
                        self.player.inventory.ui.move_selected_index(1)
                    else:
                        self.player.inventory.ui.move_selected_index(-1)

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

            self.update_cam_rect()

        else:
            state = self.server_connection.get_state()

            if state:
                if state.get("type") == "world_init":
                    print(state)

                    self.load_world_from_server(state)

            if not self.player and self.world:
                self.player = self.world.get_player_by_name(self.player_name)

                self.UI = ui.UI((self.width_screen, self.height_screen), self.player.inventory, self.tchat)
    
    def render(self, game, screen):
        pygame.draw.rect(screen, (135, 206, 235), (0, 0, self.width_screen, self.height_screen))

        self.world.render(screen, self.cam_rect)

        if game.toogle_.get(pygame.K_F3):
            self.world.hit_box_visible = True
            self.render_debug(screen)
            self.world.render_debug(screen, self.cam_rect)
        else:
            self.world.hit_box_visible = False

        if self.highlight and not self.tchat.oppened and not self.UI.is_open_inv():
            self.UI.highlight_block(screen, self.current_block_pos, self.cam_rect, self.player)

        self.world.render_entitys(screen, self.cam_rect)

        self.UI.render(screen, self.player)

    def load_world_from_server(self, world_data):
        print("World reçu du serveur")

        self.world = world.World(name=world_data.get("world_name"), json_data=world_data.get("world"), callback_loading=self.game.end_loading)

    def apply_inputs_locally(self, inputs, dt):
        speed = 200

        vx = 0

        if inputs["left"]:
            vx -= speed
        if inputs["right"]:
            vx += speed

        self.player.add_velocity(vx * dt, 0)

        if inputs["up"] and self.player.on_ground:
            self.player.jump(game_property.JUMP_VELOCITY)

    def update_cam_rect(self):
        self.cam_rect.centerx = self.player.rect.centerx
        self.cam_rect.centery = self.player.rect.centery

    def apply_server_state(self, state):
        return
    
        server_x = state["x"]
        server_y = state["y"]

        player = self.player

        # erreur entre client et server
        dx = server_x - player.rect.x
        dy = server_y - player.rect.y

        # correction douce (NE PAS TELEPORT)
        correction_factor = 0.2

        player.rect.x += dx * correction_factor
        player.rect.y += dy * correction_factor

    def apply_server_state(self, state):
        if not state:
            return
        entitys_remove = self.world.get_entities().copy()

        # exemple minimal
        for e in state.get("entitys"):
            uuid = e.get("uuid", None)

            if uuid:
                current_entity = self.world.get_entity(uuid)

                if current_entity:
                    self.update_entity(current_entity, (e.get("x"), e.get("y")), (e.get("vx"), e.get("vy")))
                    entitys_remove.remove(current_entity)
                else:
                    self.world.create_entity(entity.dict_to_entity(e, self.world))

        for e in entitys_remove:
            self.world.remove_entity(e)

    def update_entity(self, entity, pos, vel):
        dx = pos[0] - entity.rect.x
        dy = pos[1] - entity.rect.y

        correction_factor = 0.15

        entity.rect.x += dx * correction_factor
        entity.rect.y += dy * correction_factor

        entity.set_velocity(vel[0], vel[1])



    def handle_events(self):
        pass