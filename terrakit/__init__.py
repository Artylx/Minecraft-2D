from .texture_manager import TextureManager
from . import context

_texture_manager = None
_initialized = False


def init():
    """Initialise Terrakit."""
    global _texture_manager, _initialized

    if _initialized:
        return _texture_manager

    _texture_manager = TextureManager()
    context.texture_manager = _texture_manager
    _texture_manager.load_default_textures()

    from .world import Block
    Block.texture_manager = _texture_manager

    from .inventory import ItemStack
    ItemStack.texture_manager = _texture_manager

    from .entity import Entity
    Entity.texture_manager = _texture_manager

    from .game_type import ItemProperty
    ItemProperty.texture_manager = _texture_manager

    from .interface import MainMenu
    MainMenu.texture_manager = _texture_manager

    _initialized = True
    return _texture_manager


def get_texture_manager():
    if not _initialized:
        raise RuntimeError("Terrakit n'est pas initialisé. Appelez terrakit.init().")
    return _texture_manager