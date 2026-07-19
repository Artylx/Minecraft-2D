from importlib.resources import path

import pygame
from tomlkit import value
from terrakit import game_property, interface, world
import terrakit
import os
import shutil
import os
import traceback
import datetime
import platform
from terrakit import client
from terrakit import debug
from terrakit.audio_manager import AudioType

import terrakit.config as config

class Game:
    def __init__(self):
        self.title = "TeraCraft"

        pygame.init()
        pygame.display.set_caption(self.title)
        self.info = pygame.display.Info()

        self.WIDTH = int(self.info.current_w * 3 / 4)
        self.HEIGHT = int(self.info.current_h * 3 / 4)

        self.WIDTH_SCREEN = self.WIDTH
        self.HEIGHT_SCREEN = self.HEIGHT

        self.screen = pygame.display.set_mode(
            (self.WIDTH_SCREEN, self.HEIGHT_SCREEN), 
            pygame.RESIZABLE | pygame.DOUBLEBUF
        )

        # ICON
        icon = pygame.image.load(game_property.get_resource_path("resource_pack/Default/texture/blocks/grass_block.png")).convert_alpha()
        pygame.display.set_icon(icon)

        terrakit.init()
        self.texture_manager = terrakit.context.get_resource_pack().texture_manager()
        self.audio_manager = terrakit.context.get_resource_pack().audio_manager()

        self.clock = pygame.time.Clock()
        self.running = True
        self.update_rate = game_property.UPDATE_RATE
        self.game_manager = None
        self.game_name = ""

        self.fps_history = []

        self.full_screen = False

        self.press_reset()

        self.launch_sound = self.audio_manager.get_audio(AudioType.SWEEDEN)

        self.menu = interface.MainMenu(self)

        if debug.AUTO_START["enable"]:
            self.select_world(debug.AUTO_START["world_name"])
            self.load_game(debug.AUTO_START["player_name"])

    def repsawn(self):
        self.press_reset()

        if isinstance(self.game_manager, client.GameClient):
            self.game_manager.spawn_player()

        self.menu.set_menu(interface.MenusCollection.GAME)

    def died(self):
        self.press_reset()
        self.menu.set_menu(interface.MenusCollection.DIED)

    def select_world(self, game_name):
        self.press_reset()
        self.menu.set_menu(interface.MenusCollection.PSEUDO)

        for obj in self.menu.menus[interface.MenusCollection.PSEUDO]:
            if isinstance(obj, interface.TextBox):
                if obj.is_ref("pseudo"):
                    obj.text = config.Config().get("last_pseudo", "Player")
                    break

        self.game_name = game_name

    def valid_settings(self):
        item_container = self.menu.get_object_by_ref("settings_container", self.menu.menu)

        if not item_container:
            return

        global_volume_slider = item_container.get_item("slider_volume_global")

        if global_volume_slider:
            config.Config().set("global_volume", global_volume_slider.get_value())
            self.launch_sound.set_volume(global_volume_slider.get_value() / 100)

        sound_volume_slider = item_container.get_item("slider_volume_effect")

        if sound_volume_slider:
            config.Config().set("sound_volume", sound_volume_slider.get_value())

        self.menu.return_menu()


    def load_game(self, pseudo):
        self.press_reset()
        self.menu.set_loading("On fabrique les chunks...", 10)

        config.Config().set("last_pseudo", pseudo)

        self.game_manager = client.GameClient(self.game_name, self.game_manager, self.WIDTH_SCREEN, self.HEIGHT_SCREEN, callback=self.end_loading, game=self, player_name=pseudo, texture_manager=self.texture_manager)

    def end_loading(self, message="", value=0):
        self.menu.set_loading(message, value)

        if value >= 100:
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

            if isinstance(self.game_manager, client.MultiplayerClient):
                if self.game_manager.player:
                    self.game_manager.server_connection.send_leave(self.game_manager.player.name)

            else:
                self.game_manager.World.stop()

                print("Saving world...")
                print("Path: ", self.game_manager.world_path, "Name: ", self.game_manager.world_name)

                world.save_world_json(self.game_manager.World, self.game_manager.world_path, "world")

            self.press_reset()
            self.menu.set_menu(interface.MenusCollection.MAIN)
        self.game_manager = None

    def game_is_start(self):
        return self.game_manager is not None

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

    def connect_multiplayer(self, ip, port, pseudo):
        self.press_reset()
        self.menu.set_loading("Connexion au serveur...", 10)

        self.game_manager = client.MultiplayerClient(game=self, player_name=pseudo, server_ip=ip, server_port=int(port), width_screen=self.WIDTH_SCREEN, height_screen=self.HEIGHT_SCREEN)

    def update_screen_size(self, width, height):
        self.WIDTH_SCREEN = width
        self.HEIGHT_SCREEN = height

        self.menu.update_screen_size(width, height)

        if self.game_is_start():
            self.game_manager.update_screen_size(width, height)

    def quit(self):
        self.running = False

    def run(self):
        self.launch_sound.play()
        self.launch_sound.set_volume(0.1)

        dt = 1 / self.update_rate

        accumulator = 0
        previous_time = pygame.time.get_ticks() / 1000

        while self.running:
            current_time = pygame.time.get_ticks() / 1000
            frame_time = current_time - previous_time
            previous_time = current_time

            accumulator += frame_time

            # --- Update ---
            max_updates = 10
            updates = 0

            while accumulator >= dt and updates < max_updates:
                try:
                    self.handle_events()

                    self.update(dt)
                except Exception as e:
                    self.crash_report(e)
                    break

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

            try:
                self.render()
            except Exception as e:
                self.crash_report(e)
                break

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
        if self.game_is_start() and isinstance(self.game_manager, client.MultiplayerClient):
            if not self.game_manager.is_connected():
                self.stop_game()
                self.menu.open_error(
                    title="Déconnecté du serveur",
                    message="Vous avez été déconnecté du serveur."
                )

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

            self.menu.render(self.screen)
        else:
            self.screen.fill((135, 206, 235))
            self.menu.render(self.screen)
        pygame.display.flip()

    def save_crash_report(self, crash):
        try:
            # dossier crash_reports
            crash_dir = "crash_reports"
            os.makedirs(crash_dir, exist_ok=True)

            # timestamp unique
            now = datetime.datetime.now()
            filename = now.strftime("crash_%Y-%m-%d_%H-%M-%S.txt")

            path = os.path.join(crash_dir, filename)

            # récupération traceback
            tb = "".join(
                traceback.format_exception(
                    type(crash),
                    crash,
                    crash.__traceback__
                )
            )

            # contenu report
            report = f"""
    ==========================
            CRASH REPORT
    ==========================

    Date: {now.strftime("%Y-%m-%d %H:%M:%S")}

    --- SYSTEM ---
    Platform: {platform.system()}
    Platform Version: {platform.version()}
    Python Version: {platform.python_version()}
    Pygame Version: {pygame.version.ver}

    --- GAME ---
    World Loaded: {getattr(self.game_manager, "name", "Unknown")}
    Player Position: {
        self.game_manager.player.get_pos_tile()
        if hasattr(self.game_manager, "player") and self.game_manager.player
        else "Unknown"
    }

    --- EXCEPTION ---
    Type: {type(crash).__name__}
    Message: {str(crash)}

    --- TRACEBACK ---
    {tb}
    """

            # écriture fichier
            with open(path, "w", encoding="utf-8") as f:
                f.write(report)

            print(f"[CRASH REPORT SAVED] {path}")

            return path

        except Exception as e:
            print("Impossible de sauvegarder le crash report :", e)
            return None


    def crash_report(self, exception):
        report_path = self.save_crash_report(exception)

        self.stop_game()

        def open_report():
            print("Open report")
            if report_path and os.path.exists(report_path):
                os.startfile(os.path.abspath(report_path))

            print("Report : report_path")

        self.menu.open_error(
            callback=open_report
        )

if __name__ == "__main__": 
    try: 
        game = Game()
        game.run()
        
    except Exception as e: 
        traceback.print_exc() 
        input("Crash - press enter")