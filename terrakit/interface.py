import os
from terrakit import game_property
import pygame
from terrakit import context, config
from terrakit.pygame_interface import Button, Image, Surface, TextBox, ObjectReferencable, Texte, ObjectInterface, ItemsScrollContainer, LoadingBar, Slider, TexteReferencable
from terrakit.texture_manager import TextureType

class CreditsItem(ObjectInterface):
    def __init__(self, rect, version, description):
        super().__init__(rect)

        self.bg = Surface(rect, color=(40, 40, 40), alpha=255)

        # Texte version (titre)
        self.title = Texte(
            version,
            (rect.x + 10, rect.y + 10),
            color=(255, 255, 255),
            center_pos=False
        )

        # Texte description
        self.desc = Texte(
            description,
            (rect.x + 10, rect.y + 35),
            color=(180, 180, 180),
            center_pos=False,
            font_size=30
        )

    def render(self, screen):
        self.bg.rect = self.rect
        self.bg.render(screen)

        # IMPORTANT: reposition dynamique (scroll safe)
        self.title.rect.topleft = (self.rect.x + 10, self.rect.y + 10)
        self.desc.rect.topleft = (self.rect.x + 10, self.rect.y + 35)

        self.title.render(screen)
        self.desc.render(screen)

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

        self.world_name = world_name

        self.callback_play = callback_play
        self.callback_settings = callback_settings

        self.MARGIN = 10

        self.btn_play = Button(
            world_name,
            rect,
            callback_play
        )

        self.btn_settings = Button(
            "|",
            rect,
            callback_settings
        )

    def update_layout(self):
        btn_play_rect = self.rect.copy()
        btn_play_rect.width -= self.rect.height // 2 + self.MARGIN

        btn_settings_rect = self.rect.copy()
        btn_settings_rect.width = self.rect.height // 2
        btn_settings_rect.left = btn_play_rect.right + self.MARGIN

        self.btn_play.rect = btn_play_rect
        self.btn_settings.rect = btn_settings_rect

        # IMPORTANT
        self.btn_play.text_rect = self.btn_play.text_surface.get_rect(
            center=self.btn_play.rect.center
        )

        self.btn_settings.text_rect = self.btn_settings.text_surface.get_rect(
            center=self.btn_settings.rect.center
        )

    def update(self, dt):
        self.btn_play.update(dt)
        self.btn_settings.update(dt)

    def render(self, screen):
        self.btn_play.render(screen)
        self.btn_settings.render(screen)

        self.update_layout()

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
    ERROR = "error"
    CONNECT_MULTIPLAYER = "connect_multiplayer"
    LAUNCH = "launch"
    DIED = "died"
    SETTINGS = "settings"

BUTTON_HEIGHT = 60
MARGIN_UI = 40

class MainMenu:
    def __init__(self, game):
        self.game = game

        self.menu = MenusCollection.MAIN
        self.old_menu = self.menu
        self.menus = {}
        self.current_value = None

        self.worlds_manager = Worlds_manager()

        self.update_screen_size(self.game.WIDTH_SCREEN, self.game.HEIGHT_SCREEN)

    def set_menu(self, menu: MenusCollection):
        self.game.press_reset()
        self.old_menu = self.menu
        self.menu = menu

        if self.menu == MenusCollection.SINGLEPLAYER:
            self.worlds_manager.reload()
            self.reload()
        elif self.menu == MenusCollection.SETTINGS:
            self.reload()
        
    def is_menu(self, menu: MenusCollection):
        return menu == self.menu
    
    def get_object_by_ref(self, ref, menu: MenusCollection = None):
        if menu is None:
            menu = self.menu

        for obj in self.menus[menu]:
            if isinstance(obj, ObjectReferencable) and obj.is_ref(ref):
                return obj
        return None

    def update_screen_size(self, width, height):
        self.screen_size = (width, height)

        self.center_x = self.screen_size[0] // 2
        self.center_y = self.screen_size[1] // 2

        self.TITLE_W = self.screen_size[0] // 2
        self.TITLE_H = self.screen_size[1] // 9

        self.reload()

    def return_menu(self):
        self.set_menu(self.old_menu)

    def open_confirm(self, q, callback):
        self.current_value = (q, callback)

        self.menus[MenusCollection.CONFIRM] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 2 - BUTTON_HEIGHT, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT * 2), (30, 30, 30), 255),
            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT * 2, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2 - BUTTON_HEIGHT), (10, 10, 10), 255),

            Texte(q, (self.center_x, MARGIN_UI + BUTTON_HEIGHT // 2, 160, 50), center_pos=True),

            Button(
                "Confirmer",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: callback(True)
            ),
            Button(
                "Annuler",
                (self.screen_size[0] // 2 + MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: callback(False)
            )
        ]

        self.set_menu(MenusCollection.CONFIRM)

    def open_error(self, callback):
        self.menus[MenusCollection.ERROR] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 2 - BUTTON_HEIGHT, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),

            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2), (10, 10, 10), 255),

            Texte("Pas de panique votre monde a été sauvegardé.", (self.center_x, MARGIN_UI * 2 + BUTTON_HEIGHT * 2, 160, 50), center_pos=True),

            Texte("Oups... Une erreur s'est produite.", (self.center_x, BUTTON_HEIGHT, 160, 50), center_pos=True),
            
            Button(
                "Ouvrir le rapport du crash",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: callback()
            ),

            Button(
                "Continuer",
                (self.screen_size[0] // 2 + MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.MAIN)
            )
        ]

        self.set_menu(MenusCollection.ERROR)

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
        self.loading_bar = LoadingBar(
            (
                self.center_x - 250,
                self.center_y + 150,
                500,
                40
            ),
            "loading_bar",
            value=value,
            corner_radius=20
        )
            
        self.menus[MenusCollection.LOADING_WORLD] = [

            Surface(
                (0,0,self.screen_size[0],self.screen_size[1]),
                (10,10,10),
                255
            ),

            Texte(
                "Chargement du monde...",
                (self.center_x,self.center_y-80),
                center_pos=True
            ),

            Texte(
                message,
                (self.center_x,self.center_y+80),
                center_pos=True
            ),

            self.loading_bar
        ]


        self.set_menu(MenusCollection.LOADING_WORLD)

    def reload(self):
        if context.get_resource_pack().texture_manager() is None:
            return

        self.menus[MenusCollection.LAUNCH] = [
            Surface((0, 0, self.screen_size[0], self.screen_size[1]), (10, 10, 10), 255),

            Image((self.center_x - self.TITLE_W // 2, BUTTON_HEIGHT + MARGIN_UI, self.TITLE_W, self.TITLE_H), context.get_resource_pack().texture_manager().get_texture(TextureType.TITLE)),
        ]

        self.menus[MenusCollection.MAIN] = [
            Image((0, 0, self.screen_size[0], self.screen_size[1]), context.get_resource_pack().texture_manager().get_texture(TextureType.MAIN_MENU)),

            Image((self.center_x - self.TITLE_W // 2, BUTTON_HEIGHT + MARGIN_UI, self.TITLE_W, self.TITLE_H), context.get_resource_pack().texture_manager().get_texture(TextureType.TITLE)),

            Surface((self.center_x - (320 + MARGIN_UI * 2) // 2, self.center_y - (BUTTON_HEIGHT * 3 + MARGIN_UI * 4) // 2, 320 + MARGIN_UI * 2, (BUTTON_HEIGHT + MARGIN_UI) * 5 + MARGIN_UI), (0, 0, 0), 160, corner_radius=26),

            Button(
                "Solo",
                (self.center_x - 160, self.center_y - 100 - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.SINGLEPLAYER),
            ),
            Button(
                "Multijoueur",
                (self.center_x - 160, self.center_y - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.MULTIPLAYER)
            ),
            Button(
                "Paramètres",
                (self.center_x - 160, self.center_y + 100 - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.SETTINGS)
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

        self.menus[MenusCollection.DIED] = [
            Image((self.center_x - self.TITLE_W // 2, BUTTON_HEIGHT + MARGIN_UI, self.TITLE_W, self.TITLE_H), context.get_resource_pack().texture_manager().get_texture(TextureType.TITLE)),
            
            Button(
                "Réapparaitre",
                (self.center_x - 200, self.center_y - 100 - BUTTON_HEIGHT // 2, 400, BUTTON_HEIGHT),
                lambda: self.game.repsawn()
            ),
            Button(
                "Quitter",
                (self.center_x - 200, self.center_y - BUTTON_HEIGHT // 2, 400, BUTTON_HEIGHT),
                lambda: self.game.stop_game()
            ),
        ]

        self.menus[MenusCollection.GAME_PAUSED] = [
            Image((self.center_x - self.TITLE_W // 2, BUTTON_HEIGHT + MARGIN_UI, self.TITLE_W, self.TITLE_H), context.get_resource_pack().texture_manager().get_texture(TextureType.TITLE)),
            
            Surface((0, 0, self.screen_size[0], self.screen_size[1]), (0, 0, 0), alpha=100),

            Button(
                "Reprendre",
                (self.center_x - 200, self.center_y - 100 - BUTTON_HEIGHT // 2, 400, BUTTON_HEIGHT),
                lambda: return_to_game(self)
            ),
            Button(
                "Paramètres",
                (self.center_x - 200, self.center_y - BUTTON_HEIGHT // 2, 400, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.SETTINGS)
            ),
            Button(
                "Sauvegarder et quitter",
                (self.center_x - 200, self.center_y + 100 - BUTTON_HEIGHT // 2, 400, BUTTON_HEIGHT),
                lambda: self.game.stop_game()
            )
        ]

        settings_container = ItemsScrollContainer(
            (self.center_x - min(1200, self.screen_size[0] // 2) // 2, MARGIN_UI * 2 + BUTTON_HEIGHT, min(1200, self.screen_size[0] // 2), self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2),
            color=(10, 10, 10),
            spacing_border=40,
            item_height=30,
            spacing=20,
            ref="settings_container",
        )

        text_global = TexteReferencable(
            f"Volume général ({config.Config().get("global_volume")}%)",
            (0, 0),
            "text_global"
        )


        def modif_global_volume(slider):

            text = settings_container.get_item("text_global")

            if text:
                text.set_text(
                    f"Volume général ({slider.get_value()}%)"
                )


        def modif_effect_volume(slider):

            text = settings_container.get_item("text_effect")

            if text:
                text.set_text(
                    f"Volume effet sonores ({slider.get_value()})%"
                )


        text_effect = TexteReferencable(
            f"Volume effet sonores ({config.Config().get("sound_volume")}%)",
            (0, 0),
            "text_effect"
        )


        slider_global = Slider(
            (30, 30, 200, 30),
            ref="slider_volume_global",
            value=config.Config().get("global_volume"),
            callback=lambda slider: modif_global_volume(slider),
            background_color=(0, 0, 0)
        )


        slider_effect = Slider(
            (30, 30, 200, 30),
            ref="slider_volume_effect",
            value=config.Config().get("sound_volume"),
            callback=lambda slider: modif_effect_volume(slider),
            background_color=(0, 0, 0)
        )


        settings_container.set_items([
            text_global,
            slider_global,

            text_effect,
            slider_effect,
        ])

        self.menus[MenusCollection.SETTINGS] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 2 - BUTTON_HEIGHT, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2), (10, 10, 10), 255),

            Texte("Paramètres", (self.center_x, BUTTON_HEIGHT + 10, 160, 50), center_pos=True),

            #
            # SETTINGS CONTAINER

            settings_container,

            #
            #   

            Button(
                "Retour",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.return_menu()
            ),
            Button(
                "Valider",
                (self.screen_size[0] // 2 + MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.game.valid_settings(),
                background_color=(32, 69, 30),
                background_color_hover=(85, 156, 81),
            )
        ]

        self.menus[MenusCollection.MULTIPLAYER] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 3 - BUTTON_HEIGHT * 2, self.screen_size[0], MARGIN_UI * 3 + BUTTON_HEIGHT * 2), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2 - BUTTON_HEIGHT - MARGIN_UI), (10, 10, 10), 255),

            Texte("Multijoueur", (self.center_x, 80, 160, 50), center_pos=True),

            Button(
                "Host un monde",
                (MARGIN_UI, self.screen_size[1] - ( MARGIN_UI + BUTTON_HEIGHT ) * 2, self.screen_size[0] - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: None,
                enable=False
            ),
            
            Button(
                "Retour",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.MAIN)
            ),

            Button(
                "Se connecter",
                (self.screen_size[0] // 2 + MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.CONNECT_MULTIPLAYER)
            )
        ]

        self.menus[MenusCollection.CONNECT_MULTIPLAYER] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 3 - BUTTON_HEIGHT * 2, self.screen_size[0], MARGIN_UI * 3 + BUTTON_HEIGHT * 2), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2 - BUTTON_HEIGHT - MARGIN_UI), (10, 10, 10), 255),

            Texte("Multijoueur", (self.center_x, 80, 160, 50), center_pos=True),

            TextBox(
                (self.center_x - 160, self.center_y - BUTTON_HEIGHT // 2 - 100, 320, BUTTON_HEIGHT),
                "Adresse IP",
                "ip",
                text="localhost"
            ),
            TextBox(
                (self.center_x - 160, self.center_y + BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                "Port",
                "port",
                text="12345"
            ),
            TextBox(
                (self.center_x - 160, self.center_y + BUTTON_HEIGHT // 2 + 100, 320, BUTTON_HEIGHT),
                "Pseudo",
                "pseudo",
                text="Arthur"
            ),
            
            Button(
                "Retour",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.MULTIPLAYER)
            ),

            Button(
                "Se connecter",
                (self.screen_size[0] // 2 + MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.game.connect_multiplayer(self.get_object_by_ref("ip", MenusCollection.CONNECT_MULTIPLAYER).text, self.get_object_by_ref("port", MenusCollection.CONNECT_MULTIPLAYER).text, self.get_object_by_ref("pseudo", MenusCollection.CONNECT_MULTIPLAYER).text)
            )
        ]

        self.menus[MenusCollection.LOADING_WORLD] = []

        self.menus[MenusCollection.GAME] = []

        credits_container = ItemsScrollContainer(
            (self.center_x - min(1200, self.screen_size[0] // 2) // 2, MARGIN_UI * 3 + BUTTON_HEIGHT * 2, min(1200, self.screen_size[0] // 2), self.screen_size[1] - MARGIN_UI * 2 - BUTTON_HEIGHT - MARGIN_UI * 3 - BUTTON_HEIGHT * 2),
            color=(10, 10, 10),
            spacing_border=0,
        )

        credits_container.set_items([
            CreditsItem(pygame.Rect(0, 0, 0, 0), "V1.15 - 18/07/2026", "- Ajout des paramètres de volume.\n"),
            CreditsItem(pygame.Rect(0, 0, 0, 0), "V1.14 - 16/06/2026", "- Ajout d'une bar de scroll dans les ItemsScrollContainer.\n- Introdution au multi joueur malgré la création de nombreux bugs.\n- Correctif du bug de l'arc qui crashait.\n- Généralisation des textures et création du package terrakit.\n- Amélioration et rectification de bug sur l'ui.\n- Passage de texture pack à resource pack et ajout d'annimations.\n"),
            CreditsItem(pygame.Rect(0, 0, 0, 0), "V1.13 - 17/05/2026", "- Ajout d'un système de composant pour les blocks (ChestComponent, ...)\n- Ajout du système de four de coffre et de sauvegarde du monde avec un \nruntime plus rapide et moins gourmant pour le processeur.\n- Ajout du système de crash reporter avec une interface et un dossier\navec la liste des crash du jeu.\n- Ajout de l'interface des versions"),
            CreditsItem(pygame.Rect(0, 0, 0, 0), "V1.12 - 13/05/2026", "- Résolution du bug avec le scroll non détecté\n- Résolution du bug des attrubuts entres les singletons qui était\nlié avec le principal bug l'arc.\n- Ajout d'une barre de vie pour les items."),
            CreditsItem(pygame.Rect(0, 0, 0, 0), "V1.10 - 27/04/2026", ""),
            CreditsItem(pygame.Rect(0, 0, 0, 0), "V1.08 - 05/03/2026", ""),
            CreditsItem(pygame.Rect(0, 0, 0, 0), "V1.07 - 11/02/2026", ""),
            CreditsItem(pygame.Rect(0, 0, 0, 0), "V1.06 - 26/07/2026", ""),
            CreditsItem(pygame.Rect(0, 0, 0, 0), "V1.04 - 02/07/2025", ""),
        ])


        self.menus[MenusCollection.VERSIONS_CREDITS] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 2 - BUTTON_HEIGHT, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),

            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2), (10, 10, 10), 255),

            Texte("Créer par Arthur REY en Python", (self.center_x, MARGIN_UI * 2 + BUTTON_HEIGHT * 2 - 10, 160, 50), center_pos=True),

            Texte(f"Versions et crédit (actuel: V{game_property.VERSION})", (self.center_x, BUTTON_HEIGHT, 160, 50), center_pos=True),

            credits_container,

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
                "pseudo",
                enter_callback=lambda: enter_game()
            ),

            Button(
                "Entrer dans le monde",
                (self.screen_size[0] // 2 + MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: enter_game()
            )
        ]

        self.menus[MenusCollection.ERROR] = [
            
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

            ItemsScrollContainer(
                (max(0, self.center_x - 300), MARGIN_UI * 2 + BUTTON_HEIGHT * 2, min(600, self.screen_size[0]), self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2 - BUTTON_HEIGHT),
                ref="worlds_container",
                color=(10, 10, 10),
                spacing=MARGIN_UI,
                item_height=BUTTON_HEIGHT,
                center_elmt=True,
                spacing_border=MARGIN_UI,
            ),

            Button(
                "Retour",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, (self.screen_size[0] - MARGIN_UI * 4) // 3, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.MAIN)
            ),
            Button(
                "Tutoriel",
                ((self.screen_size[0] - MARGIN_UI * 4) // 3 + MARGIN_UI * 2, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, (self.screen_size[0] - MARGIN_UI * 4) // 3, BUTTON_HEIGHT),
                lambda: None,
                enable=False
            ),
            Button(
                "Créer un nouveau monde",
                (((self.screen_size[0] - MARGIN_UI * 4) // 3) * 2 + MARGIN_UI * 3, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, (self.screen_size[0] - MARGIN_UI * 4) // 3, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.CREATE_WORLD)
            )
        ]

        index = 0

        worlds_searched = self.worlds_manager.search_worlds(search)

        obj = self.get_object_by_ref("worlds_container", MenusCollection.SINGLEPLAYER)

        for key, value in worlds_searched.items():
            obj.add_item(
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