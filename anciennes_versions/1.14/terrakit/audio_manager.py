import pygame
from terrakit import game_property

class AudioType:
    SWEEDEN = "sweeden"
    NONE = "none"
    CLICK = "click"

class AudioManager:
    def __init__(self, directory):
        self.directory = directory
        self.audios = {}
        self._reload()

    def _reload(self):
        try:
            # MUSIC
            self.load_sound(AudioType.SWEEDEN, "Sweden.mp3")

            # EFFECT
            self.load_sound(AudioType.CLICK, "click.ogg")
            
        except Exception as e:
            print(f"Erreur lors du chargement des audios: {e}")
            return False

        print(f"Audios chargées avec succès: {len(self.audios)} audios chargées.")
        return True

    def load_sound(self, audio_type: AudioType, file_path):
        full_path = self.directory + "audio/" + file_path

        try:
            audio = self.click_sound = pygame.mixer.Sound(
                full_path
            )

            self.audios[audio_type] = audio

        except Exception as e:
            print(f"Erreur audio {audio_type} ({file_path}): {e}")

    def get_audio(self, audio_type: AudioType):
        if audio_type in self.audios:
            return self.audios[audio_type]
        return None