from operator import inv
from classes import language
import pygame
from classes import game_property
from classes.inventory import Crafting_types, ItemStack

class Slot:
    def __init__(self, getter, setter, slot_type="normal", meta=None):
        self._get = getter
        self._set = setter
        self.type = slot_type
        self.meta = meta

    def get(self):
        return self._get()

    def set(self, item):
        self._set(item)

    def __str__(self):
        return f"Slot(type:{self.type}, meta:{self.meta})"

class UI_menu:
    def __init__(self, screen_size):
        self.update_screen_size(screen_size)
    
    def update_screen_size(self, screen_size):
        self.screen_size = screen_size
        self.cam_rect = pygame.Rect(-self.screen_size[0] // 2 + game_property.CHUNK_WIDTH * game_property.TILE_SIZE // 2, 0, self.screen_size[0], self.screen_size[1])
        self.tchat.update_screen_size(screen_size)

class UI:
    def __init__(self, screen_size, inventory, tchat):
        self.inventory = inventory
        self.tchat = tchat

        self.open_inventory = None

        self.dragged_slot = None
        self.drag_origin = None
        self.update_screen_size(screen_size)
        
        self.close_inv()

        self.margin = 15
        self.case_size = game_property.INVENTORY_SIZE_CASE + self.margin

        self.current_title_space = 0

        self._hotbar_font = pygame.font.SysFont("Arial", 16)
        self._hotbar_numbers = [
            self._hotbar_font.render(str(i+1), True, (255,255,255))
            for i in range(10)
        ]

    def update_screen_size(self, screen_size):
        self.screen_size = screen_size
        self.cam_rect = pygame.Rect(-self.screen_size[0] // 2 + game_property.CHUNK_WIDTH * game_property.TILE_SIZE // 2, 0, self.screen_size[0], self.screen_size[1])
        self.tchat.update_screen_size(screen_size)

    def update_pos_cam_rect(self, pos):
        self.cam_rect.x = pos[0]
        self.cam_rect.y = pos[1]

    def render(self, screen, player):
        self.update(player.inventory)

        if not self.is_open_inv():
            self.tchat.render(screen)

            self.render_hotbar(screen, player.inventory)
        else:
            self.render_chest(screen, self.open_inventory)
        
        self.render_tooltip(screen)

    def key_down(self, event):
        if event.key == pygame.K_ESCAPE:
            self.close_inv()

    def update(self, inv):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_item = None

        # inventaire ouvert
        if self.is_open_inv():
            for rect, slot in self.get_all_slots(self.open_inventory):
                if rect.collidepoint(mouse_pos):
                    item = slot.get()
                    if item:
                        self.hovered_item = item
                    return

        # hotbar (inventaire fermé)
        else:
            case_size = game_property.INVENTORY_SIZE_CASE
            margin = 15

            height = case_size + margin * 2
            width = margin + (case_size + margin) * inv.ui.case_number

            start_x = self.screen_size[0] // 2 - width // 2
            start_y = self.screen_size[1] - game_property.MARGIN_UI_SCREEN - height

            for i in range(min(len(inv.items), inv.ui.case_number)):
                col = i % inv.ui.case_number
                
                x = start_x + col * (case_size + margin) + margin
                y = start_y + margin

                rect = pygame.Rect(x, y, case_size, case_size)

                if rect.collidepoint(mouse_pos):
                    item = inv.items.get(i, None)
                    if item:
                        self.hovered_item = item
                    return
    
    def render_tooltip(self, screen):
        if not self.hovered_item:
            return

        if not self.hovered_item.item_property:
            return

        item = self.hovered_item
        mouse_x, mouse_y = pygame.mouse.get_pos()

        font_title = pygame.font.SysFont("Arial", 18, bold=True)
        font_desc = pygame.font.SysFont("Arial", 14)

        name = language.get_language_items(item.item_property.item_name, language.LANGUAGE_TYPE.FRANCE)
        if not name:
            name = item.item_property.item_name
        
        desc = item.item_property.description

        title_surf = font_title.render(name, True, (255, 255, 255))
        desc_surf = font_desc.render(desc, True, (200, 200, 200))

        width = max(title_surf.get_width(), desc_surf.get_width()) + 10
        height = title_surf.get_height() + desc_surf.get_height() + 10

        x = mouse_x + 15
        y = mouse_y + 15

        if x + width > self.screen_size[0]:
            x = mouse_x - width - 15
        if y + height > self.screen_size[1]:
            y = mouse_y - height - 15

        # fond
        bg = pygame.Surface((width, height), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 220))

        screen.blit(bg, (x, y))

        # texte
        screen.blit(title_surf, (x + 5, y + 3))
        screen.blit(desc_surf, (x + 5, y + 3 + title_surf.get_height()))
        
    def mouse_down(self, button):
        if not self.is_open_inv() or (button != 1 and button != 3):
            return
    
        mouse_pos = pygame.mouse.get_pos()

        for rect, slot in self.get_all_slots(self.open_inventory):
            if rect.collidepoint(mouse_pos):

                # PRIORITÉ AU RESULT
                if slot.type == "craft_result":
                    crafted = slot.meta.take_result()
                    if crafted:
                        self.dragged_slot = Slot(lambda: crafted, lambda x: None, "temp")
                        self.drag_origin = None
                        self.drag_origin_index = None
                        slot.set(None)

                else:
                    # NORMAL
                    item = slot.get()
                    if item:
                        if button == 3:
                            half_count = item.count // 2
                            if half_count > 0:
                                item.count -= half_count
                                self.dragged_slot = Slot(lambda: type(item)(item.item_property, half_count), lambda x: None, "temp")
                                self.drag_origin = slot
                                self.drag_origin_index = self.get_slot_index(slot)
                        else:
                            self.dragged_slot = Slot(lambda: item, lambda x: None, "temp")
                            self.drag_origin = slot
                            self.drag_origin_index = self.get_slot_index(slot)
                            slot.set(None)

        if self.dragged_slot:
            print(f"{self.dragged_slot}")

    def get_slot_index(self, target_slot):
        for i, (rect, slot) in enumerate(self.get_all_slots(self.open_inventory)):
            if slot._get() is target_slot._get():  # on compare le getter pour trouver le slot réel
                return i
        return None

    def mouse_up(self, button):
        if not self.is_open_inv() or (button != 1 and button != 3) or not self.dragged_slot:
            return

        mouse_pos = pygame.mouse.get_pos()
        dropped = False

        for i, (rect, slot) in enumerate(self.get_all_slots(self.open_inventory)):
            if rect.collidepoint(mouse_pos):
                if hasattr(self, "drag_origin_index") and i == self.drag_origin_index:
                    slot.set(self.dragged_slot.get())
                    dropped = True
                    break

                if slot.type == "craft_result":
                    print("In craft result")
                    break

                item_a = self.dragged_slot.get()
                item_b = slot.get()

                if not item_a:
                    break

                # STACK
                if item_a and item_b and item_a.item_property == item_b.item_property:
                    reste = item_b.add_item(item_a.count)

                    if reste == 0:
                        self.dragged_slot.set(None)
                        dropped = True
                    else:
                        item_a.count = reste

                # SWAP
                else:
                    print(f"Swap {item_a.item_property.item_name} with {item_b.item_property.item_name if item_b else 'None'}")
                    slot.set(item_a)

                    if item_b:
                        if self.drag_origin:
                            if self.drag_origin.type != "craft_result":
                                self.drag_origin.set(item_b)
                            else:
                                self.open_inventory.add_item(ItemStack(item_b.item_property, item_b.count))
                    dropped = True

                break

        if not dropped:
            if self.drag_origin:
                #self.open_inventory.add_item(ItemStack(self.dragged_slot.get().item_property, self.dragged_slot.get().count))

                origin_item = self.inventory.get_item(self.drag_origin_index)

                if origin_item:
                    item = self.dragged_slot.get()

                    item.count += origin_item.count
                    self.drag_origin.set(item)
                else:
                    self.drag_origin.set(self.dragged_slot.get())
            else:
                self.open_inventory.add_item(ItemStack(self.dragged_slot.get().item_property, self.dragged_slot.get().count))

        self.dragged_slot = None
        self.drag_origin = None

    def render_slots(self, screen, slots):
        i = 0
        for rect, slot in slots:
            pygame.draw.rect(screen, (60, 60, 60), rect)
            pygame.draw.rect(screen, (120, 120, 120), rect, 2)

            item = slot.get()
            if item:
                item.render(
                    screen,
                    (
                        rect.x + (self.case_size - game_property.INVENTORY_SIZE_CASE) // 2,
                        rect.y + (self.case_size - game_property.INVENTORY_SIZE_CASE) // 2
                    )
                )
            i += 1

    def get_craft_size(self, craft):
        return (craft.width + 1) * (self.case_size + self.margin) + self.margin, (craft.height) * (self.case_size + self.margin) + self.margin

    def render_crafting(self, screen, craft, start_x, start_y, inv, height):
        craft_width, craft_height = self.get_craft_size(craft)

        start_x = start_x - craft_width

        surface = pygame.Surface((craft_width, craft_height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 180))
        screen.blit(surface, (start_x, start_y + height // 2 - craft_height // 2))

        # grille crafting
        self.render_slots(screen, self.get_slots(inv, type="craft_input"))

        # slot résultat 
        result_slot = self.get_slots(inv, type="craft_result")
        self.render_slots(screen, result_slot)

    def get_inv_size_ui(self, inv):
        cols = inv.ui.case_number
        rows = (inv.size + cols - 1) // cols
        return cols * (self.case_size + self.margin) + self.margin, rows * (self.case_size + self.margin) + self.margin

    def render_chest(self, screen, inv):
        cols = inv.ui.case_number

        font = pygame.font.SysFont("Arial", 26)

        # texte
        text_surface = font.render(inv.title, True, (255, 255, 255))
        text_rect = text_surface.get_rect()

        # Taille totale du fond
        width, height = self.get_inv_size_ui(inv)

        # espace pour le titre
        self.current_title_space = text_rect.height + 10

        start_x = self.screen_size[0] // 2 - width // 2
        start_y = self.screen_size[1] // 2 - (height + self.current_title_space) // 2

        # centrer le texte
        text_rect.centerx = self.screen_size[0] // 2
        text_rect.y = start_y

        screen.blit(text_surface, text_rect)

        # fond inventaire
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 180))
        screen.blit(surface, (start_x, start_y + self.current_title_space))

        slots = self.get_slots(inv, type="inventory")

        self.render_slots(screen, slots)

        if hasattr(inv, "craft_manager"):
            self.render_crafting(screen, inv.craft_manager, start_x, (start_y + self.current_title_space), height=height, inv=inv)

        # item drag
        if self.dragged_slot and self.dragged_slot.get():
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.dragged_slot.get().render(
                screen,
                (mouse_x - self.case_size // 2, mouse_y - self.case_size // 2)
            )

    def get_slots(self, inv, type="inventory"):
        return [(rect, slot) for rect, slot in self.get_all_slots(inv) if slot.type == type]

    def get_all_slots(self, inv):
        slots = []

        cols = inv.ui.case_number

        width, height = self.get_inv_size_ui(inv)

        start_x = self.screen_size[0] // 2 - width // 2 + self.margin
        start_y = self.screen_size[1] // 2 - (height + self.current_title_space) // 2 + self.current_title_space

        # =========================
        # INVENTAIRE
        # =========================
        for i in range(inv.size):
            row = i // cols
            col = i % cols

            x = start_x + col * (self.case_size + self.margin)
            y = start_y + row * (self.case_size + self.margin) + self.margin

            rect = pygame.Rect(x, y, self.case_size, self.case_size)

            slot = Slot(
                lambda i=i: inv.items[i],
                lambda item, i=i: inv.items.__setitem__(i, item),
                "inventory"
            )

            slots.append((rect, slot))

        # =========================
        # CRAFT
        # =========================
        if hasattr(inv, "craft_manager"):
            craft = inv.craft_manager

            craft_width, craft_heigth = self.get_craft_size(craft)

            # Position du bloc craft (aligné avec render_crafting)
            craft_start_x = start_x - craft_width
            craft_start_y = start_y + self.margin + height // 2 - craft_heigth // 2

            # INPUTS
            for i in range(craft.size):
                row = i // craft.width
                col = i % craft.width

                #pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(start_x, start_y, craft_width, craft_width), 2)

                x = craft_start_x + col * (self.case_size + self.margin)
                y = craft_start_y + row * (self.case_size + self.margin)

                rect = pygame.Rect(x, y, self.case_size, self.case_size)

                slot = Slot(
                    lambda i=i: craft.get_item(i),
                    lambda item, i=i: craft.set_item(i, item),
                    "craft_input",
                    craft
                )

                slots.append((rect, slot))

            # RESULT SLOT (à droite du craft)
            result_x = craft_start_x + craft.width * (self.case_size + self.margin)
            result_y = craft_start_y + craft_heigth // 2 - (self.case_size + self.margin * 2) // 2

            rect = pygame.Rect(result_x, result_y, self.case_size, self.case_size)

            result_slot = Slot(
                lambda: craft.result,
                lambda item: None,
                "craft_result",
                craft
            )

            slots.append((rect, result_slot))

        return slots

    def highlight_block(self, screen, current_block, cam_rect, player):
        if not current_block:
            print("Erreur current_block is None")
            return

        # centre du bloc
        block_center_x = current_block[0] * game_property.TILE_SIZE + game_property.TILE_SIZE / 2
        block_center_y = current_block[1] * game_property.TILE_SIZE + game_property.TILE_SIZE / 2

        # centre du joueur
        player_center_x = player.rect.centerx
        player_center_y = player.rect.centery

        dx = block_center_x - player_center_x
        dy = block_center_y - player_center_y

        if dx*dx + dy*dy > game_property.MAX_ACTION_DISTANCE**2:
            return False
        
        world_x = current_block[0] * game_property.TILE_SIZE
        world_y = current_block[1] * game_property.TILE_SIZE

        draw_x, draw_y = game_property.world_to_screen(
            world_x,
            world_y,
            game_property.TILE_SIZE,
            cam_rect
        )
    
        rect = pygame.Rect(draw_x, draw_y, game_property.TILE_SIZE, game_property.TILE_SIZE)
        pygame.draw.rect(screen, (255,255,255), rect, 2)
    
    def render_hotbar(self, screen, inv):
        case_size = game_property.INVENTORY_SIZE_CASE
        margin = 15
        case_count = inv.ui.case_number
        selected_index = inv.ui.selected_index

        total_case_size = case_size + margin

        width = margin + total_case_size * case_count
        height = case_size + margin * 2

        # Cache surface
        if not hasattr(self, "_hotbar_surface") or self._hotbar_surface.get_size() != (width, height):
            self._hotbar_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            self._hotbar_surface.fill((0, 0, 0, 150))

        start_x = self.screen_size[0] // 2 - width // 2
        start_y = self.screen_size[1] - game_property.MARGIN_UI_SCREEN - height

        screen.blit(self._hotbar_surface, (start_x, start_y))

        font = self._hotbar_font

        for i in range(case_count):
            x = start_x + i * total_case_size + margin
            y = start_y + margin

            rect = pygame.Rect(x, y, case_size, case_size)

            pygame.draw.rect(screen, (60, 60, 60), rect)
            pygame.draw.rect(screen, (120, 120, 120), rect, 2)

            item = inv.items.get(i)
            if item:
                item.render(screen, (x, y))

            if i == selected_index:
                pygame.draw.rect(screen, (255, 255, 255), rect, 2)

            screen.blit(self._hotbar_numbers[i], (x + 5, y + 2))
    
    def is_open_inv(self):
        if self.open_inventory:
            return True
        return False
    
    def open_inv(self, inv, Crafting_type=Crafting_types.INV):
        self.open_inventory = inv
        inv.open_crafting(Crafting_type)
    
    def close_inv(self):
        if self.open_inventory:
            self.open_inventory.close_crafting()
        self.open_inventory = None