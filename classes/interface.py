import os
import random
import pygame

class Worlds_manager:
    def __init__(self):
        self.worlds = {}

    def reload(self, base_path="worlds"):
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        for name in os.listdir(base_path):
            full_path = os.path.join(base_path, name)

            if os.path.isdir(full_path):
                self.worlds[name] = full_path

        print("Worlds found: ", self.worlds)

class ObjectInterface:
    def __init__(self, rect, callback=None):
        self.rect = pygame.Rect(rect)
        self.callback = callback

    def render(self, screen, color=(200, 200, 200)):
        pygame.draw.rect(screen, color, self.rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.callback()

    def is_hover(self):
        mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)

    def update(self, dt):
        pass

class Texte(ObjectInterface):
    def __init__(self, text, pos, center_pos=False):
        self.font = pygame.font.SysFont(None, 40)
        self.text = text

        if center_pos:
            text_surface = self.font.render(self.text, True, (0, 0, 0))
            text_rect = text_surface.get_rect()
            pos = (pos[0] - text_rect.width // 2, pos[1] - text_rect.height // 2)

        self.pos = pos

        self.text_surface = self.font.render(self.text, True, (0, 0, 0))
        text_rect = self.text_surface.get_rect()
        text_rect.width += pos[0]
        text_rect.height += pos[1]

        rect = pygame.Rect(self.pos[0], self.pos[1], text_rect.width, text_rect.height)

        super().__init__(rect)
        
    def render(self, screen):
        screen.blit(self.text_surface, self.pos)

class Button(ObjectInterface):
    def __init__(self, text, rect, callback):
        super().__init__(rect, callback)
        self.text = text
        self.font = pygame.font.SysFont(None, 40)

        self.text_surface = self.font.render(self.text, True, (0, 0, 0))
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def render(self, screen):
        color = (200, 200, 200) if self.is_hover() else (150, 150, 150)
        
        old_clip = screen.get_clip()
        screen.set_clip(self.rect)
        
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)

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
    def __init__(self, rect, placeholder="", ref="", text=""):
        super().__init__(rect, ref)
        self.placeholder = placeholder
        self.font = pygame.font.SysFont(None, 40)

        self.selected = False
        self.text = text

        self.placeholder_surface = self.font.render(self.placeholder, True, (0, 0, 0))
        self.placeholder_rect = self.placeholder_surface.get_rect(midleft=(self.rect.midleft[0] + 10, self.rect.midleft[1]))

        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_interval = 0.5

        self.max_char = 30
        self.scroll_x = 0

    def render(self, screen):
        color = (200, 200, 200) if self.selected else (150, 150, 150)

        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)

        old_clip = screen.get_clip()
        screen.set_clip(self.rect)

        if self.text == "" and not self.selected:
            screen.blit(self.placeholder_surface, self.placeholder_rect)
        else:
            text_surface = self.font.render(self.text, True, (0, 0, 0))
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
                (0, 0, 0),
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


class MenusCollection:
    GAME = "game"
    MAIN = "main"
    SINGLEPLAYER = "singleplayer"
    MULTIPLAYER = "multiplayer"
    GAME_PAUSED = "paused"
    CREATE_WORLD = "create_world"
    SETTINGS_WORLD = "settings_world"
    LOADING_WORLD = "loading_world"

BUTTON_HEIGHT = 60
MARGIN_UI = 40

class MainMenu:
    def __init__(self, game):
        self.game = game

        self.menu = MenusCollection.MAIN
        self.menus = {}

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

    def open_settings_world(self, world_name):
        self.current_wn = world_name

        self.menus[MenusCollection.SETTINGS_WORLD] = [
            Texte(world_name, (self.center_x, 50, 160, 50), center_pos=True),

            Button(
                "Supprimer ce monde",
                (MARGIN_UI, self.screen_size[1] - ( MARGIN_UI + BUTTON_HEIGHT ) * 2, self.screen_size[0] - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: print("Supprimer le monde " + world_name)
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
        
    def reload(self):
        self.worlds_manager.reload()

        self.menus[MenusCollection.MAIN] = [
            Texte("TeraCraft", (self.center_x - 70, 50, 160, 50)),
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
                "Quitter",
                (self.center_x - 160, self.center_y + 100 - BUTTON_HEIGHT // 2, 320, BUTTON_HEIGHT),
                lambda: setattr(self.game, "running", False)
            )
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
            Button(
                "Retour",
                (self.center_x - 100, self.center_y - BUTTON_HEIGHT // 2, 200, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.MAIN)
            )
        ]

        self.menus[MenusCollection.LOADING_WORLD] = [
            Texte("Chargement du monde...", (self.center_x, self.center_y, 160, 50), center_pos=True)
        ]

        self.menus[MenusCollection.GAME] = []

        if self.is_menu(MenusCollection.SETTINGS_WORLD):
            self.open_settings_world(self.current_wn)
        else:
            self.menus[MenusCollection.SETTINGS_WORLD] = []

        self.menus[MenusCollection.CREATE_WORLD] = [
            Texte("Création d'un monde", (self.center_x, 50, 160, 50), center_pos=True),

            Button(
                "Retour",
                (MARGIN_UI, self.screen_size[1] - MARGIN_UI - BUTTON_HEIGHT, self.screen_size[0] // 2 - MARGIN_UI * 2, BUTTON_HEIGHT),
                lambda: self.set_menu(MenusCollection.SINGLEPLAYER)
            ),
            TextBox(
                (self.center_x - 160, self.center_y - BUTTON_HEIGHT // 2 - 100, 320, BUTTON_HEIGHT),
                "Nom du monde",
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