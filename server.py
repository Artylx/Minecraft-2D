import time
import threading
import pygame
from classes import world
from classes.texture_manager import TextureManager
import socket
import json
import queue

class Server:
    TPS = 20

    def __init__(self, name, world_path, host="localhost", port=12345, max_players=5):
        self.name = name
        self.world_path = world_path
        self.host = host
        self.port = port
        self.max_players = max_players
        self.normal_world = None

        self.running = False

        pygame.init()

        load_texture()

        self.screen = pygame.display.set_mode((1280, 720))
        self.font = pygame.font.SysFont("consolas", 22)

        self.logs = []
        self.terminal_lines = []
        self.command = ""
        self.send_queue = queue.Queue()
        self.debug_values = {}

        self.start_server()

    def sender_loop(self, client):
        while self.running:
            try:
                msg = self.send_queues[client].get()
                client.sendall(msg)
            except:
                break

    def log(self, text):
        self.logs.append(text)

        if len(self.logs) > 100:
            self.logs.pop(0)

    def on_world_loaded(self, text, value):
        if value >= 100:
            print(f"Le monde '{self.normal_world.name}' a été chargé avec succès.")
            timer = self.debug_values.get("time", None)

            if timer:
                elapsed_time = time.time() - timer
                print(f"Temps de chargement: {elapsed_time:.2f} secondes")

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            self.clients = {}

            threading.Thread(target=self.accept_loop, daemon=True).start()

    def accept_loop(self):
        while self.running:
            client, addr = self.server_socket.accept()
            print("Client connecté:", addr)

            self.clients[client] = {
                "addr": addr,
                "player": None,
            }

            threading.Thread(
                target=self.client_loop,
                args=(client,),
                daemon=True
            ).start()

    def client_loop(self, client):
        buffer = ""

        while self.running:
            try:
                data = client.recv(4096)

                if not data:
                    break  # 👈 client fermé proprement

                buffer += data.decode()

                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)

                    packet = json.loads(msg)
                    self.handle_packet(client, packet)

            except:
                break  # 👈 crash / disconnect

        self.disconnect_client(client)

    def handle_packet(self, client, packet):
        action = packet.get("action")

        self.clients[client]["last_seen"] = time.time()

        if action == "join":
            name = packet.get("player_name")

            player = self.normal_world.player_join(name)
            self.clients[client] = {
                "player_name": name,
                "entity_id": player.get_uuid(),
                "last_input": {}
            }

            self.log(f"{name} a rejoint le serveur")

            # 👇 ENVOI DU WORLD INITIAL
            world_data = self.build_world_snapshot()

            try:
                client.sendall((json.dumps({
                    "type": "world_init",
                    "world": world_data
                }) + "\n").encode())
            except:
                pass

        elif action == "input":
            # exemple futur
            pass

        elif action == "disconnect":
            player = self.clients.get(client, {}).get("player")
            if player:
                self.log(f"{player} a quitté le serveur")
            self.clients.pop(client, None)

    def build_world_snapshot(self):
        data = {
            "seed": self.normal_world.seed,
            "entitys": []
        }

        # blocs (version simple brute)
        blocks = []

        for block in self.normal_world.modified_blocks_runtime:
            blocks.append(block.to_json())

        for block in self.normal_world.saved_modified_blocks:
            blocks.append(block.to_json())

        data["modified_blocks"] = blocks

        # entities existants
        for e in self.normal_world.get_entities():
            data["entitys"].append(e.to_json())

        return data
    
    def build_world_init(self):
        return {
            "type": "world_init",
            "seed": self.normal_world.seed,
            "world_size": self.normal_world.size,
        }
    
    def send_chunk(self, client, chunk):
        data = {
            "type": "chunk",
            "x": chunk.x,
            "y": chunk.y
        }

        client.sendall((json.dumps(data) + "\n").encode())

    def start_server(self):
        print(
            f"Démarrage du serveur '{self.name}' "
            f"sur {self.host}:{self.port}"
        )

        self.debug_values = {
            "time": time.time(),
        }

        json = world.load_world_json(self.world_path)

        if json is None:
            print(f"Impossible de charger le monde depuis '{self.world_path}'.")
            return

        self.normal_world = world.WorldSolo(
            name="Normal World",
            json_data=json,
            callback_loading=self.on_world_loaded
        )

        self.running = True

        threading.Thread(
            target=self.run,
            daemon=True
        ).start()

    def tick(self):
        """Logique serveur exécutée 20 fois par seconde."""
        pass

        self.normal_world.update(0.02)

        for client, data in self.clients.items():
            player = data.get("entity")
            if not player:
                continue

            state = {
                "x": player.rect.x,
                "y": player.rect.y,
            }

            try:
                client.sendall((json.dumps(state) + "\n").encode())
            except:
                pass

        for client, data in self.clients.items():
            entity = data.get("entity")
            inputs = data.get("last_input")

            if entity and inputs:
                if inputs.get("left"):
                    entity.add_velocity(-1, 0)

                if inputs.get("right"):
                    entity.add_velocity(1, 0)

                if inputs.get("jump"):
                    entity.jump()

    def disconnect_client(self, client):
        info = self.clients.get(client)

        if info:
            player = info.get("entity")

            if player:
                self.normal_world.remove_entity(player)

            name = info.get("player")
            self.log(f"{name} disconnected")

        self.clients.pop(client, None)

        try:
            client.close()
        except:
            pass

    def run(self):
        tick_time = 1 / self.TPS

        next_tick = time.perf_counter()

        self.current_tps = 0
        self.tick_counter = 0
        self.last_tps_update = time.time()

        while self.running:

            now = time.perf_counter()

            while now >= next_tick:
                self.tick()
                self.tick_counter += 1
                next_tick += tick_time

            if time.time() - self.last_tps_update >= 1:
                self.current_tps = self.tick_counter
                self.tick_counter = 0
                self.last_tps_update = time.time()

            time.sleep(0.001)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.execute_command(self.command)
                self.command = ""
            elif event.key == pygame.K_BACKSPACE:
                self.command = self.command[:-1]
            else:
                char = event.unicode
                if char.isprintable():
                    self.command += char

    def update_camera(self):
        self.camera.centerx = self.player.rect.centerx
        self.camera.centery = self.player.rect.centery

    def run_gui(self):
        clock = pygame.time.Clock()

        font_title = pygame.font.SysFont("consolas", 26, bold=True)
        font = pygame.font.SysFont("consolas", 20)
        font_small = pygame.font.SysFont("consolas", 18)

        while self.running:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop()

                elif event.type == pygame.WINDOWLEAVE:
                    pass

                elif event.type == pygame.WINDOWFOCUSLOST:
                    pass

                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

                else:
                    self.handle_input(event)

            self.screen.fill((18, 18, 20))

            # =========================
            # TOP BAR
            # =========================
            pygame.draw.rect(self.screen, (30, 30, 35), (0, 0, 1280, 50))

            tps = getattr(self, "current_tps", 0)
            players = len(self.normal_world.get_players())
            entities = len(self.normal_world.entitys)

            top_text = (
                f"{self.name}  |  {self.host}:{self.port}  |  "
                f"TPS: {tps:.1f}  |  Players: {players}/{self.max_players}  |  Entities: {entities}"
            )

            self.screen.blit(font.render(top_text, True, (220, 220, 220)), (15, 15))

            # =========================
            # LEFT PANEL (PLAYERS)
            # =========================
            left = pygame.Rect(10, 60, 300, 650)
            pygame.draw.rect(self.screen, (25, 25, 28), left, border_radius=6)

            self.screen.blit(font_title.render("PLAYERS", True, (255, 255, 255)), (25, 70))

            y = 110
            for player in self.normal_world.get_players():
                pygame.draw.circle(self.screen, (80, 220, 120), (25, y + 8), 5)

                self.screen.blit(
                    font.render(player.name, True, (230, 230, 230)),
                    (40, y)
                )
                y += 28

            # =========================
            # RIGHT PANEL (LOGS)
            # =========================
            right = pygame.Rect(320, 60, 950, 580)
            pygame.draw.rect(self.screen, (25, 25, 28), right, border_radius=6)

            self.screen.blit(font_title.render("SERVER LOGS", True, (255, 255, 255)), (335, 70))

            y = 110
            max_logs = 22

            for line in self.logs[-max_logs:]:
                color = (200, 200, 200)

                if "error" in line.lower():
                    color = (255, 90, 90)
                elif "join" in line.lower():
                    color = (90, 255, 140)

                self.screen.blit(font_small.render(line, True, color), (335, y))
                y += 22

            # =========================
            # COMMAND BAR
            # =========================
            cmd_rect = pygame.Rect(320, 664, 950, 45)
            pygame.draw.rect(self.screen, (35, 35, 40), cmd_rect, border_radius=6)

            self.screen.blit(
                font.render("> " + self.command, True, (255, 255, 255)),
                (335, 676)
            )

            # cursor simple
            if int(time.time() * 2) % 2 == 0:
                cursor_x = 335 + font.size("> " + self.command)[0]
                pygame.draw.line(
                    self.screen,
                    (255, 255, 255),
                    (cursor_x, 676),
                    (cursor_x, 696),
                    2
                )

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def execute_command(self, cmd):

        self.log("> " + cmd)

        args = cmd.split()

        if not args:
            return

        if args[0] == "stop":
            self.stop()

        elif args[0] == "list":
            players = self.normal_world.get_players()

            self.log(
                f"{len(players)} joueur(s)"
            )

        elif args[0] == "kick":
            if len(args) < 2:
                self.log("[SERVER] Usage: kick <player_name>")
                return

            player_name = args[1]
            player = self.normal_world.get_player_by_name(player_name)

            if not player:
                self.log(f"[SERVER] Joueur '{player_name}' introuvable.")
                return

            self.log(f"[SERVER] Joueur '{player_name}' expulsé du serveur.")

        elif args[0] == "say":
            self.log(
                "[SERVER] " + " ".join(args[1:])
            )

    def stop(self):
        self.running = False



class ServerConnection:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))

        self.buffer = ""

    def send_inputs(self, data):
        try:
            msg = json.dumps(data).encode()
            self.socket.sendall(msg + b"\n")
        except:
            pass

    def send_join(self, player_name):
        try:
            data = {
                "action": "join",
                "player_name": player_name
            }
            msg = json.dumps(data).encode()
            self.socket.sendall(msg + b"\n")
        except:
            pass

    def send_leave(self, player_name):
        try:
            data = {
                "action": "disconnect",
                "player_name": player_name
            }
            msg = json.dumps(data).encode()
            self.socket.sendall(msg + b"\n")
        except:
            pass

    def get_state(self):
        try:
            data = self.socket.recv(4096)
            self.buffer += data.decode()

            while "\n" in self.buffer:
                msg, self.buffer = self.buffer.split("\n", 1)
                state = json.loads(msg)

            if not state:
                return None

            return json.loads(state)
        except:
            return None

def load_texture():
    texture_manager = TextureManager()

    from classes.world import Block
    Block.texture_manager = texture_manager

    from classes.inventory import ItemStack
    ItemStack.texture_manager = texture_manager

    from classes.entity import Entity
    Entity.texture_manager = texture_manager

    from classes.game_type import ItemProperty
    ItemProperty.texture_manager = texture_manager

    from classes.interface import MainMenu
    MainMenu.texture_manager = texture_manager

if __name__ == "__main__":

    try:
        server = Server(name="Mon serveur", world_path="Noa")
        server.run_gui()
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        import traceback
        traceback.print_exc()