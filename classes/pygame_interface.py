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
    def __init__(self, text, pos, color=(255, 255, 255), center_pos=False, line_spacing=5, font_size=40):
        self.font = pygame.font.SysFont(None, font_size)
        self.text = text
        self.color = color
        self.line_spacing = line_spacing

        self.lines = text.split("\n")

        self.surfaces = [self.font.render(line, True, color) for line in self.lines]

        # calcul taille totale
        width = max(s.get_width() for s in self.surfaces) if self.surfaces else 0
        height = sum(s.get_height() for s in self.surfaces) + line_spacing * (len(self.surfaces) - 1)

        if center_pos:
            temp_rect = pygame.Rect(pos[0], pos[1], width, height)
            pos = (pos[0] - width // 2, pos[1] - height // 2)

        self.pos = pos
        self.width = width
        self.height = height

        rect = pygame.Rect(pos[0], pos[1], width, height)
        super().__init__(rect)

    def render(self, screen):
        x, y = self.pos

        for surf in self.surfaces:
            screen.blit(surf, (x, y))
            y += surf.get_height() + self.line_spacing

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

class ScrollContainer(ObjectInterface):
    def __init__(self, rect, scroll_speed=20, callback=None):
        super().__init__(rect, callback)
        self.children = []

        self.scroll_y = 0
        self.scroll_speed = scroll_speed

        self.content_height = 0

    def add(self, obj):
        self.children.append(obj)
        self.recalculate_content_height()

    def remove(self, obj):
        if obj in self.children:
            self.children.remove(obj)
            self.recalculate_content_height()

    def recalculate_content_height(self):
        self.content_height = 0
        for c in self.children:
            self.content_height = max(
                self.content_height,
                c.rect.bottom
            )

    # ---------- SCROLL ----------
    def handle_event(self, event):

        # scroll mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            if self.is_hover():
                self.scroll_y -= event.y * self.scroll_speed

                # clamp scroll
                max_scroll = max(0, self.content_height - self.rect.height)
                self.scroll_y = max(0, min(self.scroll_y, max_scroll))

        # propagate event to children (with offset)
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):

            for child in self.children:
                if self._is_child_visible(child):
                    child.handle_event(self._transform_event(event))

    # ---------- UPDATE ----------
    def update(self, dt):
        for child in self.children:
            if self._is_child_visible(child):
                child.update(dt)

    # ---------- RENDER ----------
    def render(self, screen):

        old_clip = screen.get_clip()
        screen.set_clip(self.rect)

        pygame.draw.rect(screen, (30, 30, 30), self.rect)

        offset_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        for child in self.children:
            if self._is_child_visible(child):
                original_y = child.rect.y

                # apply scroll offset
                child.rect.y -= self.scroll_y

                child.render(offset_surface)

                # restore position
                child.rect.y = original_y

        screen.blit(offset_surface, self.rect.topleft)

        screen.set_clip(old_clip)

    # ---------- VISIBILITY (CULLING) ----------
    def _is_child_visible(self, child):
        return (
            child.rect.bottom >= self.scroll_y and
            child.rect.top <= self.scroll_y + self.rect.height
        )

    # ---------- EVENT TRANSFORM ----------
    def _transform_event(self, event):
        # convert mouse position into scroll-local space
        if hasattr(event, "pos"):
            x, y = event.pos
            x -= self.rect.x
            y -= self.rect.y
            y += self.scroll_y

            new_event = pygame.event.Event(event.type, {
                **event.__dict__,
                "pos": (x, y)
            })
            return new_event

        return event
    
class ScrollList(ObjectInterface):
    def __init__(self, rect, item_height=80, spacing=10, scroll_speed=20):
        super().__init__(rect)

        self.items = []
        self.scroll_y = 0

        self.item_height = item_height
        self.spacing = spacing
        self.scroll_speed = scroll_speed

        self.content_height = 0

    def add(self, item):
        self.items.append(item)
        self.recalc()

    def clear(self):
        self.items = []
        self.recalc()

    def recalc(self):
        self.content_height = len(self.items) * (self.item_height + self.spacing)

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL and self.is_hover():
            self.scroll_y -= event.y * self.scroll_speed

            max_scroll = max(0, self.content_height - self.rect.height)
            self.scroll_y = max(0, min(self.scroll_y, max_scroll))

        # only visible items receive events
        for item in self.items:
            if self._visible(item):
                item.handle_event(event)

    def update(self, dt):
        for item in self.items:
            if self._visible(item):
                item.update(dt)

    def render(self, screen):
        old_clip = screen.get_clip()
        screen.set_clip(self.rect)

        pygame.draw.rect(screen, (15, 15, 15), self.rect)

        y = self.rect.y - self.scroll_y

        for item in self.items:
            item.rect.y = y
            item.render(screen)
            y += self.item_height + self.spacing

        screen.set_clip(old_clip)

    def _visible(self, item):
        return (
            item.rect.bottom >= self.scroll_y and
            item.rect.top <= self.scroll_y + self.rect.height
        )