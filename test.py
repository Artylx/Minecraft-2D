from terrakit.biome import BiomeManager

bm = BiomeManager()
seed = 123
runs, last, start = [], None, 0
for x in range(-20000, 20000):
    b = bm.get_biome_at(x, seed)
    if b != last:
        if last is not None:
            runs.append((last, x - start))
        last, start = b, x
from collections import defaultdict
d = defaultdict(list)
for b, l in runs:
    d[b].append(l)
for b, ls in d.items():
    print(b.name, "min", min(ls), "moy", sum(ls)//len(ls), "max", max(ls))