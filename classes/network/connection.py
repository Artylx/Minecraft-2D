import socket
import struct
import packet as Packet

class Connection:
    def __init__(self, sock):
        self.sock = sock

        self.recv_buffer = b""

    def send_packet(self, packet):
        self.sock.sendall(packet.encode())

    def receive_packets(self):
        packets = []

        try:
            chunk = self.sock.recv(4096)

            if not chunk:
                return None

            self.recv_buffer += chunk

            while True:

                # pas assez pour le header
                if len(self.recv_buffer) < 4:
                    break

                # taille packet
                packet_size = struct.unpack(
                    "!I",
                    self.recv_buffer[:4]
                )[0]

                # packet incomplet
                if len(self.recv_buffer) < 4 + packet_size:
                    break

                # extraction packet
                raw_packet = self.recv_buffer[4:4 + packet_size]

                self.recv_buffer = self.recv_buffer[4 + packet_size:]

                packets.append(Packet.decode(raw_packet))

        except ConnectionResetError:
            return None

        return packets