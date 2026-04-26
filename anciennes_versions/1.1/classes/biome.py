from enum import Enum
from classes.struct import StructureType
from noise import pnoise1
import math

class BiomeType(Enum):
    PLAINS = "plains"
    HILLS = "hills"
    MOUNTAINS = "mountains"
    FOREST = "forest"
    DEEP_OCEAN = "deep_ocean"
    REDSTONE_DESERT = "redstone_desert"

class BiomeManager:
    def __init__(self):
        self.biomes = [
            BiomeType.MOUNTAINS,
            BiomeType.HILLS,
            BiomeType.PLAINS,
            BiomeType.FOREST,
            BiomeType.REDSTONE_DESERT,
            BiomeType.DEEP_OCEAN,
            ]
        
        self.biome_scale = 0.003
        
    def get_structure(self, biome_type, r):
        if biome_type == BiomeType.FOREST:
            if r < 0.1:
                return StructureType.BIG_TREE
            elif r < 0.15:
                return StructureType.ROCK
            elif r < 0.2:
                return StructureType.GRASS_2
            elif r < 0.25:
                return StructureType.MUSHROOM
            elif r < 0.3:
                return StructureType.SMALL_TREE

        elif biome_type == BiomeType.PLAINS:
            if r < 0.15:
                return StructureType.SMALL_TREE
            elif r < 0.2:
                return StructureType.ROCK
            elif r < 0.25:
                return StructureType.MUSHROOM
            elif r < 0.3:
                return StructureType.GRASS_3
            elif r < 0.35:
                return StructureType.GRASS_4

        elif biome_type == BiomeType.HILLS:
            if r < 0.1:
                return StructureType.SMALL_TREE
            elif r < 0.25:
                return StructureType.MUSHROOM
            elif r < 0.3:
                return StructureType.GRASS_3
            elif r < 0.35:
                return StructureType.GRASS_4

        elif biome_type == BiomeType.MOUNTAINS:
            if r < 0.1:
                return StructureType.GRASS_1
            elif r < 0.15:
                return StructureType.ROCK
            elif r < 0.2:
                return StructureType.GRASS_2
            
    def get_biome_at(self, world_x, seed):
        noise = pnoise1(world_x * self.biome_scale, base=seed)

        # Normalisation
        t = (noise + 1) / 2
        t = max(0.0, min(1.0, t))

        t = (math.sin((t - 0.5) * math.pi) + 1) / 2

        # Mapping
        index = t * (len(self.biomes) - 1)

        i0 = int(index)
        i1 = min(i0 + 1, len(self.biomes) - 1)

        #print(f"t: {t:.3f}, index: {index:.3f}, i0: {i0}, i1: {i1}")

        blend = index - i0

        return self.biomes[i0] if blend < 0.5 else self.biomes[i1]

    def get_biome_params(self, biome):
        if biome == BiomeType.PLAINS:
            return 10, 20
        elif biome == BiomeType.HILLS:
            return 20, 25
        elif biome == BiomeType.MOUNTAINS:
            return 35, 40
        elif biome == BiomeType.FOREST:
            return 15, 22
        elif biome == BiomeType.DEEP_OCEAN:
            return 20, 0
        elif biome == BiomeType.REDSTONE_DESERT:
            return 12, 18
        
    def get_biome_generate_values(self, world_x, seed):
        noise = pnoise1(world_x * self.biome_scale, base=seed)

        # Normalisation
        t = (noise + 1) / 2
        t = max(0.0, min(1.0, t))

        t = (math.sin((t - 0.5) * math.pi) + 1) / 2

        biome_ranges = [
            (0.0, 0.15, BiomeType.DEEP_OCEAN),
            (0.15, 0.3, BiomeType.PLAINS),
            (0.3, 0.5, BiomeType.FOREST),
            (0.5, 0.7, BiomeType.HILLS),
            (0.7, 0.85, BiomeType.MOUNTAINS),
            (0.85, 1.0, BiomeType.REDSTONE_DESERT),
        ]

        for i in range(len(biome_ranges)):
            t_min, t_max, b0 = biome_ranges[i]

            if t >= t_min and t <= t_max:
                if i < len(biome_ranges) - 1:
                    b1 = biome_ranges[i + 1][2]
                else:
                    b1 = b0

                # blend local
                if t_max - t_min == 0:
                    blend = 0
                else:
                    blend = (t - t_min) / (t_max - t_min)

                break

        # 🎯 interpolation terrain
        amp0, base0 = self.get_biome_params(b0)
        amp1, base1 = self.get_biome_params(b1)

        amplitude = amp0 * (1 - blend) + amp1 * blend
        base_height = base0 * (1 - blend) + base1 * blend

        # ✅ biome principal = ton ancien système
        biome = self.get_biome_at(world_x, seed)

        return biome, amplitude, base_height