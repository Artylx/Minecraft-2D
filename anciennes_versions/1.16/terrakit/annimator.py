import json
import os
import pygame
from enum import Enum

ANIMATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "animations")


class AnimationSet(Enum):
    """Quel fichier JSON charger pour une entité."""
    NONE = None
    PLAYER = "player.json"
    FOX = "fox.json"
    ZOMBIE = "zombie.json"


class Anim(str, Enum):
    """Noms des animations (clés du JSON)."""
    IDLE = "idle"
    WALK = "walk"
    SHOOT = "shoot"
    ATTACK = "attack"
    PLACE = "place"
    BREAK = "break"


def _key(name):
    return name.value if isinstance(name, Enum) else name

EASINGS = {
    "linear": lambda x: x,
    "ease_in": lambda x: x * x,
    "ease_out": lambda x: 1 - (1 - x) ** 2,
    "ease_in_out": lambda x: x * x * (3 - 2 * x),
}


def _lerp(a, b, k):
    if isinstance(a, (list, tuple)):
        return [x + (y - x) * k for x, y in zip(a, b)]
    return a + (b - a) * k


def _sample(keys, t):
    if t <= keys[0]["t"]:
        return keys[0]["v"]
    for a, b in zip(keys, keys[1:]):
        if t <= b["t"]:
            k = (t - a["t"]) / (b["t"] - a["t"])
            k = EASINGS[a.get("ease", "linear")](k)
            return _lerp(a["v"], b["v"], k)
    return keys[-1]["v"]


class AnimationClip:
    def __init__(self, name, data):
        self.name = name
        self.duration = data["duration"]
        self.loop = data.get("loop", True)
        self.tracks = {
            part: {prop: sorted(keys, key=lambda k: k["t"]) for prop, keys in props.items()}
            for part, props in data.get("tracks", {}).items()
        }
        self.events = sorted(data.get("events", []), key=lambda e: e["t"])

    @staticmethod
    def load_file(source):
        if isinstance(source, AnimationSet):
            source = source.value
        if not source:
            return {}

        path = source if os.path.isabs(source) else os.path.join(ANIMATIONS_DIR, source)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"[Animator] Fichier d'animations introuvable : {path}")
            return {}                      # le jeu continue, sans animations

        known = {a.value for a in Anim}
        clips = {}
        for key, clip_data in data.items():
            if key not in known:
                print(f"[Animator] Animation inconnue dans {path} : '{key}' (absente de l'enum Anim)")
            clips[key] = AnimationClip(key, clip_data)
        return clips


class Animator:
    def __init__(self, parts, clips):
        self.parts = {p.name: p for p in parts}
        self.clips = clips
        # pose de repos mémorisée une fois pour toutes
        self.rest = {n: (pygame.Vector2(p.offset), getattr(p, "angle", 0),
                         getattr(p, "alpha", 255)) for n, p in self.parts.items()}
        self.current = None
        self.time = 0.0
        self.speed = 1.0
        self.finished = False
        self.on_event = None        # callback(event_name, clip_name)
        self.on_finish = None       # callback(clip_name)
        self._last = -1.0

    @staticmethod
    def _animatable(part):
        return part.kind == "texture"

    def _register(self, part):
        if not self._animatable(part):
            return False
        if part.name in self.parts:
            raise ValueError(f"Une part nommée '{part.name}' existe déjà")
        self.parts[part.name] = part
        self.rest[part.name] = (
            pygame.Vector2(part.offset),
            getattr(part, "angle", 0),
            getattr(part, "alpha", 255),
        )
        return True

    def set_rest(self, part_name, angle=None):
        if part_name in self.rest:
            off, ang, alpha = self.rest[part_name]
            self.rest[part_name] = (off, ang if angle is None else angle, alpha)

    def add_part(self, part):
        return self._register(part)

    def remove_part(self, name):
        self.rest.pop(name, None)
        return self.parts.pop(name, None)

    def has(self, name):
        return _key(name) in self.clips

    def play(self, name, restart=False):
        name = _key(name)
        if name == self.current and not restart:
            return
        self.current = name
        self.time = 0.0
        self._last = -1.0
        self.finished = False

    @property
    def busy(self):
        """True pendant une action (clip non bouclé en cours) : la marche/idle ne doit pas la couper."""
        clip = self.clips.get(self.current)
        return clip is not None and not clip.loop and not self.finished

    def _fire_events(self, clip, prev, now, wrapped):
        if not (self.on_event and clip.events):
            return
        for ev in clip.events:
            t = ev["t"]
            crossed = (t > prev or t <= now) if wrapped else (prev < t <= now)
            if crossed:
                self.on_event(ev["name"], clip.name)

    def update(self, dt):
        # 1) retour à la pose de repos
        for n, p in self.parts.items():
            off, ang, alpha = self.rest[n]
            p.offset = pygame.Vector2(off)
            if hasattr(p, "angle"):
                p.angle, p.alpha = ang, alpha

        clip = self.clips.get(self.current)
        if clip is None:
            return

        # 2) avance du temps
        prev, wrapped = self._last, False
        self.time += dt * self.speed
        if self.time >= clip.duration:
            if clip.loop:
                self.time %= clip.duration
                wrapped = True
            else:
                self.time, self.finished = clip.duration, True

        # 3) événements (une seule fois chacun)
        self._fire_events(clip, prev, self.time, wrapped)
        self._last = self.time

        # 4) application des pistes
        for part_name, props in clip.tracks.items():
            p = self.parts.get(part_name)
            if p is None:
                continue
            off, ang, alpha = self.rest[part_name]
            if "offset" in props:
                dx, dy = _sample(props["offset"], self.time)
                p.offset = off + pygame.Vector2(dx, dy)
            if "angle" in props and hasattr(p, "angle"):
                p.angle = (ang + _sample(props["angle"], self.time)) % 360
            if "alpha" in props and hasattr(p, "alpha"):
                p.alpha = int(_sample(props["alpha"], self.time))

        # 5) fin d'une action : on libère, l'idle/walk reprend au prochain update
        if self.finished and not clip.loop:
            finished_name = self.current
            self.current = None
            if self.on_finish:
                self.on_finish(finished_name)