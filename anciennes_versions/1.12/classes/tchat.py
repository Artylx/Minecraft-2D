import pygame
from classes import game_property, game_type
import re
import time
from classes.inventory import ItemStack

COLORS = {
    "&0": (0, 0, 0),
    "&1": (0, 0, 170),
    "&2": (0, 170, 0),
    "&3": (0, 170, 170),
    "&4": (170, 0, 0),
    "&5": (170, 0, 170),
    "&6": (255, 170, 0),
    "&7": (170, 170, 170),
    "&8": (85, 85, 85),
    "&9": (85, 85, 255),
    "&a": (85, 255, 85),
    "&b": (85, 255, 255),
    "&c": (255, 85, 85),
    "&d": (255, 85, 255),
    "&e": (255, 255, 85),
    "&f": (255, 255, 255),
}

def parse_color_codes(text):
    """
    Transforme une chaîne avec des codes &a, &c etc en liste de tuples (texte, couleur)
    """
    segments = []
    last_color = COLORS.get("&f", (255, 255, 255))
    parts = re.split(r'(&.)', text)
    for part in parts:
        if part in COLORS:
            last_color = COLORS[part]
        elif part != "":
            segments.append((part, last_color))
    return segments

class TchatMessage():
    def __init__(self, id_, sender, content):
        self.id_ = id_
        self.sender = sender
        self.content = content
        self.time = time.time()

    def __str__(self):
        if self.sender == "":
            return f"> {self.content}"
        return f"{self.sender}: {self.content}"

class Tchat:
    def __init__(self, screen_size, width=400, margin=game_property.MARGIN_UI_SCREEN, height=160, font_size=18):
        self.messages = []
        self.width = width
        self.height = height
        self.margin = margin

        self.command_manager = CommandManager(self)
        
        self.update_screen_size(screen_size)

        self.font = pygame.font.SysFont("Arial", font_size)
        self.max_lines = height // self.font.get_height()

        self.current = ""
        self.close_tchat()
    
    def send_message(self, sender, content):
        msg_id = len(self.messages) + 1
        msg = TchatMessage(msg_id, sender, content)
        self.messages.append(msg)

        self.command_manager.send_message(msg)
    
    def offset_msg_index_move(self, dy):
        self.offset_msg_index += dy
        if self.offset_msg_index < 0:
            self.offset_msg_index = 0
        elif self.offset_msg_index > len(self.messages) - self.max_lines:
            self.offset_msg_index = len(self.messages) - self.max_lines
    
    def render(self, screen):
        x, y = self.pos
        height = self.height
        if self.oppened:
            height += self.font.get_height() + 5
            y -= self.font.get_height() + 10

        # fond semi-transparent
        chat_surface = pygame.Surface((self.width, height), pygame.SRCALPHA)
        chat_surface.fill((0, 0, 0, 150))
        screen.blit(chat_surface, (x, y))

        # combien de lignes visibles
        self.max_lines = height // self.font.get_height()
        if self.oppened:
            self.max_lines -= 1

        start_index = max(len(self.messages) - self.max_lines - self.offset_msg_index, 0)
        end_index = len(self.messages) - self.offset_msg_index

        visible_messages = self.messages[start_index:end_index]

        for i, msg in enumerate(visible_messages):
            y_pos = y + 5 + i * self.font.get_height()
            x_pos = x + 5

            # sender
            if msg.sender != "":
                sender_segments = parse_color_codes(f"&e{msg.sender}: ")
                for seg_text, seg_color in sender_segments:
                    seg_surface = self.font.render(seg_text, True, seg_color)
                    screen.blit(seg_surface, (x_pos, y_pos))
                    x_pos += seg_surface.get_width()

            # message
            content_segments = parse_color_codes(msg.content)
            for seg_text, seg_color in content_segments:
                seg_surface = self.font.render(seg_text, True, seg_color)
                screen.blit(seg_surface, (x_pos, y_pos))
                x_pos += seg_surface.get_width()

        # barre input si chat ouvert
        if self.oppened:
            input_y = y + height - self.font.get_height() - 5
            pygame.draw.rect(screen, (30,30,30), (x + 5, input_y - 2, self.width - 10, self.font.get_height() + 4))
            text_surface = self.font.render("> " + self.current, True, (255,255,255))
            screen.blit(text_surface, (x + 8, input_y))
    
    def update_screen_size(self, screen_size):
        self.screen_size = screen_size
        self.pos = (self.margin, self.screen_size[1] - self.height - self.margin)

    def key_down(self, event, player):
        if event.key == pygame.K_RETURN:
            if self.current.strip() != "":
                self.send_message(player.name, self.current)
                self.current = ""
                self.close_tchat()

        elif event.key == pygame.K_BACKSPACE:
            self.current = self.current[:-1]

        elif event.key == pygame.K_ESCAPE:
            self.close_tchat()

        elif event.key == pygame.K_UP:
            old_msg = self.get_old_msg(player.name)

            if old_msg:
                self.current = old_msg.content
            else:
                self.current = ""

        else:
            if event.unicode.isprintable():
                self.current += event.unicode

    def get_old_msg(self, sender):
        for msg in reversed(self.messages):
            if msg.sender == sender:
                return msg
        return None
    
    def close_tchat(self):
        self.oppened = False
        self.offset_msg_index = 0
    
class CommandManager:
    game = None

    def __init__(self, tchat):
        self.tchat = tchat

    def send_message(self, tchatMessage):
        content = tchatMessage.content.strip()

        # Vérifie si c'est une commande
        if content.startswith("/"):
            parts = content[1:].split()

            if len(parts) == 0:
                self.send_error_message(tchatMessage.content)
                return
            command = parts[0]

            args = []
            if len(parts) > 1:
                args = parts[1:]

            self.do_command(tchatMessage.sender, command, args, tchatMessage.content)
            return

        print(f"Simple message({str(tchatMessage)})")

    def do_command(self, sender, command, args, content):
        if command == "help":
            self.tchat.send_message("", "Commandes disponibles:")
            self.tchat.send_message("", "- /help")
            self.tchat.send_message("", "- /tp <player> <x> <y>")
            self.tchat.send_message("", "- /give <player> <itemType> <count>")
            self.tchat.send_message("", "- /say <message>")
            self.tchat.send_message("", "- /clear <player>")

        elif command == "tp":
            player = None
            x = 0
            y = 0
            len_args = len(args)
            player_name = ""
            if len_args == 2:
                player = self.game.World.get_player_by_name(sender)
                x = float(args[0])
                y = float(args[1])
            elif len_args == 3:
                player_name = args[0]
                x = float(args[1])
                y = float(args[2])

                player = self.game.World.get_player_by_name(player_name)
            else:
                self.send_error_message_command(content)
                return

            if not player:
                self.send_error_message(f"Le joueur {player_name} n'existe pas")
                return
            
            player.tp(x * game_property.TILE_SIZE, y * game_property.TILE_SIZE)
            self.tchat.send_message("", f"Teleport player {player.name} to {x} {y}")

        elif command == "say":
            message = " ".join(args)
            self.tchat.send_message(sender, message)

        elif command == "give":
            count = 0

            player = None
            item_type = ""
            len_args = len(args)
            if len_args == 1:
                player = self.game.World.get_player_by_name(player_name=sender)
                item_type = args[0]
                count = 1
            elif len_args == 2:
                player_name = args[0]
                player = self.game.World.get_player_by_name(player_name=player_name)
                item_type = args[1]
                count = 1
            elif len_args == 3:
                player_name = args[0]
                player = self.game.World.get_player_by_name(player_name=player_name)
                item_type = args[1]
                count = args[2]

                try:
                    count = int(count)
                except:
                    self.send_error_message_command(content)
                    return
            else:
                self.send_error_message_command(content)
                return
            
            if not player:
                self.send_error_message(f"Le joueur {player_name} n'existe pas")
                return
            
            item = game_type.ItemProperty.REGISTRY.get(item_type.upper())
            
            if not item:
                self.send_error_message(f"L'item {item_type} n'existe pas")
                return
            
            print("Item " + str(item))
            for i in range(count):
                player.inventory.insert(ItemStack(item, 1))
            self.tchat.send_message("", f"{count} Item {item.item_name} give to player {player.name}")

        elif command == "clear":
            player = None
            len_args = len(args)
            if len_args == 0:
                player = self.game.World.get_player_by_name(sender)
            elif len_args == 1:
                player_name = args[0]
                player = self.game.World.get_player_by_name(player_name)
            else:
                self.send_error_message_command(content)
                return
            
            if not player:
                if len_args == 0:
                    self.send_error_message(f"Le joueur {sender} n'existe pas")
                else:
                    self.send_error_message(f"Le joueur {player_name} n'existe pas")
                return
            
            player.inventory.clear()

        else:
            self.send_error_message_command(content)
            return
        
    def send_error_message_command(self, content):
        self.tchat.send_message("", f"&4Erreur: {content} <---[HERE]")
    
    def send_error_message(self, content):
        self.tchat.send_message("", f"&4Erreur, {content}")