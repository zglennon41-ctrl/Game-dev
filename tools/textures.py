"""WILDLINE detail textures: tileable greyscale patterns the cel shader blends under its
bands by triplanar projection, so no model needs UVs (docs/graphics-comparison.md,
docs/style.md rule 3). 256 square, mid-grey on average so they neither lighten nor darken the
colour. Run: python3 tools/textures.py

The first seven are what a thing is made of, by its class (data/style.json,
materials.classes): linen (a weave), wool (a soft noise), leather (grain), bronze (brushed),
skin (fine pores), stone (a mottle), wood (grain).

The second nine are what a body is covered in, by its material's name (materials.grains):
fur (strokes with a lie), feathers (overlapping, barbed), scales (overlapping rows), pebble
(a hide of small bumps), horn (fine ridges: horn, claw, beak, shell, chitin), hammered (soft
dimples: plate), twill (a herringbone weave: a cloak, a robe), bark (fissures), fog (soft
cloud: mist, smoke, shadow). Where a pattern has a direction it runs down the picture, which
the shader lays along a body's length and down its front.
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


# --- what a body is covered in (data/style.json, materials.grains) -----------------------------

rng2 = np.random.default_rng(11)      # its own stream: the first seven stay as they were made


def smooth(a, su, sv):
    """A picture smoothed su pixels across and sv down, wrapping (so it still tiles)."""
    f = np.fft.fft2(a)
    fy = np.fft.fftfreq(a.shape[0])[:, None]
    fx = np.fft.fftfreq(a.shape[1])[None, :]
    return np.real(np.fft.ifft2(f * np.exp(-2.0 * np.pi ** 2 * ((fx * su) ** 2 + (fy * sv) ** 2))))


def streaks(n, su, sv):
    """Noise drawn out into streaks su wide and sv long, of unit spread."""
    a = smooth(rng2.standard_normal((n, n)), su, sv)
    return a / a.std()


def cloud(n, beta=1.8, cut=1.0):
    """Soft tileable cloud: noise with most of its strength in its largest shapes."""
    f = np.fft.fft2(rng2.standard_normal((n, n)))
    fy = np.fft.fftfreq(n)[:, None] * n
    fx = np.fft.fftfreq(n)[None, :] * n
    k = np.sqrt(fx ** 2 + fy ** 2)
    k[0, 0] = 1.0
    a = np.real(np.fft.ifft2(f / k ** beta * (k >= cut)))
    return a / a.std()


def cells(n, g, jitter=0.8):
    """A wrapped scatter of g x g points: for every pixel, how far the nearest is and how far
    the next (in cells), for bumps, dimples and the grooves between them."""
    pts = (np.stack(np.meshgrid(np.arange(g), np.arange(g), indexing="ij"), -1) + 0.5 + (rng2.random((g, g, 2)) - 0.5) * jitter)
    y, x = np.mgrid[0:n, 0:n] * (g / n)
    f1 = np.full((n, n), 9.0)
    f2 = np.full((n, n), 9.0)
    ci, cj = np.floor(y).astype(int), np.floor(x).astype(int)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ii, jj = (ci + di) % g, (cj + dj) % g
            py = pts[ii, jj, 0] + (ci + di - ii)
            px = pts[ii, jj, 1] + (cj + dj - jj)
            d = np.sqrt((y - py) ** 2 + (x - px) ** 2)
            f2 = np.where(d < f1, f1, np.minimum(f2, d))
            f1 = np.minimum(f1, d)
    return f1, f2


def step(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def shingles(n, cols, rows, length, width, taper):
    """Rows of overlapping shapes hanging tip down (scales, feathers): every other row half a
    step across, each row lying over the one below it. For every pixel, where it is on the
    shape that shows there: across (-1 to 1 at the shape's edge) and along (0 at its root, 1
    at its tip). rows must be even for the picture to tile."""
    v, u = np.mgrid[0:n, 0:n] / float(n)
    across = np.zeros((n, n))
    along = np.zeros((n, n))
    done = np.zeros((n, n), dtype=bool)
    r0 = np.floor(v * rows)
    for k in range(int(np.ceil(length)) + 1, -1, -1):          # the highest row that reaches here lies on top
        r = r0 - k
        yy = (v * rows - r) / length                           # 0 at this row's line, 1 at its shapes' tips
        cu = u * cols - 0.5 * (r % 2)
        xx = (cu - np.floor(cu) - 0.5) * 2.0                   # -1 to 1 across its column
        half = width * np.maximum(0.0, 1.0 - np.clip(yy, 0.0, 1.0) ** taper) ** (1.0 / taper)
        for shift in (0.0, 2.0, -2.0):                         # and its neighbours', which lap into this column
            x = xx + shift
            inside = (yy >= 0.0) & (yy <= 1.0) & (np.abs(x) <= half) & ~done
            across = np.where(inside, x / np.maximum(half, 1e-6), across)
            along = np.where(inside, yy, along)
            done |= inside
    return across, along, done


def level(a, spread=0.085, lo=0.24, hi=0.76):
    """Mid-grey on average, with this much spread about it."""
    a = (a - a.mean()) / max(1e-6, a.std()) * spread + 0.5
    a = np.clip(a, lo, hi)
    return a - a.mean() + 0.5


def more():
    v, u = np.mgrid[0:N, 0:N] / float(N)
    # fur: strokes that lie down the picture, in locks
    fur = np.tanh(2.0 * streaks(N, 1.0, 11.0)) * 0.5 + np.tanh(1.4 * streaks(N, 2.6, 26.0)) * 0.36 + 0.3 * streaks(N, 11.0, 22.0)
    save("fur", level(fur, 0.085))
    # feathers: long vanes overlapping, each with a shaft and its barbs, a dark edge where the next lies under
    x, y, on = shingles(N, 3, 4, 2.3, 1.12, 2.2)
    shaft = np.exp(-(x / 0.07) ** 2)
    barbs = np.sin((y * 2.3 * 9.0 - np.abs(x) * 3.2) * 2.0 * np.pi) * (1.0 - shaft) * step(0.0, 0.25, y)
    edge = step(0.82, 1.0, np.maximum(np.abs(x), y ** 3))
    feathers = 0.5 + 0.2 * (y - 0.55) + 0.1 * shaft * step(0.05, 0.3, y) + 0.05 * barbs - 0.34 * edge
    save("feathers", level(smooth(np.where(on, feathers, 0.3), 0.7, 0.7), 0.085))
    # scales: short round scales in rows, bright toward the lip, shadowed where the row above lies over
    x, y, on = shingles(N, 4, 6, 1.75, 1.1, 2.0)
    r = np.sqrt(x ** 2 * 0.55 + y ** 2)
    lip = step(0.84, 1.0, np.maximum(np.abs(x) ** 1.5, y ** 2))
    scales = 0.5 + 0.3 * (y - 0.45) + 0.06 * np.cos(r * 9.0) * step(0.2, 0.6, y) - 0.36 * lip
    save("scales", level(smooth(np.where(on, scales, 0.3), 0.8, 0.8), 0.09))
    # pebble: a hide of small bumps with dark grooves between (a tortoise's leg, a lizard's flank, an octopus)
    f1, f2 = cells(N, 11, 0.85)
    pebble = 0.5 + 0.2 * (1.0 - step(0.0, 0.5, f1)) - 0.3 * (1.0 - step(0.0, 0.13, f2 - f1))
    save("pebble", level(smooth(pebble, 0.8, 0.8), 0.075))
    # horn: fine ridges across the grain, uneven (horn, antler, claw, beak, a shell's rings, chitin)
    warp = streaks(N, 26.0, 9.0)
    ridges = (0.5 + 0.5 * np.sin((v * 22.0 + warp * 0.34) * 2.0 * np.pi)) ** 1.6
    horn = ridges * 0.8 + 0.2 * (0.5 + 0.5 * np.sin((v * 66.0 + warp * 0.9) * 2.0 * np.pi)) + 0.12 * streaks(N, 9.0, 2.0)
    save("horn", level(horn, 0.07))
    # hammered: soft dimples, each with a bright rim where it meets the next (beaten plate)
    f1, f2 = cells(N, 7, 0.7)
    hammered = 0.5 - 0.16 * (1.0 - step(0.0, 0.55, f1)) + 0.14 * (1.0 - step(0.0, 0.16, f2 - f1))
    save("hammered", level(smooth(hammered, 1.6, 1.6), 0.06))
    # twill: a herringbone weave, the diagonal turning back every band
    bands, threads = 8, 16
    turn = np.where(np.floor(u * bands) % 2 == 0, 1.0, -1.0)
    wale = 0.5 + 0.5 * np.sin((v * threads + turn * (u * bands - np.floor(u * bands)) * (threads / bands) * 2.0) * 2.0 * np.pi)
    seam = 1.0 - step(0.0, 0.08, np.abs((u * bands) % 1.0 - 0.5) * 2.0 - 0.92 + 0.08)
    twill = wale ** 0.8 - 0.25 * seam + 0.18 * streaks(N, 1.2, 1.2)
    save("twill", level(twill, 0.075))
    # bark: broad ridges with narrow dark fissures running down
    grain = streaks(N, 5.0, 46.0)
    fissure = 1.0 - step(0.04, 0.62, np.abs(grain))
    bark = 0.58 - 0.42 * fissure + 0.1 * np.tanh(streaks(N, 2.0, 20.0)) + 0.05 * streaks(N, 6.0, 2.0)
    save("bark", level(bark, 0.085))
    # fog: soft cloud, nothing in it small (mist, smoke, a body of shadow)
    save("fog", level(cloud(N, 1.9), 0.075))


if __name__ == "__main__":
    main()
    more()
