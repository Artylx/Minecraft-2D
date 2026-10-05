from enum import Enum
from terrakit.struct import StructureType
from noise import pnoise1
import bisect

class BiomeType(Enum):
    PLAINS = "plains"
    HILLS = "hills"
    MOUNTAINS = "mountains"
    FOREST = "forest"
    DEEP_OCEAN = "deep_ocean"
    REDSTONE_DESERT = "redstone_desert"
    ROCK_MONS = "rock_mons"

class BiomeManager:
    # (biome, poids) dans l'ordre d'enchaînement. Les voisins se mélangent.
    LAYOUT = [
        (BiomeType.DEEP_OCEAN,      0.10),
        (BiomeType.PLAINS,          0.16),
        (BiomeType.FOREST,          0.18),
        (BiomeType.HILLS,           0.18),
        (BiomeType.MOUNTAINS,       0.14),
        (BiomeType.ROCK_MONS,       0.10),
        (BiomeType.REDSTONE_DESERT, 0.14),
    ]

    PARAMS = {  # (amplitude, base_height)
        BiomeType.DEEP_OCEAN:      (20, 0),
        BiomeType.PLAINS:          (10, 20),
        BiomeType.FOREST:          (15, 22),
        BiomeType.HILLS:           (20, 25),
        BiomeType.MOUNTAINS:       (35, 40),
        BiomeType.ROCK_MONS:       (30, 45),   # à ajuster selon ton biome
        BiomeType.REDSTONE_DESERT: (12, 18),
    }

    def __init__(self):
        self.biome_scale = 0.001   # biomes ~3,5x plus larges qu'aujourd'hui
        self.noise_gain = 1.4

        total = sum(w for _, w in self.LAYOUT)
        self.ranges = []
        start = 0.0
        for biome, w in self.LAYOUT:
            end = start + w / total
            self.ranges.append((start, end, biome))
            start = end

        samples = [pnoise1(x * self.biome_scale, octaves=2)
                   for x in range(0, 400000, 11)]
        samples.sort()
        self._noise_sorted = samples

    def get_t(self, world_x, seed):
        noise = pnoise1(world_x * self.biome_scale, base=seed, octaves=2)
        rank = bisect.bisect_left(self._noise_sorted, noise)
        return rank / len(self._noise_sorted)

    def get_biome_generate_values(self, world_x, seed):
        t = self.get_t(world_x, seed)

        i = len(self.ranges) - 1
        for k, (t_min, t_max, _) in enumerate(self.ranges):
            if t <= t_max:
                i = k
                break

        t_min, t_max, b0 = self.ranges[i]
        b1 = self.ranges[min(i + 1, len(self.ranges) - 1)][2]
        blend = (t - t_min) / (t_max - t_min) if t_max > t_min else 0.0

        amp0, base0 = self.PARAMS[b0]
        amp1, base1 = self.PARAMS[b1]
        amplitude = amp0 * (1 - blend) + amp1 * blend
        base_height = base0 * (1 - blend) + base1 * blend

        # même logique que le terrain : le biome affiché est le plus proche
        biome = b0 if blend < 0.5 else b1
        return biome, amplitude, base_height

    def get_biome_at(self, world_x, seed):
        return self.get_biome_generate_values(world_x, seed)[0]

    STRUCTURES = {
        BiomeType.FOREST: [(0.10, StructureType.BIG_TREE), (0.15, StructureType.ROCK),
                        (0.20, StructureType.GRASS_2), (0.25, StructureType.MUSHROOM),
                        (0.30, StructureType.SMALL_TREE), (0.13, StructureType.ROCK_MOSS)],
        BiomeType.PLAINS: [(0.15, StructureType.SMALL_TREE), (0.20, StructureType.ROCK),
                        (0.25, StructureType.MUSHROOM), (0.30, StructureType.GRASS_3),
                        (0.35, StructureType.GRASS_4)],
        BiomeType.HILLS: [(0.10, StructureType.ROCK), (0.13, StructureType.SMALL_TREE), (0.15, StructureType.MUSHROOM), 
                        (0.30, StructureType.GRASS_TAN),
                        (0.25, StructureType.GRASS_3), (0.35, StructureType.GRASS_4)],
        BiomeType.ROCK_MONS: [(0.20, StructureType.ROCK), (0.10, StructureType.ROCK_MOSS)],
        BiomeType.DEEP_OCEAN: [(0.15, StructureType.SMALL_TREE), (0.20, StructureType.ROCK),
                        (0.25, StructureType.MUSHROOM), (0.30, StructureType.GRASS_3),
                        (0.35, StructureType.GRASS_4)],
        BiomeType.MOUNTAINS: [(0.15, StructureType.SMALL_TREE), (0.20, StructureType.ROCK),
                        (0.25, StructureType.MUSHROOM), (0.30, StructureType.GRASS_3),
                        (0.35, StructureType.GRASS_4)],
        BiomeType.REDSTONE_DESERT: [(0.15, StructureType.ROCK), (0.25, StructureType.GRASS_BROWN),
                                    (0.35, StructureType.GRASS_TAN)],
    }

    def get_structure(self, biome_type, r):
        for limit, struct in self.STRUCTURES.get(biome_type, []):
            if r < limit:
                return struct
        return None