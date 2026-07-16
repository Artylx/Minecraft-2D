import time
import threading
import pygame
from classes import world, game_property
from classes.texture_manager import TextureManager
import socket
import json
import queue
import traceback

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
        self.debug_values = {}

        self.player_to_client = {}
        self.clients = {}
        self.send_queues = {}

        self.start_server()

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
                    print("Client déconnecté:", self.clients[client]["addr"])
                    break  # 👈 client fermé proprement

                buffer += data.decode()

                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)

                    packet = json.loads(msg)
                    self.handle_packet(client, packet)

                self.send_current_snapshot(client)

            except Exception as e:
                print("Client crash / disconnect:", self.clients[client]["addr"])
                print("Error:", e)
                traceback.print_exc()
                break

        self.disconnect_client(client)

    def send_current_snapshot(self, client):
        pass

    def handle_packet(self, client, packet):
        action = packet.get("action")

        self.clients[client]["last_seen"] = time.time()

        if action == "join":
            name = packet.get("player_name")

            player = self.normal_world.player_join(name)
            self.clients[client]["player_name"] = name
            self.clients[client]["entity_id"] = player.get_uuid()
            self.clients[client]["last_input"] = {}

            self.player_to_client[name] = client

            self.log(f"{name} a rejoint le serveur")

            print("JOIN RECU")

            world_data = self.build_world_init()

            print("ENVOI WORLD_INIT")

            try:
                client.sendall((json.dumps(world_data) + "\n").encode())
            except:
                pass

            threading.Thread(target=self.sender_loop, args=(client,), daemon=True).start()

        elif action == "input":
            print(packet)

            right = packet.get("right")
            left = packet.get("left")
            up = packet.get("up")

            if right or left or up:
                self.log("Move for player " + self.clients[client]["player_name"] + ": " + str(left) + ", " + str(right) + ", " + str(up))

                player = self.normal_world.get_player_by_name(self.clients[client]["player_name"])

                if player:
                    if right:
                        player.add_velocity(1, 0)
                    elif left:
                        player.add_velocity(-1, 0)

                    if up and player.on_ground:
                        player.jump(game_property.JUMP_VELOCITY + game_property.JUMP_VELOCITY * 0.1)

        elif action == "disconnect":
            self.disconnect_client(client)

    def build_snapshot(self):
        return {
            "type": "snapshot",
            "timestamp": time.time(),
            "entitys": [
                e.to_json()
                for e in self.normal_world.get_entities()
            ]
        }
    
    def build_world_init(self):
        return {
            "type": "world_init",
            "world_name": "Normal World",
            "world": self.normal_world.get_json(),
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

    def tick(self, dt):
        """Logique serveur exécutée 20 fois par seconde."""
        for client, data in self.clients.items():
            entity = data.get("entity")
            inputs = data.get("last_input")

            if entity and inputs:
                if inputs.get("left"):
                    entity.add_velocity(-1, 0)

                if inputs.get("right"):
                    entity.add_velocity(1, 0)

                if inputs.get("jump"):
                    if entity.on_ground:
                        entity.jump()

        self.normal_world.update(dt)

        snapshot = self.build_snapshot()

        packet = (
            json.dumps(snapshot) + "\n"
        ).encode()

        dead_clients = []

        for client in self.clients:
            try:
                self.send_queues[client].put(packet)
            except:
                dead_clients.append(client)

        for client in dead_clients:
            self.disconnect_client(client)


    def sender_loop(self, client):
        while self.running:
            packet = self.send_queues[client].get()

            try:
                client.sendall(packet)
            except:
                break
            

    def disconnect_client(self, client):
        info = self.clients.get(client)

        if info:
            player_name = info.get("player_name")

            if player_name:
                self.normal_world.player_quit(player_name)
            self.log(f"{player_name} disconnected")

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
                self.tick(tick_time)
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

            client = self.player_to_client.get(player_name)

            if not client:
                self.log(f"[SERVER] Joueur '{player_name}' introuvable.")
                return

            try:
                client.sendall((json.dumps({
                    "type": "kick",
                    "reason": "Vous avez été expulsé du serveur."
                }) + "\n").encode())
            except:
                pass

            self.disconnect_client(client)

            self.normal_world.player_quit(player_name)
            self.player_to_client.pop(player_name, None)

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

        self.disconnected = False

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((ip, port))
        except Exception as e:
            print(f"Erreur de connexion au serveur : {e}")
            self.disconnected = True
        
        self.socket.setblocking(False)

        self.buffer = ""

    def send_inputs(self, data):
        try:
            msg = json.dumps(data).encode()
            self.socket.sendall(msg + b"\n")
        except:
            pass

    def send_join(self, player_name):
        data = {
            "action": "join",
            "player_name": player_name
        }

        self.socket.sendall(
            (json.dumps(data) + "\n").encode()
        )

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
            try:
                data = self.socket.recv(4096)
            except BlockingIOError:
                return None

            if not data:
                print("SERVEUR FERME")
                return None
            
            self.buffer += data.decode()
            while "\n" in self.buffer:
                msg, self.buffer = self.buffer.split("\n", 1)

                return json.loads(msg)

        except Exception as e:
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
        server = Server(name="Tera server", world_path="Noa")
        server.run_gui()
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        import traceback
        traceback.print_exc()