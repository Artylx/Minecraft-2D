import json
from pathlib import Path
import pygame


class KeyCollection:
    ATTACK = "attack"
    JUMP = "jump"
    LEFT = "left"
    RIGHT = "right"
    PLACE = "place"
    USE = "use"


def event_mouse_get(button):
        return f"mouse{button}"


class KeyManager:
    DEFAULT_KEYS = {
        KeyCollection.ATTACK: event_mouse_get(3),
        KeyCollection.JUMP: pygame.K_SPACE,
        KeyCollection.LEFT: pygame.K_q,
        KeyCollection.RIGHT: pygame.K_d,
        KeyCollection.PLACE: event_mouse_get(1)
    }

    def __init__(self, filename="keybindings.json"):
        self.filename = Path(filename)
        self.keybindings = self.DEFAULT_KEYS.copy()
        self._dirty = False
        self._load()

    def _load(self):
        if not self.filename.exists():
            self._dirty = True
            return

        try:
            with self.filename.open("r", encoding="utf-8") as f:
                data = json.load(f)

            self.keybindings.update(data)

        except (json.JSONDecodeError, OSError):
            print("Impossible de charger les raccourcis.")
            self._dirty = True

    def save(self):
        if not self._dirty:
            return

        with self.filename.open("w", encoding="utf-8") as f:
            json.dump(self.keybindings, f, indent=4)

        self._dirty = False

        print(f"Raccourcis sauvegardés.")

    def get(self, action):
        return self.keybindings.get(action)

    def set(self, action, key):
        if self.keybindings.get(action) == key:
            return

        self.keybindings[action] = key
        self._dirty = True

        print(f"Raccourci pour '{action}' mis à jour vers '{pygame.key.name(key)}'")