import os
from classes import game_property
import pygame
from classes.texture_manager import TextureType
from classes.pygame_interface import Button, Image, Surface, TextBox, ObjectReferencable, Texte, ObjectInterface

class Worlds_manager:
    def __init__(self, base_path="worlds"):
        self.base_path = base_path
        self.reload()

    def search_worlds(self, name):
        self.reload()

        result = {key: value for key, value in self.worlds.items() if name.lower() in key.lower()}
        print("Search result:", result)
        return result

    def reload(self):
        self.worlds = {}
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        for name in os.listdir(self.base_path):
            full_path = os.path.join(self.base_path, name)

            if os.path.isdir(full_path):
                self.worlds[name] = full_path

class WorldInterface(ObjectReferencable):
    def __init__(self, rect, world_name, ref="", callback_play=None, callback_settings=None):
        super().__init__(rect, ref)

        MARGIN = 10

        btn_play_rect = self.rect.copy()
        btn_play_rect.width -= self.rect.height // 2 + MARGIN
        self.btn_play = Button(world_name, btn_play_rect, callback_play)

        btn_settings_rect = self.rect.copy()
        btn_settings_rect.width = self.rect.height // 2
        btn_settings_rect.left += btn_play_rect.width + MARGIN
        self.btn_settings = Button("|", btn_settings_rect, callback_settings)

    def render(self, screen):
        self.btn_play.render(screen)
        self.btn_settings.render(screen)

    def handle_event(self, event):
        self.btn_play.handle_event(event)
        self.btn_settings.handle_event(event)

class MenusCollection:
    GAME = "game"
    MAIN = "main"
    SINGLEPLAYER = "singleplayer"
    MULTIPLAYER = "multiplayer"
    GAME_PAUSED = "paused"
    CREATE_WORLD = "create_world"
    SETTINGS_WORLD = "settings_world"
    LOADING_WORLD = "loading_world"
    CONFIRM = "confirm"
    VERSIONS_CREDITS = "versions_credits"
    PSEUDO = "pseudo"

BUTTON_HEIGHT = 60
MARGIN_UI = 40

class MainMenu:
    texture_manager = None

    def __init__(self, game):
        self.game = game

        self.menu = MenusCollection.MAIN
        self.menus = {}
        self.current_value = None

        self.worlds_manager = Worlds_manager()

        self.update_screen_size(self.game.WIDTH_SCREEN, self.game.HEIGHT_SCREEN)

    def set_menu(self, menu: MenusCollection):
        self.game.press_reset()
        self.menu = menu

        if self.menu == MenusCollection.SINGLEPLAYER:
            self.worlds_manager.reload()
            self.reload()
        
    def is_menu(self, menu: MenusCollection):
        return menu == self.menu

    def update_screen_size(self, width, height):
        self.screen_size = (width, height)

        self.center_x = self.screen_size[0] // 2
        self.center_y = self.screen_size[1] // 2

        self.TITLE_W = self.screen_size[0] // 2
        self.TITLE_H = self.screen_size[1] // 9

        self.reload()

    def open_confirm(self, q, callback):
        self.current_value = (q, callback)

        self.menus[MenusCollection.CONFIRM] = [
            Surface((0, 0, self.screen_size[0], self.screen_size[1]), (10, 10, 10), 255),

            Texte(q, (self.center_x, self.center_y - 100, 160, 50), center_pos=True),

            Button(
                "Confirmer",
                (self.center_x - 150, self.center_y + 100, 160, 50),
                lambda: callback(True)
            ),
            Button(
                "Annuler",
                (self.center_x + 150, self.center_y + 100, 160, 50),
                lambda: callback(False)
            )
        ]

        self.set_menu(MenusCollection.CONFIRM)

    def open_settings_world(self, world_name):
        self.current_value = world_name

        def delete_world(event):
            if event:
                self.game.delete_world_func(world_name)
            else:
                self.open_settings_world(world_name)

        self.menus[MenusCollection.SETTINGS_WORLD] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 3 - BUTTON_HEIGHT * 2, self.screen_size[0], MARGIN_UI * 3 + BUTTON_HEIGHT * 2), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2 - BUTTON_HEIGHT - MARGIN_UI), (10, 10, 10), 255),

            Texte(world_name, (self.center_x, MARGIN_UI + BUTTON_HEIGHT // 2, 160, 50), center_pos=True),

            Button(
                "Supprimer ce monde",
                (MARGIN_UI, self.screen_size[1] - ( MARGIN_UI + BUTTON_HEIGHT ) * 2, self.screen_size[0] - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda wn=world_name: self.open_confirm(f"Voulez vous vraiment supprimer le monde {wn} ?", delete_world)
            ),

            Button(
                "Retour",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.SINGLEPLAYER)
            ),
            Button(
                "Jouer sur ce monde",
                (self.screen_size[0] // 2 + MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.game.select_world(world_name)
            )
        ]

        self.set_menu(MenusCollection.SETTINGS_WORLD)

    def set_loading(self, message, value):
        self.menus[MenusCollection.LOADING_WORLD] = [
            Surface((0, 0, self.screen_size[0], self.screen_size[1]), (10, 10, 10), 255),

            Texte("Chargement du monde...", (self.center_x, self.center_y, 160, 50), center_pos=True),
            Texte(message + f" - {value}%", (self.center_x, self.center_y + 80, 160, 50), center_pos=True)
        ]

        self.set_menu(MenusCollection.LOADING_WORLD)

    def reload(self):
        if self.texture_manager is None:
            return

        

        self.menus[MenusCollection.MAIN] = [
            Image((0, 0, self.screen_size[0], self.screen_size[1]), self.texture_manager.get_texture(TextureType.MAIN_MENU)),

            Image((self.center_x - self.TITLE_W // 2, BUTTON_HEIGHT + MARGIN_UI, self.TITLE_W, self.TITLE_H), self.texture_manager.get_texture(TextureType.TITLE)),

            Surface((self.center_x - (320 + MARGIN_UI * 2) // 2, self.center_y - (BUTTON_HEIGHT * 3 + MARGIN_UI * 4) // 2, 320 + MARGIN_UI * 2, (BUTTON_HEIGHT + MARGIN_UI) * 5 + MARGIN_UI), (0, 0, 0), 160),

            Button(
                "Solo",
                (self.center_x - 160, self.center_y - 100 - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.SINGLEPLAYER)
            ),
            Button(
                "Multijoueur",
                (self.center_x - 160, self.center_y - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.MULTIPLAYER)
            ),
            Button(
                "Tutoriel",
                (self.center_x - 160, self.center_y + 100 - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: self.game.select_tuto()
            ),
            Button(
                "Versions et crédits",
                (self.center_x - 160, self.center_y + 200 - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.VERSIONS_CREDITS)
            ),
            Button(
                "Quitter",
                (self.center_x - 160, self.center_y + 300 - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: setattr(self.game, "running", False)
            ),
        ]

        def return_to_game(self):
            self.game.press_reset()
            self.set_menu(MenusCollection.GAME)

        self.menus[MenusCollection.GAME_PAUSED] = [
            Image((self.center_x - self.TITLE_W // 2, BUTTON_HEIGHT + MARGIN_UI, self.TITLE_W, self.TITLE_H), self.texture_manager.get_texture(TextureType.TITLE)),
            
            Button(
                "Reprendre",
                (self.center_x - 200, self.center_y - 100 - BUTTON_HEIGHT // 2, 400, BUTTON_HEIGHT),
                lambda: return_to_game(self)
            ),
            Button(
                "Paramètres",
                (self.center_x - 200, self.center_y - BUTTON_HEIGHT // 2, 400, BUTTON_HEIGHT),
                lambda: print("Settings")
            ),
            Button(
                "Sauvegarder et quitter",
                (self.center_x - 200, self.center_y + 100 - BUTTON_HEIGHT // 2, 400, BUTTON_HEIGHT),
                lambda: self.game.stop_game()
            )
        ]

        self.menus[MenusCollection.MULTIPLAYER] = [
            Surface((0, 0, self.screen_size[0], self.screen_size[1]), (10, 10, 10), 255),

            Texte("Multijoueur", (self.center_x, 50, 160, 50), center_pos=True),
            Button(
                "Retour",
                (self.center_x - 100, self.center_y - BUTTON_HEIGHT // 2, 200, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.MAIN)
            )
        ]

        self.menus[MenusCollection.LOADING_WORLD] = []

        self.menus[MenusCollection.GAME] = []

        self.menus[MenusCollection.VERSIONS_CREDITS] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 2 - BUTTON_HEIGHT, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),

            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2), (10, 10, 10), 255),

            Texte("Créer par Arthur REY en Python", (self.center_x, MARGIN_UI * 2 + BUTTON_HEIGHT * 2, 160, 50), center_pos=True),

            Texte("Versions et crédit", (self.center_x, BUTTON_HEIGHT, 160, 50), center_pos=True),

            Button(
                "Retour",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.MAIN)
            )
        ]

        def enter_game():
            self.game.press_reset()
            self.set_menu(MenusCollection.LOADING_WORLD)

            pseudo = None
            for obj in self.menus[MenusCollection.PSEUDO]:
                if isinstance(obj, TextBox) and obj.is_ref("pseudo"):
                    pseudo = obj.text
                    break
            
            if pseudo and pseudo.strip() != "":
                self.game.load_game(pseudo)

        self.menus[MenusCollection.PSEUDO] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 2 - BUTTON_HEIGHT, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2), (10, 10, 10), 255),

            Texte("Entrez votre nom", (self.center_x, MARGIN_UI + BUTTON_HEIGHT // 2, 160, 50), center_pos=True),

            Button(
                "Retour",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.SINGLEPLAYER)
            ),
            TextBox(
                (self.center_x - 160, self.center_y - BUTTON_HEIGHT // 2 - 100, 320, BUTTON_HEIGHT),
                "Pseudo",
                "pseudo"
            ),

            Button(
                "Entrer dans le monde",
                (self.screen_size[0] // 2 + MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: enter_game()
            )
        ]

        if self.is_menu(MenusCollection.CONFIRM):
            self.open_confirm(self.current_value[0], self.current_value[1])
        else:
            self.menus[MenusCollection.CONFIRM] = []

        if self.is_menu(MenusCollection.SETTINGS_WORLD):
            self.open_settings_world(self.current_value)
        else:
            self.menus[MenusCollection.SETTINGS_WORLD] = []

        self.menus[MenusCollection.CREATE_WORLD] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 2 - BUTTON_HEIGHT, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2), (10, 10, 10), 255),

            Texte("Création d'un monde", (self.center_x, MARGIN_UI + BUTTON_HEIGHT // 2, 160, 50), center_pos=True),

            Button(
                "Retour",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.SINGLEPLAYER)
            ),
            TextBox(
                (self.center_x - 160, self.center_y - BUTTON_HEIGHT // 2 - 100, 320, BUTTON_HEIGHT),
                "Nom",
                "world_name"
            ),
            TextBox(
                (self.center_x - 160, self.center_y + BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                "Seed (optionnel)",
                "world_seed"
            ),
            Button(
                "Créer un nouveau monde",
                (self.screen_size[0] // 2 + MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.game.create_world()
            )
        ]

        search = ""
        if self.menus.get(MenusCollection.SINGLEPLAYER):
            for obj in self.menus[MenusCollection.SINGLEPLAYER]:
                if isinstance(obj, TextBox):
                    if obj.is_ref("world_name"):
                        search = obj.text
                        print("Search:", search)
                        break

        self.menus[MenusCollection.SINGLEPLAYER] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 2 - BUTTON_HEIGHT, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT * 2), (30, 30, 30), 255),
            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT * 2, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2 - BUTTON_HEIGHT), (10, 10, 10), 255),

            Texte("Sélection du monde", (self.center_x, 50, 160, 50), center_pos=True),

            TextBox(
                (self.center_x - 160, 100, 320, BUTTON_HEIGHT),
                "Nom",
                "world_name",
                text=search,
                enter_callback=lambda: self.reload(),
            ),

            Button(
                "Retour",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.MAIN)
            ),
            Button(
                "Créer un nouveau monde",
                (self.screen_size[0] // 2 + MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.CREATE_WORLD)
            )
        ]

        index = 0

        worlds_searched = self.worlds_manager.search_worlds(search)

        for key, value in worlds_searched.items():
            self.menus[MenusCollection.SINGLEPLAYER].append(
                WorldInterface(
                    (self.center_x - 160, 300 + index * 100, 320, 60),
                    key,
                    f"world_{key}",
                    lambda wn=key: self.game.select_world(wn),
                    lambda wn=key: self.open_settings_world(wn)
                )
            )
            index += 1
        
        if len(worlds_searched) == 0 and len(self.worlds_manager.worlds) > 0:
            self.menus[MenusCollection.SINGLEPLAYER].append(
                Texte("Aucun monde trouvé", (self.center_x, 300, 160, 50), center_pos=True)
            )
        elif len(worlds_searched) == 0:
            self.menus[MenusCollection.SINGLEPLAYER].append(
                Texte("Aucun monde", (self.center_x, 300, 160, 50), center_pos=True)
            )

    def render(self, screen):
        for obj in self.menus[self.menu]:
            obj.render(screen)

    def handle_events(self, event):
        for obj in self.menus[self.menu]:
            obj.handle_event(event)

    def update(self, dt):
        if self.is_menu(MenusCollection.GAME_PAUSED):
            if self.game.is_press(pygame.K_ESCAPE):
                self.set_menu(MenusCollection.GAME)

        for obj in self.menus[self.menu]:
            obj.update(dt)