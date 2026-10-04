import os
import random
import pygame
from terrakit import game_property

class AudioType:
    SWEEDEN = "sweeden"
    NONE = "none"
    CLICK = "click"
    DREITON = "dreiton"
    ARIA_MATH = "aria_math"
    MINECRAFT = "minecraft"

class AudioManager:
    MUSIC_FILES = {
        AudioType.SWEEDEN: "Sweden.mp3",
        AudioType.DREITON: "Dreiton.mp3",
        AudioType.ARIA_MATH: "Aria Math.mp3",
        AudioType.MINECRAFT: "Minecraft.mp3",
    }
    EFFECT_FILES = {
        AudioType.CLICK: "click.ogg",
    }

    def __init__(self, directory):
        self.directory = directory
        self.audios = {}            # effets (pygame.mixer.Sound)

        self.music_volume = 0.5
        self.effect_volume = 1.0

        self.playlist = []          # pistes restantes avant un nouveau mélange
        self.current_track = None
        self.music_playing = False  # True entre play_music() et stop_music()

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self._reload()
        pygame.mixer.music.set_volume(self.music_volume)

    # ---------- chargement ----------
    def _path(self, file_name):
        return os.path.join(self.directory, "audio", file_name)

    def _reload(self):
        for audio_type, file_name in self.EFFECT_FILES.items():
            self.load_sound(audio_type, file_name)
        print(f"Audios chargés : {len(self.audios)} effets, {len(self.MUSIC_FILES)} musiques.")

    def load_sound(self, audio_type, file_name):
        try:
            sound = pygame.mixer.Sound(self._path(file_name))
            sound.set_volume(self.effect_volume)
            self.audios[audio_type] = sound
        except Exception as e:
            print(f"Erreur audio {audio_type} ({file_name}): {e}")

    def get_audio(self, audio_type):
        return self.audios.get(audio_type)

    # ---------- effets ----------
    def play_effect(self, audio_type):
        sound = self.audios.get(audio_type)
        if sound:
            sound.play()

    def set_effect_volume(self, volume):
        self.effect_volume = max(0.0, min(1.0, volume))
        for sound in self.audios.values():
            sound.set_volume(self.effect_volume)

    # ---------- musique ----------
    def _refill_playlist(self):
        tracks = list(self.MUSIC_FILES.keys())
        random.shuffle(tracks)
        # évite de rejouer deux fois de suite la même piste entre deux mélanges
        if len(tracks) > 1 and tracks[0] == self.current_track:
            tracks[0], tracks[-1] = tracks[-1], tracks[0]
        self.playlist = tracks

    def _play_next(self):
        if not self.playlist:
            self._refill_playlist()

        # essaie les pistes jusqu'à en trouver une qui se charge
        while self.playlist:
            track = self.playlist.pop(0)
            try:
                pygame.mixer.music.load(self._path(self.MUSIC_FILES[track]))
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play()
                self.current_track = track
                return True
            except Exception as e:
                print(f"Erreur musique {track}: {e}")
        return False

    def play_music(self):
        """Lance la playlist aléatoire (sans effet si elle joue déjà)."""
        if self.music_playing:
            return
        self.music_playing = True
        if not self._play_next():
            self.music_playing = False

    def stop_music(self):
        self.music_playing = False
        pygame.mixer.music.stop()

    def update(self):
        """À appeler à chaque frame : enchaîne la piste suivante quand l'actuelle finit."""
        if self.music_playing and not pygame.mixer.music.get_busy():
            if not self._play_next():
                self.music_playing = False

    def set_music_volume(self, volume):
        """volume entre 0.0 et 1.0"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)