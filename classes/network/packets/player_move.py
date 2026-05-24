from packet import Packet, register_packet

@register_packet
class PlayerMovePacket(Packet):
    packet_id = "player_move"

    def __init__(self, x, y):
        super().__init__(x=x, y=y)