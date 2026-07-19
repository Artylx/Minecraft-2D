import pygame
from terrakit import context, config
from terrakit.audio_manager import AudioType

def lerp(a, b, t):
    return a + (b - a) * min(t, 1)


class ObjectInterface:

    def __init__(
            self,
            rect,
            callback=None,
            enable=True,
            annimation=False,
            sound_enabled=False,
            corner_radius=8,
            debug=False,
        ):

        self.rect = pygame.Rect(rect)

        self.callback = callback
        self.set_enable(enable)

        self.corner_radius = corner_radius
        self.pressed = False
        self.debug = debug

        # ---------- Animation ----------
        self.scale = 1
        self.target_scale = 1

        self.offset_y = 0
        self.target_offset_y = 0

        self.hover_scale = 1.08
        self.click_depth = 5

        self.animation_speed = 12
        self.click_speed = 18

        self.annimation = annimation
        self.sound_enabled = sound_enabled

        self.click_sound = context.get_resource_pack().audio_manager().get_audio(AudioType.CLICK)

    def set_enable(self, value):
        self.enable = value

    # ------------------------

    def get_rect(self):

        rect = self.rect.inflate(
            self.rect.width * (self.scale - 1),
            self.rect.height * (self.scale - 1)
        )

        rect.y += int(self.offset_y)

        return rect

    # ------------------------

    def is_hover(self):

        return self.rect.collidepoint(
            pygame.mouse.get_pos()
        )

    # ------------------------

    def handle_event(self, event):

        if not self.enable:
            return
        
        if self.debug:
            print(f"hover={self.is_hover()}, event={event.type}, pressed={self.pressed}")

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1 and self.is_hover():
                
                if self.annimation:
                    self.target_offset_y = self.click_depth

                if self.sound_enabled:
                    self.click_sound.set_volume(config.Config().get("sound_volume") / 100)
                    self.click_sound.play()

                self.pressed = True

        elif event.type == pygame.MOUSEBUTTONUP:
            
            if self.pressed:
                self.target_offset_y = 0

                if self.callback and self.is_hover():
                    self.callback()
                    
                self.pressed = False

    # ------------------------

    def update(self, dt):

        if not self.enable:
            return

        if self.is_hover():
            if self.annimation:
                self.target_scale = self.hover_scale
        else:
            self.target_scale = 1

        self.scale = lerp(
            self.scale,
            self.target_scale,
            dt * self.animation_speed
        )

        self.offset_y = lerp(
            self.offset_y,
            self.target_offset_y,
            dt * self.click_speed
        )

class Texte(ObjectInterface):
    def __init__(self, text, pos, color=(255, 255, 255), center_pos=False, line_spacing=5, font_size=40):
        self.font = pygame.font.SysFont(None, font_size)
        self.text = text
        self.color = color
        self.line_spacing = line_spacing
        self.center_pos = center_pos
        self.pos = pos

        self.deep_update()

        super().__init__(self.rect)

    def set_text(self, text):
        self.text = text
        self.deep_update()

    def deep_update(self):
        self.lines = self.text.split("\n")

        self.surfaces = [self.font.render(line, True, self.color) for line in self.lines]

        # calcul taille totale
        width = max(s.get_width() for s in self.surfaces) if self.surfaces else 0
        height = sum(s.get_height() for s in self.surfaces) + self.line_spacing * (len(self.surfaces) - 1)

        if self.center_pos:
            self.pos = (self.pos[0] - width // 2, self.pos[1] - height // 2)

        self.width = width
        self.height = height

        self.rect = pygame.Rect(self.pos[0], self.pos[1], self.width, self.height)

    def render(self, screen):
        x, y = self.rect.topleft

        for surf in self.surfaces:
            screen.blit(surf, (x, y))
            y += surf.get_height() + self.line_spacing

class TexteReferencable(Texte):
    def __init__(self, text, pos, ref="", color=(255, 255, 255), center_pos=False, line_spacing=5, font_size=40):
        super().__init__(text, pos, color, center_pos, line_spacing, font_size)
        self.ref = ref

    def is_ref(self, ref):
        return self.ref == ref

class Button(ObjectInterface):
    def __init__(self, text, rect, callback, enable=True ,
                 text_color=(255, 255, 255), 
                 border_color=(255, 255, 255), 
                 background_color=(0, 0, 0), 
                 background_color_hover=(50, 50, 50),
                 border_color_hover=(255, 255, 255),
                 corner_radius=8,
                 disable_text_color=(200, 200, 200),
                 disable_border_color=(160, 160, 160),
                 disable_background_color=(100, 100, 100),
                 debug=False,
                 ):
        
        self.text = text
        self.font = pygame.font.SysFont(None, 40)

        self.text_color = text_color
        self.border_color = border_color
        self.background_color = background_color
        self.background_color_hover = background_color_hover
        self.border_color_hover = border_color_hover

        self.disable_text_color = disable_text_color
        self.disable_border_color = disable_border_color
        self.disable_background_color = disable_background_color

        super().__init__(rect, callback, enable, annimation=True, sound_enabled=True, corner_radius=corner_radius, debug=debug)

    def set_enable(self, value):
        super().set_enable(value)
        self.update_layout()

    def update_layout(self):
        if self.enable:
            self.text_surface = self.font.render(self.text, True, self.text_color)
            self.text_rect = self.text_surface.get_rect(center=self.rect.center)
        else:
            self.text_surface = self.font.render(self.text, True, self.disable_text_color)
            self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def render(self, screen):

        rect = self.get_rect()

        bg = self.background_color_hover if self.is_hover() else self.background_color
        bd = self.border_color_hover if self.is_hover() else self.border_color

        bg = bg if self.enable else self.disable_background_color
        bd = bd if self.enable else self.disable_border_color

        pygame.draw.rect(
            screen,
            bg,
            rect,
            border_radius=self.corner_radius
        )

        pygame.draw.rect(
            screen,
            bd,
            rect,
            2,
            border_radius=self.corner_radius
        )

        screen.blit(
            self.text_surface,
            self.text_rect
        )

class ObjectReferencable(ObjectInterface):
    def __init__(self, rect, ref="", callback=None, sound_enabled=False, annimation=False, corner_radius=8, debug=False):
        super().__init__(rect, callback, sound_enabled=sound_enabled, annimation=annimation, corner_radius=corner_radius, debug=debug)
        self.ref = ref

    def is_ref(self, ref):
        return self.ref == ref
    
class Panel(ObjectReferencable):
    def __init__(
        self,
        rect,
        ref="",
        color=(30,30,30),
        alpha=220,
        spacing=10,
        padding=15,
        corner_radius=12,
        debug=False
    ):

        super().__init__(
            rect,
            ref=ref,
            corner_radius=corner_radius,
            debug=debug
        )

        self.color = color
        self.alpha = alpha

        self.spacing = spacing
        self.padding = padding

        self.controls = []


    # ------------------------
    # Ajouter un contrôle
    # ------------------------

    def add(self, control):

        self.controls.append(control)

        self.update_layout()


    # ------------------------
    # Organisation verticale
    # ------------------------

    def update_layout(self):

        y = self.rect.y + self.padding

        for control in self.controls:

            control.rect.x = (
                self.rect.x +
                (self.rect.width - control.rect.width) // 2
            )

            control.rect.y = y

            y += (
                control.rect.height +
                self.spacing
            )


    # ------------------------
    # Events
    # ------------------------

    def handle_event(self, event):

        if not self.enable:
            return

        for control in self.controls:
            control.handle_event(event)


    # ------------------------
    # Update
    # ------------------------

    def update(self, dt):

        for control in self.controls:
            control.update(dt)


    # ------------------------
    # Render
    # ------------------------

    def render(self, screen):

        rect = self.get_rect()

        surface = pygame.Surface(
            rect.size,
            pygame.SRCALPHA
        )


        pygame.draw.rect(
            surface,
            (*self.color, self.alpha),
            surface.get_rect(),
            border_radius=self.corner_radius
        )


        screen.blit(
            surface,
            rect
        )


        for control in self.controls:
            control.render(screen)
    
class Slider(ObjectReferencable):
    def __init__(
        self,
        rect,
        ref="",
        min_value=0,
        max_value=100,
        value=50,
        callback=None,
        background_color=(50,50,50),
        bar_color=(0,180,255),
        cursor_color=(255,255,255),
        cursor_radius=10,
        corner_radius=8
    ):

        super().__init__(
            rect,
            ref,
            callback,
            corner_radius=corner_radius
        )

        self.min_value = min_value
        self.max_value = max_value

        self.value = value
        self.target_value = value

        self.background_color = background_color
        self.bar_color = bar_color
        self.cursor_color = cursor_color

        self.cursor_radius = cursor_radius

        self.dragging = False


    # ------------------------
    # Valeur
    # ------------------------

    def set_value(self, value):

        value = int(value)

        self.value = max(
            self.min_value,
            min(value, self.max_value)
        )

        if self.callback:
            self.callback(self)


    def get_value(self):
        return self.value


    # ------------------------
    # Position curseur
    # ------------------------

    def value_to_x(self):

        ratio = (
            self.value - self.min_value
        ) / (
            self.max_value - self.min_value
        )

        return (
            self.rect.left +
            ratio * self.rect.width
        )


    def x_to_value(self, x):

        ratio = (
            x - self.rect.left
        ) / self.rect.width

        ratio = max(0, min(1, ratio))

        value = (
            self.min_value +
            ratio * (self.max_value - self.min_value)
        )

        return round(value)


    # ------------------------
    # Events
    # ------------------------

    def handle_event(self, event):

        if not self.enable:
            return


        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1 and self.is_hover():

                self.dragging = True

                self.set_value(
                    self.x_to_value(event.pos[0])
                )


        elif event.type == pygame.MOUSEMOTION:

            if self.dragging:

                self.set_value(
                    self.x_to_value(event.pos[0])
                )


        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1:

                self.dragging = False


    # ------------------------
    # Render
    # ------------------------

    def render(self, screen):

        rect = self.get_rect()


        # barre de fond

        pygame.draw.rect(
            screen,
            self.background_color,
            rect,
            border_radius=self.corner_radius
        )


        # progression

        progress_width = (
            self.value - self.min_value
        ) / (
            self.max_value - self.min_value
        ) * rect.width


        progress_rect = pygame.Rect(
            rect.x,
            rect.y,
            progress_width,
            rect.height
        )


        pygame.draw.rect(
            screen,
            self.bar_color,
            progress_rect,
            border_radius=self.corner_radius
        )


        # curseur

        pygame.draw.circle(
            screen,
            self.cursor_color,
            (
                int(self.value_to_x()),
                rect.centery
            ),
            self.cursor_radius
        )

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
        rect = self.get_rect()
        bg_color = self.background_color_hover if self.selected else self.background_color
        bd_color = self.border_color_hover if self.selected else self.border_color

        pygame.draw.rect(screen, bg_color, rect, border_radius=self.corner_radius)
        pygame.draw.rect(screen, bd_color, rect, 2, border_radius=self.corner_radius)

        old_clip = screen.get_clip()
        screen.set_clip(rect)

        if self.text == "" and not self.selected:
            screen.blit(self.placeholder_surface, self.placeholder_rect)
        else:
            text_surface = self.font.render(self.text, True, self.text_color)
            text_width = text_surface.get_width()

            max_width = rect.width - 20  # padding

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
                midleft=(rect.midleft[0] + 10 - self.scroll_x, rect.midleft[1])
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
            if event.button == 1:
                if self.rect.collidepoint(event.pos):

                    # activation
                    self.selected = True

                    # 🔥 place le curseur à la fin
                    self.cursor_index = len(self.text)

                    # optionnel : reset scroll pour focus fin
                    self.scroll_x = 0

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

        rect = self.get_rect()

        image = pygame.transform.smoothscale(
            self.surface,
            rect.size
        )

        screen.blit(image, rect)

class Surface(ObjectInterface):
    def __init__(
        self,
        rect,
        color=(200, 200, 200),
        alpha=255,
        callback=None,
        corner_radius=0
    ):
        super().__init__(
            rect,
            callback,
            corner_radius=corner_radius
        )

        self.color = color
        self.alpha = alpha

    def render(self, screen):

        rect = self.get_rect()

        surface = pygame.Surface(
            rect.size,
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            surface,
            (*self.color, self.alpha),
            surface.get_rect(),
            border_radius=self.corner_radius
        )

        screen.blit(surface, rect)

class SurfaceReferencable(ObjectReferencable):
    def __init__(self, rect, ref="", color=(200, 200, 200), alpha=255, callback=None):
        super().__init__(rect, ref=ref, callback=callback)

        self.color = color
        self.alpha = alpha

        self.surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        self.surface.fill((self.color[0], self.color[1], self.color[2], self.alpha))
    
    def render(self, screen):
        screen.blit(self.surface, self.rect)

class ItemsScrollContainer(SurfaceReferencable):
    def __init__(
        self,
        rect,
        ref="",
        color=(0, 0, 0),
        scroll_speed=25,
        spacing=120,
        item_height=80,
        center_elmt=False,
        spacing_border=120,
    ):
        super().__init__(rect, ref=ref, color=color)

        self.items = []

        self.scroll_y = 0
        self.scroll_speed = scroll_speed

        self.spacing = spacing
        self.item_height = item_height
        self.center_elmt = center_elmt
        self.spacing_border = spacing_border
        self.content_height = 0

        # SCROLLBAR DRAG
        self.dragging_scrollbar = False
        self.drag_offset_y = 0
        self.scrollbar_width = 10

        self.scrollbar_color = (80, 80, 80)
        self.scrollbar_handle_color = (180, 180, 180)

    # -----------------------------
    # ITEMS
    # -----------------------------
    def set_items(self, items):
        self.items = items
        self.update_height()

    def add_item(self, item):
        self.items.append(item)
        self.update_height()

    def update_height(self):

        if len(self.items) == 0:
            self.content_height = 0
            return

        self.content_height = (
            len(self.items) * self.item_height +
            (len(self.items) - 1) * self.spacing + self.spacing_border * 2
        )

    def get_item(self, ref):
        for item in self.items:

            if hasattr(item, "ref"):
                if item.is_ref(ref):
                    return item
        return None

    # -----------------------------
    # EVENTS
    # -----------------------------
    def handle_event(self, event):

        # -----------------------------
        # SCROLL
        # -----------------------------
        if event.type == pygame.MOUSEWHEEL:
            if self.is_hover():

                self.scroll_y -= event.y * self.scroll_speed

                max_scroll = max(
                    0,
                    self.content_height - self.rect.height
                )

                self.scroll_y = max(
                    0,
                    min(self.scroll_y, max_scroll)
                )

        # -----------------------------
        # CHILD EVENTS
        # -----------------------------
        for item in self.items:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not self.is_hover(): # Sécurité pour pas cliquer dans le vide et tomber sur un controle invisible pour l'utilisateur
                    continue

            item.handle_event(event)
        
        # -----------------------------
        # SCROLLBAR CLICK / DRAG
        # -----------------------------

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if self.content_height > self.rect.height:

                    _, handle_rect = self.get_scrollbar_rects()

                    if handle_rect.collidepoint(event.pos):

                        self.dragging_scrollbar = True

                        self.drag_offset_y = (
                            event.pos[1] - handle_rect.y
                        )

                        return
        if event.type == pygame.MOUSEMOTION:

            if self.dragging_scrollbar:

                bar_rect, handle_rect = self.get_scrollbar_rects()

                new_y = (
                    event.pos[1]
                    - self.drag_offset_y
                )

                min_y = bar_rect.y
                max_y = bar_rect.bottom - handle_rect.height

                new_y = max(
                    min_y,
                    min(new_y, max_y)
                )


                ratio = (
                    new_y - min_y
                ) / (max_y - min_y)


                self.scroll_y = (
                    self.content_height - self.rect.height
                ) * ratio

                return
        if event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1:
                self.dragging_scrollbar = False

    # -----------------------------
    # UPDATE
    # -----------------------------
    def update(self, dt):
        for item in self.items:
            item.update(dt) 

    # -----------------------------
    # RENDER
    # -----------------------------
    def render(self, screen):

        super().render(screen)

        old_clip = screen.get_clip()
        screen.set_clip(self.rect)

        y = self.rect.y - self.scroll_y + self.spacing_border

        # -----------------------------
        # ITEMS
        # -----------------------------
        for item in self.items:

            if not self.center_elmt:
                x = self.rect.x + 10
            else:
                x = self.rect.x + (
                    self.rect.width - item.rect.width
                ) // 2

            item.rect.topleft = (x, y)

            item.render(screen)

            y += self.item_height + self.spacing

        screen.set_clip(old_clip)

        # -----------------------------
        # SCROLLBAR
        # -----------------------------
        self.render_scrollbar(screen)

    # -----------------------------
    # SCROLLBAR
    # -----------------------------
    def render_scrollbar(self, screen):

        if self.content_height <= self.rect.height:
            return

        bar_rect, handle_rect = self.get_scrollbar_rects()

        pygame.draw.rect(
            screen,
            self.scrollbar_color,
            bar_rect,
            border_radius=8
        )

        pygame.draw.rect(
            screen,
            self.scrollbar_handle_color,
            handle_rect,
            border_radius=8
        )

    def get_scrollbar_rects(self):

        bar_rect = pygame.Rect(
            self.rect.right - self.scrollbar_width - 4,
            self.rect.y + 4,
            self.scrollbar_width,
            self.rect.height - 8
        )

        visible_ratio = self.rect.height / self.content_height

        handle_height = max(
            30,
            int(bar_rect.height * visible_ratio)
        )

        max_scroll = self.content_height - self.rect.height

        scroll_ratio = self.scroll_y / max_scroll if max_scroll > 0 else 0

        handle_y = (
            bar_rect.y +
            (bar_rect.height - handle_height) * scroll_ratio
        )

        handle_rect = pygame.Rect(
            bar_rect.x,
            handle_y,
            bar_rect.width,
            handle_height
        )

        return bar_rect, handle_rect
    
class LoadingBar(ObjectReferencable):
    def __init__(
        self,
        rect,
        ref="",
        value=0,
        background_color=(50,50,50),
        progress_color=(0,200,100),
        border_color=(255,255,255),
        border_width=2,
        corner_radius=10,
        smooth=True
    ):

        super().__init__(
            rect, ref,
            corner_radius=corner_radius
        )

        self.value = value
        self.target_value = value

        self.background_color = background_color
        self.progress_color = progress_color
        self.border_color = border_color

        self.border_width = border_width
        self.smooth = smooth

        self.animation_speed = 8


    def set_value(self, value):
        self.target_value = max(0, min(value, 100))


    def update(self, dt):

        if self.smooth:

            self.value = lerp(
                self.value,
                self.target_value,
                dt * self.animation_speed
            )

        else:
            self.value = self.target_value


    def render(self, screen):

        rect = self.get_rect()


        # Fond
        pygame.draw.rect(
            screen,
            self.background_color,
            rect,
            border_radius=self.corner_radius
        )


        # Progression
        progress_width = int(
            rect.width * (self.value / 100)
        )

        if progress_width > 0:

            progress_rect = pygame.Rect(
                rect.x,
                rect.y,
                progress_width,
                rect.height
            )

            pygame.draw.rect(
                screen,
                self.progress_color,
                progress_rect,
                border_radius=self.corner_radius
            )


        # Bordure
        if self.border_width:

            pygame.draw.rect(
                screen,
                self.border_color,
                rect,
                self.border_width,
                border_radius=self.corner_radius
            )