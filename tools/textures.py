"""WILDLINE detail textures: five tileable greyscale patterns the cel shader blends under
its bands by world-space triplanar projection (docs/graphics-comparison.md): linen (a weave),
wool (a soft noise), leather (grain), bronze (brushed), skin (fine pores). 256 square, mid-grey
on average so they neither lighten nor darken the colour. Run: python3 tools/textures.py
"""
import os
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "assets", "textures", "detail")
N = 256
rng = np.random.default_rng(7)


def tile_noise(n, octaves=4, base=8, persistence=0.55):
    """Tileable value noise by summing wrapped, smoothly resized grids."""
    out = np.zeros((n, n))
    amp = 1.0
    total = 0.0
    for o in range(octaves):
        cells = min(n // 2, base * (2 ** o))
        grid = rng.random((cells, cells))
        # tile by wrapping: resize with bilinear interpolation on a wrapped grid
        big = np.kron(grid, np.ones((n // cells, n // cells)))
        # smooth to remove the blockiness, wrapping
        k = max(1, n // cells // 2)
        sm = big.copy()
        for _ in range(2):
            sm = (np.roll(sm, k, 0) + np.roll(sm, -k, 0) + np.roll(sm, k, 1) + np.roll(sm, -k, 1) + 4 * sm) / 8.0
        out += sm * amp
        total += amp
        amp *= persistence
    out /= total
    return out


def normalize(a, lo=0.35, hi=0.65):
    a = (a - a.min()) / max(1e-6, a.max() - a.min())
    return lo + a * (hi - lo)


def save(name, a):
    img = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img, "L").save(os.path.join(OUT, name + ".png"))
    print("wrote", name, "mean %.2f" % a.mean())


def main():
    os.makedirs(OUT, exist_ok=True)
    y, x = np.mgrid[0:N, 0:N]
    # linen: a crosshatched weave of threads, 16 per tile each way, with slight unevenness
    threads = 16
    wx = 0.5 + 0.5 * np.sin(x / N * threads * 2 * np.pi)
    wy = 0.5 + 0.5 * np.sin(y / N * threads * 2 * np.pi)
    weave = np.where(((x // (N // threads)) + (y // (N // threads))) % 2 == 0, wx, wy)
    linen = normalize(weave * 0.7 + tile_noise(N, 3, 8) * 0.3, 0.38, 0.62)
    save("linen", linen)
    # wool: soft noise with a faint diagonal nap
    nap = 0.5 + 0.5 * np.sin((x + y) / N * 40 * 2 * np.pi)
    save("wool", normalize(tile_noise(N, 5, 4, 0.6) * 0.8 + nap * 0.2, 0.4, 0.6))
    # leather: grain from cells, darker creases between them
    cells = tile_noise(N, 2, 16, 0.5)
    grain = np.abs(np.gradient(cells)[0]) + np.abs(np.gradient(cells)[1])
    save("leather", normalize(cells * 0.6 - grain * 6.0 + tile_noise(N, 4, 32, 0.5) * 0.3, 0.34, 0.62))
    # bronze: brushed streaks along one axis, a little mottle
    streaks = tile_noise(N, 3, 2, 0.5)
    streaks = np.roll(streaks, 0, 1)
    brushed = 0.5 + 0.5 * np.sin(y / N * 64 * 2 * np.pi + streaks * 6.0)
    save("bronze", normalize(brushed * 0.35 + tile_noise(N, 4, 8, 0.5) * 0.65, 0.42, 0.6))
    # skin: fine pores, barely there
    save("skin", normalize(tile_noise(N, 5, 32, 0.5), 0.44, 0.56))
    # stone: a coarse mottle with flecks, for floors, walls and rock
    stone = tile_noise(N, 4, 4, 0.55) * 0.7 + tile_noise(N, 3, 32, 0.5) * 0.3
    flecks = (rng.random((N, N)) > 0.985).astype(float)
    save("stone", normalize(stone - flecks * 0.25, 0.38, 0.62))
    # wood: grain along one axis, warped by slow noise
    warp = tile_noise(N, 2, 2, 0.5)
    grain = 0.5 + 0.5 * np.sin((x / N * 14 + warp * 3.0) * 2 * np.pi)
    save("wood", normalize(grain * 0.6 + tile_noise(N, 4, 16, 0.5) * 0.4, 0.4, 0.6))


if __name__ == "__main__":
    main()
