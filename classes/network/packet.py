import json
import struct

PACKET_REGISTRY = {}

def register_packet(cls):
    PACKET_REGISTRY[cls.packet_id] = cls
    return cls

class Packet:
    packet_id = "base"

    def __init__(self, **data):
        self.data = data

    def to_dict(self):
        return {
            "packet_id": self.packet_id,
            "data": self.data
        }

    def encode(self):
        json_data = json.dumps(self.to_dict()).encode("utf-8")

        # HEADER 4 bytes = taille packet
        header = struct.pack("!I", len(json_data))

        return header + json_data

    @staticmethod
    def decode(data):
        payload = json.loads(data.decode("utf-8"))

        return payload