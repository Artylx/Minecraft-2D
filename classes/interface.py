import os
from classes import game_property
import pygame
from classes.texture_manager import TextureType

class Worlds_manager:
    def __init__(self):
        self.reload()

    def reload(self, base_path="worlds"):
        self.worlds = {}
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        for name in os.listdir(base_path):
            full_path = os.path.join(base_path, name)

            if os.path.isdir(full_path):
                self.worlds[name] = full_path

class ObjectInterface:
    def __init__(self, rect, callback=None):
        self.rect = pygame.Rect(rect)
        self.callback = callback

    def render(self, screen, color=(200, 200, 200)):
        pygame.draw.rect(screen, color, self.rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                if self.callback:
                    self.callback()

    def is_hover(self):
        mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)

    def update(self, dt):
        pass

class Texte(ObjectInterface):
    def __init__(self, text, pos, color=(255, 255, 255), center_pos=False):
        self.font = pygame.font.SysFont(None, 40)
        self.text = text

        if center_pos:
            text_surface = self.font.render(self.text, True, color)
            text_rect = text_surface.get_rect()
            pos = (pos[0] - text_rect.width // 2, pos[1] - text_rect.height // 2)

        self.pos = pos

        self.text_surface = self.font.render(self.text, True, color)
        text_rect = self.text_surface.get_rect()
        text_rect.width += pos[0]
        text_rect.height += pos[1]

        rect = pygame.Rect(self.pos[0], self.pos[1], text_rect.width, text_rect.height)

        super().__init__(rect)
        
    def render(self, screen):
        screen.blit(self.text_surface, self.pos)

class Button(ObjectInterface):
    def __init__(self, text, rect, callback, 
                 text_color=(255, 255, 255), 
                 border_color=(255, 255, 255), 
                 background_color=(0, 0, 0), 
                 background_color_hover=(50, 50, 50),
                 border_color_hover=(255, 255, 255)
                 ):
        
        super().__init__(rect, callback)
        self.text = text
        self.font = pygame.font.SysFont(None, 40)

        self.text_color = text_color
        self.border_color = border_color
        self.background_color = background_color
        self.background_color_hover = background_color_hover
        self.border_color_hover = border_color_hover

        self.text_surface = self.font.render(self.text, True, text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def render(self, screen):
        bg_color = self.background_color_hover if self.is_hover() else self.background_color
        bd_color = self.border_color_hover if self.is_hover() else self.border_color
        
        old_clip = screen.get_clip()
        screen.set_clip(self.rect)
        
        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.rect(screen, bd_color, self.rect, 2)

        screen.blit(self.text_surface, self.text_rect)

        screen.set_clip(old_clip)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.callback()

class ObjectReferencable(ObjectInterface):
    def __init__(self, rect, ref="", callback=None):
        super().__init__(rect, callback)
        self.ref = ref

    def is_ref(self, ref):
        return self.ref == ref

class TextBox(ObjectReferencable):
    def __init__(self, rect, placeholder="", ref="", text="",
                 text_color=(255, 255, 255),
                 placeholder_color=(150, 150, 150),
                 border_color=(255, 255, 255), 
                 background_color=(0, 0, 0), 
                 background_color_hover=(50, 50, 50),
                 border_color_hover=(255, 255, 255)
                 ):
        super().__init__(rect, ref)
        self.placeholder = placeholder
        self.font = pygame.font.SysFont(None, 40)

        self.selected = False
        self.text = text

        self.text_color = text_color
        self.placeholder_color = placeholder_color

        self.border_color = border_color
        self.background_color = background_color
        self.background_color_hover = background_color_hover
        self.border_color_hover = border_color_hover

        self.placeholder_surface = self.font.render(self.placeholder, True, self.placeholder_color)
        self.placeholder_rect = self.placeholder_surface.get_rect(midleft=(self.rect.midleft[0] + 10, self.rect.midleft[1]))

        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_interval = 0.5

        self.max_char = 30
        self.scroll_x = 0

    def render(self, screen):
        bg_color = self.background_color_hover if self.selected else self.background_color
        bd_color = self.border_color_hover if self.selected else self.border_color

        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.rect(screen, bd_color, self.rect, 2)

        old_clip = screen.get_clip()
        screen.set_clip(self.rect)

        if self.text == "" and not self.selected:
            screen.blit(self.placeholder_surface, self.placeholder_rect)
        else:
            text_surface = self.font.render(self.text, True, self.text_color)
            text_width = text_surface.get_width()

            max_width = self.rect.width - 20  # padding

            if text_width > max_width:
                self.scroll_x = text_width - max_width
            else:
                self.scroll_x = 0
            
            text_rect = text_surface.get_rect(
                midleft=(self.rect.midleft[0] + 10 - self.scroll_x, self.rect.midleft[1])
            )

            screen.blit(text_surface, text_rect)

        screen.set_clip(old_clip)

        if self.selected and self.cursor_visible:
            cursor_x = text_rect.right + 2
            pygame.draw.line(
                screen,
                self.text_color,
                (cursor_x, text_rect.top),
                (cursor_x, text_rect.bottom),
                2
            )
    
    def handle_event(self, event):
        if self.selected:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.unicode and event.unicode.isprintable():

                    if len(self.text) < self.max_char:
                        self.text += event.unicode
                
                print(f"Event key down text unicode: {event.unicode}")
                pass

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.selected = True
            else:
                self.selected = False
    
    def update(self, dt):
        if self.selected:
            self.cursor_timer += dt

            if self.cursor_timer >= self.cursor_interval:
                self.cursor_timer = 0
                self.cursor_visible = not self.cursor_visible
        else:
            self.cursor_visible = False

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

class Image(ObjectInterface):
    def __init__(self, rect, surface, callback=None):
        super().__init__(rect, callback)

        self.surface = pygame.transform.scale(surface, (self.rect.width, self.rect.height))
    
    def render(self, screen):
        screen.blit(self.surface, self.rect)

class Surface(ObjectInterface):
    def __init__(self, rect, color=(200, 200, 200), alpha=255, callback=None):
        super().__init__(rect, callback)

        self.color = color
        self.alpha = alpha

        self.surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        self.surface.fill((self.color[0], self.color[1], self.color[2], self.alpha))
    
    def render(self, screen):
        screen.blit(self.surface, self.rect)

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
                self.game.delete_world(world_name)
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
                lambda: self.game.load_game(world_name, world_name)
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
        
        self.worlds_manager.reload()

        TITLE_W = self.screen_size[0] // 2
        TITLE_H = self.screen_size[1] // 9

        self.menus[MenusCollection.MAIN] = [
            Image((0, 0, self.screen_size[0], self.screen_size[1]), self.texture_manager.get_texture(TextureType.MAIN_MENU)),

            Image((self.center_x - TITLE_W // 2, BUTTON_HEIGHT + MARGIN_UI, TITLE_W, TITLE_H), self.texture_manager.get_texture(TextureType.TITLE)),

            Surface((self.center_x - (320 + MARGIN_UI * 2) // 2, self.center_y - (BUTTON_HEIGHT * 3 + MARGIN_UI * 4) // 2, 320 + MARGIN_UI * 2, BUTTON_HEIGHT * 4 + MARGIN_UI * 5), (0, 0, 0), 160),

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
                "Versions et crédits",
                (self.center_x - 160, self.center_y + 100 - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.VERSIONS_CREDITS)
            ),
            Button(
                "Quitter",
                (self.center_x - 160, self.center_y + 200 - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: setattr(self.game, "running", False)
            ),

            Texte(f"Version {game_property.VERSION}", (MARGIN_UI, MARGIN_UI - 20, 160, 20))
        ]

        def return_to_game(self):
            self.game.press_reset()
            self.set_menu(MenusCollection.GAME)

        self.menus[MenusCollection.GAME_PAUSED] = [
            Texte("TeraCraft", (self.center_x, 50, 160, 50), center_pos=True),
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

        self.menus[MenusCollection.VERSIONS_CREDITS] = []

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

        self.menus[MenusCollection.SINGLEPLAYER] = [
            Surface((0, self.screen_size[1] - MARGIN_UI * 2 - BUTTON_HEIGHT, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT), (30, 30, 30), 255),
            Surface((0, 0, self.screen_size[0], MARGIN_UI * 2 + BUTTON_HEIGHT * 2), (30, 30, 30), 255),
            Surface((0, MARGIN_UI * 2 + BUTTON_HEIGHT * 2, self.screen_size[0], self.screen_size[1] - (MARGIN_UI * 2 + BUTTON_HEIGHT) * 2 - BUTTON_HEIGHT), (10, 10, 10), 255),

            Texte("Sélection du monde", (self.center_x, 50, 160, 50), center_pos=True),

            TextBox(
                (self.center_x - 160, 100, 320, BUTTON_HEIGHT),
                "Nom",
                "world_name"
            ),

            Button(
                "Rechercher",
                (self.center_x + 200, 100, 200, BUTTON_HEIGHT),
                lambda: print("Rechercher un monde")
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
        for key, value in self.worlds_manager.worlds.items():
            self.menus[MenusCollection.SINGLEPLAYER].append(
                WorldInterface(
                    (self.center_x - 160, 300 + index * 100, 320, 60),
                    key,
                    f"world_{key}",
                    lambda v=value, path=key: self.game.load_game(v, path),
                    lambda wn=key: self.open_settings_world(wn)
                )
            )
            index += 1

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