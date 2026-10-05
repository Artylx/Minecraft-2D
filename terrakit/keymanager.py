import json
from pathlib import Path
import pygame


class KeyCollection:
    ATTACK_BREAK = "attack_break"
    JUMP = "jump"
    LEFT = "left"
    RIGHT = "right"
    PLACE_USE = "place_use"
    SPEAK = "speak"
    SNEAK = "sneak"

    SLOT_1 = "slot_1"
    SLOT_2 = "slot_2"
    SLOT_3 = "slot_3"
    SLOT_4 = "slot_4"
    SLOT_5 = "slot_5"
    SLOT_6 = "slot_6"

    DROP_ITEM = "drop_item"
    TCHAT = "tchat"
    INVENTORY = "inventory"


def event_mouse_get(button):
        return f"mouse{button}"


class KeyManager:
    DEFAULT_KEYS = {
        KeyCollection.ATTACK_BREAK: event_mouse_get(1),
        KeyCollection.JUMP: pygame.K_SPACE,
        KeyCollection.LEFT: pygame.K_q,
        KeyCollection.RIGHT: pygame.K_d,
        KeyCollection.SNEAK: pygame.K_LCTRL,
        KeyCollection.PLACE_USE: event_mouse_get(3),
        KeyCollection.SPEAK: pygame.K_e,

        KeyCollection.SLOT_1: pygame.K_1,
        KeyCollection.SLOT_2: pygame.K_2,
        KeyCollection.SLOT_3: pygame.K_3,
        KeyCollection.SLOT_4: pygame.K_4,
        KeyCollection.SLOT_5: pygame.K_5,
        KeyCollection.SLOT_6: pygame.K_6,

        KeyCollection.DROP_ITEM: pygame.K_a,
        KeyCollection.TCHAT: pygame.K_t,
        KeyCollection.INVENTORY: pygame.K_e,
    }

    def __init__(self, filename="keybindings.json"):
        self.filename = Path(filename)
        self.keybindings = self.DEFAULT_KEYS.copy()
        self._dirty = False
        if not self._load():
            self.save()

    def _load(self):
        if not self.filename.exists():
            self._dirty = True
            return False

        try:
            with self.filename.open("r", encoding="utf-8") as f:
                data = json.load(f)

            self.keybindings.update(data)
            print("Raccourcis chargées avec succès.")
            return True

        except (json.JSONDecodeError, OSError):
            print("Impossible de charger les raccourcis.")
            self._dirty = True
            return False

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