import pygame

class ObjectInterface:
    def __init__(self, rect, callback=None, enable=True):
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.enable = enable

    def render(self, screen, color=(200, 200, 200)):
        pygame.draw.rect(screen, color, self.rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pygame.mouse.get_pos()):

                if self.enable:
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
    def __init__(self, text, rect, callback, enable=True ,
                 text_color=(255, 255, 255), 
                 border_color=(255, 255, 255), 
                 background_color=(0, 0, 0), 
                 background_color_hover=(50, 50, 50),
                 border_color_hover=(255, 255, 255)
                 ):
        
        super().__init__(rect, callback, enable)
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
                 border_color_hover=(255, 255, 255),
                 write_callback=None,
                 enter_callback=None
                 ):
        super().__init__(rect, ref)
        self.placeholder = placeholder
        self.font = pygame.font.SysFont(None, 40)

        self.selected = False
        self.text = text

        self.text_color = text_color
        self.placeholder_color = placeholder_color

        self.write_callback = write_callback
        self.enter_callback = enter_callback

        self.border_color = border_color
        self.background_color = background_color
        self.background_color_hover = background_color_hover
        self.border_color_hover = border_color_hover

        self.placeholder_surface = self.font.render(self.placeholder, True, self.placeholder_color)
        self.placeholder_rect = self.placeholder_surface.get_rect(midleft=(self.rect.midleft[0] + 10, self.rect.midleft[1]))

        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_interval = 0.5

        self.cursor_index = 0
        self.max_char = 30
        self.scroll_x = 0

    def move_cursor_index(self, value):
        self.cursor_index += value
        self.cursor_index = max(0, min(self.cursor_index, len(self.text)))

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

            cursor_text = self.text[:self.cursor_index]
            cursor_surface = self.font.render(cursor_text, True, self.text_color)
            cursor_x_local = cursor_surface.get_width()

            padding = 10
            visible_width = max_width

            # Si le curseur dépasse à droite
            if cursor_x_local - self.scroll_x > visible_width:
                self.scroll_x = cursor_x_local - visible_width

            # Si le curseur dépasse à gauche
            elif cursor_x_local - self.scroll_x < 0:
                self.scroll_x = cursor_x_local

            self.scroll_x = max(0, self.scroll_x)
            self.scroll_x = min(self.scroll_x, max(0, text_width - visible_width))
            
            text_rect = text_surface.get_rect(
                midleft=(self.rect.midleft[0] + 10 - self.scroll_x, self.rect.midleft[1])
            )

            screen.blit(text_surface, text_rect)

            if self.cursor_visible:
                cursor_x = text_rect.left + cursor_x_local

                pygame.draw.line(
                    screen,
                    self.text_color,
                    (cursor_x, text_rect.top),
                    (cursor_x, text_rect.bottom - 2),
                    2
                )

        screen.set_clip(old_clip)
    
    def handle_event(self, event):
        if self.selected:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if self.cursor_index > 0:
                        self.text = (
                            self.text[:self.cursor_index - 1] +
                            self.text[self.cursor_index:]
                        )
                        self.move_cursor_index(-1)

                    if self.write_callback:
                        self.write_callback()
                elif event.unicode and event.unicode.isprintable():

                    if len(self.text) < self.max_char:
                        self.text = (
                            self.text[:self.cursor_index] +
                            event.unicode +
                            self.text[self.cursor_index:]
                        )
                        self.move_cursor_index(1)
                
                    if self.write_callback:
                        self.write_callback()
                elif event.key == pygame.K_RETURN:
                    if self.enter_callback:
                        self.enter_callback()

                elif event.key == pygame.K_LEFT:
                    self.move_cursor_index(-1)
                elif event.key == pygame.K_RIGHT:
                    self.move_cursor_index(1)

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