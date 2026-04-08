import pygame
from classes import game_property

class UI:
    def __init__(self, screen_size, inventory, tchat):
        self.inventory = inventory
        self.tchat = tchat

        self.dragged_item = None
        self.dragged_index = None
        self.update_screen_size(screen_size)
        
        self.close_inv()

        self.margin = 15
        self.case_size = game_property.INVENTORY_SIZE_CASE + self.margin

    def update_screen_size(self, screen_size):
        self.screen_size = screen_size
        self.cam_rect = pygame.Rect(-self.screen_size[0] // 2 + game_property.CHUNK_WIDTH * game_property.TILE_SIZE // 2, 0, self.screen_size[0], self.screen_size[1])
        self.tchat.update_screen_size(screen_size)
        self.inventory.update_screen_size(screen_size)

    def update_pos_cam_rect(self, pos):
        self.cam_rect.x = pos[0]
        self.cam_rect.y = pos[1]

    def render(self, screen, player):
        self.update(player.inventory)

        if not self.is_open_inv():
            self.tchat.render(screen)

            self.render_hotbar(screen, player.inventory)
        else:
            self.render_inv(screen, self.open_inventory)

    def key_down(self, event):
        if event.key == pygame.K_ESCAPE:
            self.close_inv()

    def update(self, inv):
        if not self.is_open_inv():
            mouse_pos = pygame.mouse.get_pos()
            case_size = game_property.INVENTORY_SIZE_CASE
            margin = 15

            height = case_size + margin * 2
            width = margin + (case_size + margin) * inv.case_number

            start_x = self.screen_size[0] // 2 - width // 2
            start_y = self.screen_size[1] - game_property.MARGIN_UI_SCREEN - height

            for i in range(min(len(inv.items), inv.case_number)):
                col = i % inv.case_number
                
                x = start_x + col * (case_size + margin) + margin
                y = start_y + margin

                rect = pygame.Rect(x, y, case_size, case_size)
                
                if rect.collidepoint(mouse_pos):
                    inv.visible_name = i
                    return
            inv.visible_name = None
        
    def mouse_down(self, button):
        if not self.is_open_inv() or button != 1:
            return
        
        mouse_pos = pygame.mouse.get_pos()
        cols = self.open_inventory.case_number

        width = cols * (self.case_size + self.margin) + self.margin
        rows = (self.open_inventory.size + cols - 1) // cols
        height = rows * (self.case_size + self.margin) + self.margin

        start_x = self.screen_size[0] // 2 - width // 2
        start_y = self.screen_size[1] // 2 - height // 2

        # Vérifier si on clique sur un item
        for index, item in self.open_inventory.items.items():
            row = index // cols
            col = index % cols
            x = start_x + self.margin + col * (self.case_size + self.margin)
            y = start_y + self.margin + row * (self.case_size + self.margin)
            rect = pygame.Rect(x, y, self.case_size, self.case_size)

            if rect.collidepoint(mouse_pos) and item:
                self.dragged_item = item
                self.dragged_index = index
                break
        print(f"{self.dragged_item}")

    def mouse_up(self, button):
        if not self.is_open_inv() or button != 1 or not self.dragged_item:
            return
        else:
            mouse_pos = pygame.mouse.get_pos()
            cols = self.open_inventory.case_number

            width = cols * (self.case_size + self.margin) + self.margin
            rows = (self.open_inventory.size + cols - 1) // cols
            height = rows * (self.case_size + self.margin) + self.margin

            start_x = self.screen_size[0] // 2 - width // 2
            start_y = self.screen_size[1] // 2 - height // 2

            # Vérifier sur quelle case on relâche
            for index in range(self.open_inventory.size):
                row = index // cols
                col = index % cols
                x = start_x + self.margin + col * (self.case_size + self.margin) 
                y = start_y + self.margin + row * (self.case_size + self.margin)
                rect = pygame.Rect(x, y, self.case_size, self.case_size)

                if rect.collidepoint(mouse_pos):
                    # swap si case occupée ou move si vide
                    self.open_inventory.items[self.dragged_index], self.open_inventory.items[index] = self.open_inventory.items.get(index), self.dragged_item
                    break

            self.dragged_item = None
            self.dragged_index = None

    def render_inv(self, screen, inv):
        cols = inv.case_number

        font = pygame.font.SysFont("Arial", 26)

        # texte
        text_surface = font.render(inv.title, True, (255, 255, 255))
        text_rect = text_surface.get_rect()

        # Taille totale du fond
        width = cols * (self.case_size + self.margin) + self.margin
        rows = (inv.size + cols - 1) // cols
        height = rows * (self.case_size + self.margin) + self.margin

        # espace pour le titre
        title_space = text_rect.height + 10

        start_x = self.screen_size[0] // 2 - width // 2
        start_y = self.screen_size[1] // 2 - (height + title_space) // 2

        # centrer le texte
        text_rect.centerx = self.screen_size[0] // 2
        text_rect.y = start_y

        screen.blit(text_surface, text_rect)

        # fond inventaire
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 180))
        screen.blit(surface, (start_x, start_y + title_space))

        for index, item in inv.items.items():
            row = index // cols
            col = index % cols

            x = start_x + self.margin + col * (self.case_size + self.margin)
            y = start_y + title_space + self.margin + row * (self.case_size + self.margin)

            rect = pygame.Rect(x, y, self.case_size, self.case_size)

            pygame.draw.rect(screen, (60, 60, 60), rect)
            pygame.draw.rect(screen, (120, 120, 120), rect, 2)

            if item:
                item.render(
                    screen,
                    (
                        x + (self.case_size - game_property.INVENTORY_SIZE_CASE) // 2,
                        y + (self.case_size - game_property.INVENTORY_SIZE_CASE) // 2
                    )
                )

        if self.dragged_item:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.dragged_item.render(
                screen,
                (mouse_x - self.case_size // 2, mouse_y - self.case_size // 2)
            )

    def highlight_block(self, screen, current_block, cam_rect):
        if not current_block:
            print("Erreur current_block is None")
            return
        
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

        height = case_size + margin * 2
        width = margin + (case_size + margin) * inv.case_number

        chat_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        chat_surface.fill((0, 0, 0, 150))

        start_x = self.screen_size[0] // 2 - width // 2
        start_y = self.screen_size[1] - game_property.MARGIN_UI_SCREEN - height
        screen.blit(chat_surface, (start_x, start_y))

        font = pygame.font.SysFont("Arial", 16)

        for i in range(inv.case_number):
            item = inv.items.get(i, None)

            col = i % inv.case_number

            x = start_x + col * (case_size + margin) + margin
            y = start_y + margin

            rect = pygame.Rect(x, y, case_size, case_size)

            # Rendu de l'item après le fond
            if item != None:
                item.render(screen, (x, y))
            else:
                pygame.draw.rect(screen, (60, 60, 60), rect)
                pygame.draw.rect(screen, (120, 120, 120), rect, 2)

            if i == inv.selected_index:
                pygame.draw.rect(screen, (255, 255, 255), rect, width=2)

            # souris sur la case
            if i == inv.visible_name and item:
                item_name = item.item_type.item_name.capitalize()
                text = font.render(item_name, True, (255, 255, 255))
                text_rect = text.get_rect()
                # position au dessus de l'item
                text_rect.midbottom = (rect.centerx, rect.top - 5)
                # fond
                bg = pygame.Surface((text_rect.width + 10, text_rect.height + 6), pygame.SRCALPHA)
                bg.fill((0, 0, 0, 200))
                screen.blit(bg, (text_rect.x - 5, text_rect.y - 3))
                screen.blit(text, text_rect)
    
    def is_open_inv(self):
        if self.open_inventory:
            return True
        return False
    
    def open_inv(self, inv):
        self.open_inventory = inv
    
    def close_inv(self):
        self.open_inventory = None