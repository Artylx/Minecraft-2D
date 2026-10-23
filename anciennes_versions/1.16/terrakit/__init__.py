from .texture_manager import TextureManager
from . import context
from .resource_pack import ResourcePack

_initialized = False

def init():
    """Initialise Terrakit."""
    global _initialized

    context.resource_pack = ResourcePack()
    _initialized = True