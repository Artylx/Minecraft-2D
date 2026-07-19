# CONTEXT
from terrakit.resource_pack import ResourcePack

resource_pack = None

def get_resource_pack() -> ResourcePack:
    if not resource_pack:
        raise RuntimeError("Terrakit n'est pas initialisé. Appelez terrakit.init().")
    return resource_pack