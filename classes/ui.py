from classes import language
import pygame
from classes import game_property, game_type
from classes.inventory import Crafting_types, ItemStack, SlotWrapper, CraftManager, FurnaceManager, ChestManager
    
class DragState:
    def __init__(self):
        self.stack = None
        self.source_slot = None
    
class InventoryController:
    def __init__(self, inventory):
        self.inventory = inventory
        self.drag = DragState()

    def start_drag(self, slot, inv):
        if not slot:
            return
        
        if slot.is_empty():
            return

        self.drag.stack = slot.get()

        if not (slot.get_type() == "craft_result" or slot.get_type() == "furnace_output"):
            self.drag.source_slot = slot

        slot.set(None)

    def start_split_drag(self, slot, inv):
        if slot.is_empty():
            return
        
        if slot.get_type() == "craft_result" or slot.get_type() == "furnace_output":
            return

        item = slot.get()

        half = max(item.count // 2, 1)

        self.drag.stack = ItemStack(item.item_property, half)
        self.drag.source_slot = slot
        item.count -= half

        if item.count <= 0:
            slot.set(None)

    def drop(self, target):
        if not self.drag.stack or not target:
            return

        if not self.can_drop(target, self.drag.stack):
            self.drop_to_drag()
            return     

        # EMPTY
        if target.is_empty():
            target.set(self.drag.stack)
            self._clear()
            return

        # STACK
        if self.inventory.try_stack_item(self.drag.stack, target):
            if self.drag.stack.count <= 0:
                self._clear()
            else:
                self.drop_outside()
            return

        # SWAP
        if not self.can_drop(self.drag.source_slot, target.get()):
            self.drop_to_drag()
            return

        temp = target.get()
        target.set(self.drag.stack)

        self.drag.source_slot.set(temp)
        self._clear()

    def can_drop(self, target, stack):
        if not target:
            return False

        if target.get_type() == "craft_result" or target.get_type() == "furnace_output":
            return False
        
        if target.get_type() == "furnace_input":
            if not stack.item_property.heatable:
                return False
            
        if target.get_type() == "furnace_fuel":
            if not stack.item_property.is_fuel():
                return False
        
        return True

    def drop_to_drag(self):
        if self.drag.source_slot:
            if self.drag.source_slot.is_empty():

                self.drag.source_slot.set(self.drag.stack)
                self._clear()
                return
            
            elif self.inventory.try_stack_item(self.drag.stack, self.drag.source_slot):
                if self.drag.stack.count <= 0:
                    self._clear()
                else:
                    self.drop_outside()
                return
            
        self.drop_outside()

        self._clear()
        return

    def drop_outside(self):
        self.inventory.insert(self.drag.stack)
        self._clear()

    def _clear(self):
        self.drag = DragState()

    def is_draging(self):
        return True if self.drag.stack else None

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

        self.update_screen_size(screen_size)
        
        self.close_inv()

        self.margin = 15
        self.case_size = game_property.INVENTORY_SIZE_CASE + self.margin

        self.current_title_space = 0

        self.controller = InventoryController(inventory)

        self._hotbar_font = pygame.font.SysFont("Arial", 16)
        self._hotbar_numbers = [
            self._hotbar_font.render(str(i+1), True, (255,255,255))
            for i in range(10)
        ]

        self.buttons = {
            1: False,
            3: False,
        }

    def update_screen_size(self, screen_size):
        self.screen_size = screen_size
        self.cam_rect = pygame.Rect(-self.screen_size[0] // 2 + game_property.CHUNK_WIDTH * game_property.TILE_SIZE // 2, 0, self.screen_size[0], self.screen_size[1])
        self.tchat.update_screen_size(screen_size)

    def update_pos_cam_rect(self, pos):
        self.cam_rect.x = pos[0]
        self.cam_rect.y = pos[1]

    def render(self, screen, player):
        self.update_hovered_item(player.inventory)

        if not self.is_open_inv():
            self.tchat.render(screen)

            self.render_hotbar(screen, player.inventory)
        else:
            if self.opened_chest:
                self.render_chest_ui(screen)
            else:
                self.render_chest(screen, self.open_inventory)
            self.render_drag(screen)
        
        self.render_tooltip(screen)

    def render_drag(self, screen):
        if self.controller.drag.stack:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            self.controller.drag.stack.render(
                screen,
                (mouse_x - game_property.INVENTORY_SIZE_CASE // 2,
                mouse_y - game_property.INVENTORY_SIZE_CASE // 2)
            )

    def key_down(self, event):
        if event.key == pygame.K_ESCAPE:
            self.close_inv()

    def update(self, dt):
        
        if self.is_furnace():
            self.opened_furnace.update(dt)

    def update_hovered_item(self, inv):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_item = None

        # =========================
        # INVENTAIRE OUVERT
        # =========================
        if self.is_open_inv():

            for rect, slot in self.get_all_open_slots():

                if rect.collidepoint(mouse_pos):

                    item = slot.get_ui()

                    if item:
                        self.hovered_item = item

                    return

        # =========================
        # HOTBAR
        # =========================
        else:

            case_size = game_property.INVENTORY_SIZE_CASE
            margin = 15

            height = case_size + margin * 2
            width = margin + (case_size + margin) * inv.ui.case_number

            start_x = self.screen_size[0] // 2 - width // 2
            start_y = self.screen_size[1] - game_property.MARGIN_UI_SCREEN - height

            for i in range(inv.ui.case_number):

                x = start_x + i * (case_size + margin) + margin
                y = start_y + margin

                rect = pygame.Rect(x, y, case_size, case_size)

                if rect.collidepoint(mouse_pos):

                    item = inv.items.get(i)

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

    def other_button(self, current):
        if current == 1:
            return 3
        elif current == 3:
            return 1
        return 0
    
    def reset_btns(self):
        self.buttons = {
            1: False,
            3: False,
        }
        
    def mouse_down(self, button):
        if not self.is_open_inv():

            if button == 1:
                case_size = game_property.INVENTORY_SIZE_CASE
                margin = 15

                height = case_size + margin * 2
                width = margin + (case_size + margin) * self.inventory.ui.case_number

                start_x = self.screen_size[0] // 2 - width // 2
                start_y = self.screen_size[1] - game_property.MARGIN_UI_SCREEN - height

                for i in range(self.inventory.ui.case_number):

                    x = start_x + i * (case_size + margin) + margin
                    y = start_y + margin

                    rect = pygame.Rect(x, y, case_size, case_size)

                    if rect.collidepoint(pygame.mouse.get_pos()):
                        self.inventory.ui.selected_index = i
                        return

            return

        mouse_pos = pygame.mouse.get_pos()
        slot = self.get_slot_from_mouse(mouse_pos)

        if self.buttons[button]:
            return
        
        if self.buttons[self.other_button(button)]:
            return
        
        self.buttons[button] = True

        if slot is None:
            return

        if button == 1:
            self.controller.start_drag(slot, self.open_inventory)

        elif button == 3:
            self.controller.start_split_drag(slot, self.open_inventory)

    def mouse_up(self, button):
        if not self.is_open_inv():
            return
        
        if not self.buttons[button]:
            return
        
        self.buttons[button] = False

        mouse_pos = pygame.mouse.get_pos()
        slot = self.get_slot_from_mouse(mouse_pos)

        if slot is None:
            self.controller.drop_outside()
        else:
            self.controller.drop(slot)
    
    def get_slot(self, index):
        for i, (rect, slot) in enumerate(self.get_all_slots(self.open_inventory)):
            if i == index:
                return slot
        return None
    
    def get_slot_from_mouse(self, mouse_pos):
        for rect, slot in self.get_all_open_slots():
            if rect.collidepoint(mouse_pos):
                return slot
        return None

    def render_slots(self, screen, slots):
        i = 0
        for rect, slot in slots:
            pygame.draw.rect(screen, (60, 60, 60), rect)
            pygame.draw.rect(screen, (120, 120, 120), rect, 2)

            item = slot.get_ui()
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

    def get_furnace_size(self, furnaceManager):
        return 4 * (self.case_size + self.margin) + self.margin, self.case_size + self.margin * 2

    def render_furnace(self, screen, furnaceManager, start_x, start_y, inv, height):
        width_f, height_f = self.get_furnace_size(furnaceManager)

        start_x = start_x - width_f
        start_y = start_y + height // 2 - height_f // 2

        surface = pygame.Surface((width_f, height_f), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 180))
        screen.blit(surface, (start_x, start_y))

        # slot input
        self.render_slots(screen, self.get_slots(inv, type="furnace_input"))

        # slot fuel
        self.render_slots(screen, self.get_slots(inv, type="furnace_fuel"))

        # slot output
        self.render_slots(screen, self.get_slots(inv, type="furnace_output"))

        # =========================
        # BARRE DE PROGRESSION
        # =========================

        if furnaceManager.max_progress > 0:
            progress_ratio = furnaceManager.progress / furnaceManager.max_progress
        else:
            progress_ratio = 0

        bar_width = self.case_size - 10
        bar_height = 8

        progress_x = start_x + 3 * (self.case_size + self.margin) + self.margin + 5
        progress_y = start_y + 20

        # fond
        pygame.draw.rect(
            screen,
            (50, 50, 50),
            (progress_x, progress_y, bar_width, bar_height)
        )

        # remplissage
        pygame.draw.rect(
            screen,
            (0, 220, 0),
            (
                progress_x,
                progress_y,
                int(bar_width * progress_ratio),
                bar_height
            )
        )

        # =========================
        # BARRE FUEL
        # =========================

        if furnaceManager.max_burn_time > 0:
            fuel_ratio = furnaceManager.burn_time / furnaceManager.max_burn_time
        else:
            fuel_ratio = 0

        fuel_width = 8
        fuel_height = self.case_size

        fuel_x = start_x + 2 * (self.case_size + self.margin) + 10
        fuel_y = start_y + self.margin

        # fond
        pygame.draw.rect(
            screen,
            (50, 50, 50),
            (fuel_x, fuel_y, fuel_width, fuel_height)
        )

        # remplissage du bas vers le haut
        filled = int(fuel_height * fuel_ratio)

        pygame.draw.rect(
            screen,
            (255, 140, 0),
            (
                fuel_x,
                fuel_y + (fuel_height - filled),
                fuel_width,
                filled
            )
        )

    def render_chest_ui(self, screen):
        chest_inv = self.opened_chest.inventory
        player_inv = self.open_inventory

        chest_width, chest_height = self.get_inv_size_ui(chest_inv)
        player_width, player_height = self.get_inv_size_ui(player_inv)

        total_width = max(chest_width, player_width)

        spacing = 40

        total_height = chest_height + player_height + spacing + 60

        start_x = self.screen_size[0] // 2 - total_width // 2
        start_y = self.screen_size[1] // 2 - total_height // 2

        # =========================
        # TITRE COFFRE
        # =========================

        font = pygame.font.SysFont("Arial", 26)

        chest_text = font.render("Chest", True, (255,255,255))
        screen.blit(chest_text, (start_x, start_y))

        chest_y = start_y + 40

        # fond coffre
        surface = pygame.Surface((chest_width, chest_height), pygame.SRCALPHA)
        surface.fill((0,0,0,180))

        screen.blit(surface, (start_x, chest_y))

        self.render_slots(
            screen,
            self.get_inventory_slots(
                chest_inv,
                start_x,
                chest_y
            )
        )

        # =========================
        # INVENTAIRE JOUEUR
        # =========================

        player_text = font.render(player_inv.title, True, (255,255,255))

        player_y = chest_y + chest_height + spacing

        screen.blit(player_text, (start_x, player_y))

        player_inv_y = player_y + 40

        surface = pygame.Surface((player_width, player_height), pygame.SRCALPHA)
        surface.fill((0,0,0,180))

        screen.blit(surface, (start_x, player_inv_y))

        self.render_slots(
            screen,
            self.get_inventory_slots(
                player_inv,
                start_x,
                player_inv_y
            )
        )

    def get_all_open_slots(self):
        slots = []
        
        if self.opened_chest:
            chest_inv = self.opened_chest.inventory

            chest_width, chest_height = self.get_inv_size_ui(chest_inv)
            player_width, player_height = self.get_inv_size_ui(self.open_inventory)

            total_width = max(chest_width, player_width)

            spacing = 40

            total_height = chest_height + player_height + spacing + 60

            start_x = self.screen_size[0] // 2 - total_width // 2 - self.margin
            start_y = self.screen_size[1] // 2 - total_height // 2

            chest_y = start_y + 40

            slots += self.get_inventory_slots(
                chest_inv,
                start_x,
                chest_y
            )

            player_y = chest_y + chest_height + spacing + 40

            slots += self.get_inventory_slots(
                self.open_inventory,
                start_x,
                player_y
            )

        else:
            slots += self.get_all_slots(self.open_inventory)

        return slots

    def get_inventory_slots(self, inv, start_x, start_y):
        slots = []

        cols = inv.ui.case_number

        for i in range(inv.size):
            row = i // cols
            col = i % cols

            x = start_x + self.margin + col * (self.case_size + self.margin)
            y = start_y + self.margin + row * (self.case_size + self.margin)

            rect = pygame.Rect(x, y, self.case_size, self.case_size)

            slot = SlotWrapper(
                ui_getter=lambda i=i: inv.items.get(i),
                setter=lambda item, i=i: inv.items.__setitem__(i, item)
            )

            slots.append((rect, slot))

        return slots

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

        if self.is_crafting():
            self.render_crafting(screen, self.craft_manager, start_x, (start_y + self.current_title_space), height=height, inv=inv)
        
        if self.is_furnace():
            self.render_furnace(screen, self.opened_furnace, start_x, (start_y + self.current_title_space), height=height, inv=inv)
        

    def get_slots(self, inv, type="inventory"):
        return [(rect, slot) for rect, slot in self.get_all_slots(inv) if slot.get_type() == type]

    def get_all_slots(self, inv):
        slots = []

        width, height = self.get_inv_size_ui(inv)

        start_x = self.screen_size[0] // 2 - width // 2 + self.margin
        start_y = self.screen_size[1] // 2 - (height + self.current_title_space) // 2 + self.current_title_space

        slots += self.get_inventory_slots(
            inv,
            start_x - self.margin,
            start_y
        )

        # =========================
        # CRAFT
        # =========================
        if self.is_crafting():
            craft = self.craft_manager

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

                slot = SlotWrapper(
                    ui_getter=lambda i=i: craft.get_item(i),
                    setter=lambda item, i=i: craft.set_item(i, item),
                    slot_type="craft_input"
                )

                slots.append((rect, slot))

            # RESULT SLOT (à droite du craft)
            result_x = craft_start_x + craft.width * (self.case_size + self.margin)
            result_y = craft_start_y + craft_heigth // 2 - (self.case_size + self.margin * 2) // 2

            rect = pygame.Rect(result_x, result_y, self.case_size, self.case_size)

            result_slot = result_slot = SlotWrapper(
                ui_getter=lambda: craft.result,
                getter=lambda: craft.take_result(),
                setter=lambda item: None,
                slot_type="craft_result"
            )
 
            slots.append((rect, result_slot))

        if self.is_furnace():
            furnaceManager = self.opened_furnace

            width_f, height_f = self.get_furnace_size(furnaceManager)

            result_x = start_x - width_f
            result_y = start_y + height // 2 - height_f // 2 + self.margin

            rect = pygame.Rect(result_x, result_y, self.case_size, self.case_size)

            input_slot = SlotWrapper(
                ui_getter=lambda: furnaceManager.input,
                setter=lambda it: furnaceManager.set_input(it),
                slot_type="furnace_input"
            )

            slots.append((rect, input_slot))

            result_x = start_x - width_f + (self.margin + self.case_size)
            result_y = start_y + height // 2 - height_f // 2 + self.margin

            rect = pygame.Rect(result_x, result_y, self.case_size, self.case_size)

            fuel_slot = SlotWrapper(
                ui_getter=lambda: furnaceManager.fuel,
                setter=lambda it: furnaceManager.set_fuel(it),
                slot_type="furnace_fuel"
            )

            slots.append((rect, fuel_slot))

            result_x = start_x - width_f + (self.margin + self.case_size) * 3
            result_y = start_y + height // 2 - height_f // 2 + self.margin

            rect = pygame.Rect(result_x, result_y, self.case_size, self.case_size)

            output_slot = SlotWrapper(
                ui_getter=lambda: furnaceManager.output,
                setter=lambda it: furnaceManager.set_output(it),
                slot_type="furnace_output"
            )

            slots.append((rect, output_slot))

        return slots

    def highlight_block(self, screen, current_block, cam_rect, player):
        if not current_block:
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
    
    def is_crafting(self):
        return True if self.craft_manager else False
    
    def is_furnace(self):
        return True if self.opened_furnace else False
    
    def open_crafting(self, inv, Crafting_type=Crafting_types.INV):
        self.open_inventory = inv
        
        if Crafting_type in Crafting_types.__dict__.values():
            self.craft_manager = CraftManager(size=Crafting_type, current_inv=inv)

    def open_furnace(self, inv, block):
        self.open_inventory = inv

        if not block.get_component("furnace"):
            block.add_component(FurnaceManager(), "furnace")

        self.opened_furnace = block.get_component("furnace")
            
    def is_open_chest(self):
        return True if self.opened_chest else False

    def open_inv(self, inv, block):
        self.open_inventory = inv

        if not block.get_component("chest"):
            if block.block_property == game_type.BlockProperty.CHEST:
                block.add_component(ChestManager(level=game_type.MaterialTool.WOODEN), "chest")
            elif block.block_property == game_type.BlockProperty.IRON_CHEST:
                block.add_component(ChestManager(level=game_type.MaterialTool.IRON), "chest")

        self.opened_chest = block.get_component("chest")

    def close_inv(self):
        if self.open_inventory:
            if self.is_crafting():
                self.craft_manager.close()
                self.craft_manager = None

            if self.is_open_chest():
                self.opened_chest = None

            if self.controller.is_draging():
                self.controller.drop_outside()
                self.reset_btns()

            if self.is_furnace():
                self.opened_furnace = None

        self.open_inventory = None
        self.craft_manager = None
        self.opened_furnace = None
        self.opened_chest = None