from terrakit.texture_manager import TextureManager
from terrakit.audio_manager import AudioManager

class ResourcePack:
    def __init__(self):
        self.resource_pack = ""
        self.init_directory = "resource_pack/"
        
        self.set_resource_pack("Default")

    def set_resource_pack(self, name):
        self.resource_pack = name + "/"
        self._reload()

    def get_path(self):
        return self.init_directory + self.resource_pack

    def _reload(self):
        self._texture_manager = TextureManager(self.get_path())
        self._audio_manager = AudioManager(self.get_path())

    def audio_manager(self):
        return self._audio_manager
    
    def texture_manager(self):
        return self._texture_manager