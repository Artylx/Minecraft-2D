import random
from dataclasses import dataclass
from typing import Callable, Optional
from enum import Enum
import math

import pygame
from terrakit import game_property

class Rarity(Enum):
    COMMON = 1.0          # réussit à chaque fois
    UNCOMMON = 0.5
    RARE = 0.15
    EPIC = 0.04
    LEGENDARY = 0.01

@dataclass(eq=False)                       # eq=False : une catégorie reste hashable (comparée par identité)
class SpawnCategory:
    name: str
    max_count: Optional[int] = None        # plafond partagé par toutes les règles de la catégorie (None = aucun)
    count_radius: int = 80

@dataclass
class SpawnRule:
    entity_class: type
    category: Optional[SpawnCategory] = None
    weight: float = 10                       # fréquence relative parmi les règles disponibles
    rarity: Rarity | float = Rarity.COMMON
    min_light: float = 0
    max_light: float = 15
    group_min: int = 1
    group_max: int = 1
    group_radius: int = 3
    max_count: Optional[int] = 6             # plafond propre à cette entité (None = aucun)
    min_distance: int = 12
    max_distance: int = 40
    vertical_range: int = 20
    size: tuple = (1, 3)
    allow_liquid: bool = False
    condition: Optional[Callable] = None

    @property
    def rarity_value(self):
        return self.rarity.value if isinstance(self.rarity, Rarity) else float(self.rarity)


class MobSpawner:
    def __init__(self, world, rules=None, interval=3.0, attempts=5):
        self.world = world
        self.rules = list(rules or [])
        self.interval = interval             # secondes entre deux cycles de spawn
        self.attempts = attempts             # tentatives par cycle
        self._timer = 0.0

    def add_rule(self, rule):
        self.rules.append(rule)

    def update(self, dt):
        self._timer += dt
        if self._timer < self.interval:
            return
        self._timer = 0.0
        self.spawn_cycle()

    # ---------- cycle ----------

    def spawn_cycle(self):
        if not self.world.is_loaded or not self.rules:
            return                           # pas de spawn pendant le chargement (lumière non calculée)
        players = self.world.get_players()
        if not players:
            return

        for _ in range(self.attempts):
            player = random.choice(players)
            rule = self._pick_rule(player)
            if rule:
                self._try_spawn_group(rule, player, players)

    def _free_slots(self, player, rule):
        """Places restantes pour cette règle autour du joueur (infini si aucune limite)."""
        free = math.inf
        if rule.max_count is not None:
            free = rule.max_count - self._count(player, {rule.entity_class}, rule.max_distance * 2)
        cat = rule.category
        if cat is not None and cat.max_count is not None:
            used = self._count(player, self._classes_of(cat), cat.count_radius)
            free = min(free, cat.max_count - used)
        return free
    
    def _pick_rule(self, player):
        eligible = [r for r in self.rules if r.weight > 0 and self._free_slots(player, r) > 0]
        if not eligible:
            return None
        return random.choices(eligible, weights=[r.weight for r in eligible])[0]

    def _classes_of(self, category):
        return {r.entity_class for r in self.rules if r.category is category}

    def _count(self, player, classes, radius_tiles):
        radius = radius_tiles * game_property.TILE_SIZE
        cx = player.rect.centerx
        return sum(1 for e in self.world.get_entities()
                   if type(e) in classes and abs(e.rect.centerx - cx) <= radius)

    # ---------- groupe ----------

    def _try_spawn_group(self, rule, player, players):
        if random.random() > rule.rarity_value:
            return 0

        spot = self._random_spot(rule, player)
        if spot is None:
            return 0
        x, y = spot

        free = self._free_slots(player, rule)
        wanted = int(min(random.randint(rule.group_min, rule.group_max), free))

        spawned = 0
        for i in range(wanted):
            if i == 0:
                sx, sy = x, y
            else:
                sx = x + random.randint(-rule.group_radius, rule.group_radius)
                sy = self._find_floor(sx, y, rule.group_radius + 2)
                if sy is None:
                    continue
            if self._valid_spot(rule, sx, sy, players):
                self._spawn(rule, sx, sy)
                spawned += 1
        return spawned

    def _random_spot(self, rule, player):
        T = game_property.TILE_SIZE
        px, py = player.rect.centerx // T, player.rect.centery // T
        x = px + random.choice((-1, 1)) * random.randint(rule.min_distance, rule.max_distance)
        y = py + random.randint(-rule.vertical_range, rule.vertical_range)
        fy = self._find_floor(x, y, rule.vertical_range)
        return (x, fy) if fy is not None else None

    def _find_floor(self, x, y_start, search):
        """Renvoie la tuile d'air posée sur un sol solide, la plus proche de y_start, ou None."""
        world = self.world
        y = y_start

        for _ in range(search):                       # dans un bloc solide : on remonte jusqu'à l'air
            block = world.get_block(x, y)
            if block is None:
                return None                           # chunk non chargé
            if not block.can_collide():
                break
            y += 1
        else:
            return None

        for _ in range(search * 2):                   # dans l'air : on descend jusqu'au sol
            below = world.get_block(x, y - 1)
            if below is None:
                return None
            if below.can_collide():
                return y
            y -= 1
        return None

    # ---------- validation ----------

    def _light_at(self, x, y):
        block = self.world.get_block(x, y)
        if block is None:
            return 15
        # le ciel s'assombrit la nuit : on le pondère par le cycle jour/nuit
        return max(block.block_light, block.sky_light)

    @staticmethod
    def _is_liquid(block):
        # À ADAPTER : ta façon de reconnaître un bloc liquide
        return bool(block) and bool(getattr(block.block_property, "is_liquid", False))

    def _valid_spot(self, rule, x, y, players):
        world = self.world
        T = game_property.TILE_SIZE

        if world.get_block(x, y) is None:
            return False

        light = self._light_at(x, y)
        if not (rule.min_light <= light <= rule.max_light):
            return False

        for p in players:                              # jamais trop près d'un joueur
            dx = p.rect.centerx // T - x
            dy = p.rect.centery // T - y
            if dx * dx + dy * dy < rule.min_distance ** 2:
                return False

        w, h = rule.size                               # assez de place pour l'entité
        box = pygame.Rect(x * T + T // 2 - (w * T) // 2, y * T, w * T, h * T)
        if world.is_collide_at(box):
            return False

        if not rule.allow_liquid:
            if any(self._is_liquid(world.get_block(x, y + dy)) for dy in range(h)):
                return False

        if rule.condition and not rule.condition(world, x, y):
            return False
        return True

    def _spawn(self, rule, x, y):
        entity = rule.entity_class(world=self.world)
        entity.tp_tile(x, y)                           # pieds posés sur le sol, centré sur la tuile
        entity.spawn_rule = rule
        self.world.create_entity(entity)