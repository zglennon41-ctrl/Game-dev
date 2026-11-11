"""WILDLINE detail textures: tileable greyscale patterns the cel shader blends under its
bands by triplanar projection, so no model needs UVs (docs/graphics-comparison.md,
docs/style.md rule 3). 256 square, mid-grey on average so they neither lighten nor darken the
colour. Run: python3 tools/textures.py

The first seven are what a thing is made of, by its class (data/style.json,
materials.classes), and are what a place wears: linen (a weave), wool (a soft noise), leather
(grain), bronze (brushed), skin (fine pores), stone (a mottle), wood (grain).

The other thirteen are what a body is covered in, by its material's name (materials.grains):
fur (pointed locks, a lit tip over the dark root of the next), feathers (overlapping vanes,
shafted and barbed), scales (overlapping rows), pebble (a hide of small bumps), horn (fine
rings: horn, claw, beak, shell, chitin), hammered (soft dimples: plate, iron), twill (a
herringbone weave: a cloak, a robe, a rope), bark (fissures), fog (soft cloud: mist, smoke,
shadow), timber (wood's figure and pores), creased (worn leather), brushed (steel, brass), rock
(stone, slate, clay, coal, bone). A coat's are shapes cut clean, and shaded root to tip so
that they still read from across a yard, where a thin line would be gone (docs/style.md,
rule 1: detail is cut in as planes, never as noise).

Where a pattern has a direction it runs down the picture, which the shader lays toward the
tail along a body's back and sides and toward the ground on its front; wood, brushed metal,
bark and horn run along the piece they are on instead (materials.grainFit.along). Every one
tiles: each is made of pieces that wrap (noise shaped in its Fourier transform, points and
rows counted round the edge), never of a picture cut to size.
"""
import os
import zlib
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


def fresh(name):
    """Each of these grains draws from a stream of its own, so that making one anew (or adding
    one) changes no other."""
    global rng2
    rng2 = np.random.default_rng(zlib.crc32(name.encode()))


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


def shingles(n, cols, rows, length, width, taper, du=0.0, dv=0.0):
    """Rows of overlapping shapes hanging tip down (scales, feathers, locks of fur): every
    other row half a step across, each row lying over the one below it. For every pixel, where
    it is on the shape that shows there: across (-1 to 1 at the shape's edge) and along (0 at
    its root, 1 at its tip). rows must be even for the picture to tile. taper 1 is a point, 2 a
    round end. du, dv: how far each pixel is pushed across and down before it is asked (in
    tiles; pictures that wrap), so that the rows are not ruled."""
    v, u = np.mgrid[0:n, 0:n] / float(n)
    u = u + du
    v = v + dv
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


def keep(name, a):
    """Save a grain, having seen that it repeats without a seam: the step from its last row to
    its first, and from its last column to its first, is no greater than its steps elsewhere."""
    for axis, what in ((0, "top to bottom"), (1, "side to side")):
        steps = np.abs(np.diff(a, axis=axis, append=np.take(a, [0], axis=axis))).mean(axis=1 - axis)
        if steps[-1] > 1.25 * steps[:-1].max():
            raise SystemExit("%s does not tile %s: the step across its edge is %.4f and nowhere else over %.4f" % (name, what, steps[-1], steps[:-1].max()))
    save(name, a)


def more():
    v, u = np.mgrid[0:N, 0:N] / float(N)
    # fur: locks lying down the picture, each a pointed tuft over the next (what is seen of a
    # coat from across a yard), and strokes within them (what is seen of it close)
    fresh("fur")
    x, y, on = shingles(N, 8, 2, 1.7, 1.5, 1.35, du=0.01 * streaks(N, 40.0, 20.0), dv=0.13 * streaks(N, 6.0, 80.0))
    lock = 0.3 + 0.44 * step(0.3, 0.75, y) - 0.2 * step(0.5, 1.0, np.abs(x)) * (1.0 - 0.5 * y)
    strokes = np.tanh(2.0 * streaks(N, 1.0, 11.0)) * 0.5 + np.tanh(1.4 * streaks(N, 2.6, 26.0)) * 0.36 + 0.3 * streaks(N, 11.0, 22.0)
    lock = smooth(np.where(on, lock, 0.25), 1.0, 1.6)
    keep("fur", level((lock - lock.mean()) / lock.std() * 0.8 + strokes / strokes.std() * 0.5, 0.095, 0.2, 0.8))
    # feathers: long vanes overlapping, each with a shaft and its barbs, a dark edge where the next lies under
    fresh("feathers")
    x, y, on = shingles(N, 3, 4, 2.3, 1.12, 2.2)
    shaft = np.exp(-(x / 0.07) ** 2)
    barbs = np.sin((y * 2.3 * 9.0 - np.abs(x) * 3.2) * 2.0 * np.pi) * (1.0 - shaft) * step(0.0, 0.25, y)
    edge = step(0.82, 1.0, np.maximum(np.abs(x), y ** 3))
    feathers = 0.5 + 0.46 * (step(0.25, 1.0, y) - 0.5) + 0.1 * shaft * step(0.05, 0.3, y) + 0.05 * barbs - 0.3 * edge
    keep("feathers", level(smooth(np.where(on, feathers, 0.26), 0.7, 0.7), 0.1, 0.2, 0.8))
    # scales: short round scales in rows, bright toward the lip, shadowed where the row above lies over
    fresh("scales")
    x, y, on = shingles(N, 4, 6, 1.75, 1.1, 2.0)
    r = np.sqrt(x ** 2 * 0.55 + y ** 2)
    lip = step(0.84, 1.0, np.maximum(np.abs(x) ** 1.5, y ** 2))
    scales = 0.5 + 0.5 * (step(0.2, 1.0, y) - 0.5) + 0.05 * np.cos(r * 9.0) * step(0.2, 0.6, y) - 0.32 * lip
    keep("scales", level(smooth(np.where(on, scales, 0.26), 0.8, 0.8), 0.1, 0.2, 0.8))
    # pebble: a hide of small bumps with dark grooves between (a tortoise's leg, a lizard's flank, an octopus)
    fresh("pebble")
    f1, f2 = cells(N, 11, 0.85)
    pebble = 0.5 + 0.2 * (1.0 - step(0.0, 0.5, f1)) - 0.3 * (1.0 - step(0.0, 0.13, f2 - f1))
    keep("pebble", level(smooth(pebble, 0.8, 0.8), 0.075))
    # horn: fine ridges across the grain, uneven (horn, antler, claw, beak, a shell's rings, chitin)
    fresh("horn")
    warp = streaks(N, 26.0, 9.0)
    ridges = (0.5 + 0.5 * np.sin((v * 22.0 + warp * 0.34) * 2.0 * np.pi)) ** 1.6
    horn = ridges * 0.8 + 0.2 * (0.5 + 0.5 * np.sin((v * 66.0 + warp * 0.9) * 2.0 * np.pi)) + 0.12 * streaks(N, 9.0, 2.0)
    keep("horn", level(horn, 0.07))
    # hammered: soft dimples, each with a bright rim where it meets the next (beaten plate)
    fresh("hammered")
    f1, f2 = cells(N, 7, 0.7)
    hammered = 0.5 - 0.16 * (1.0 - step(0.0, 0.55, f1)) + 0.14 * (1.0 - step(0.0, 0.16, f2 - f1))
    keep("hammered", level(smooth(hammered, 1.6, 1.6), 0.06))
    # twill: a herringbone weave, the diagonal turning back every band
    fresh("twill")
    bands, threads = 8, 16
    turn = np.where(np.floor(u * bands) % 2 == 0, 1.0, -1.0)
    wale = 0.5 + 0.5 * np.sin((v * threads + turn * (u * bands - np.floor(u * bands)) * (threads / bands) * 2.0) * 2.0 * np.pi)
    seam = 1.0 - step(0.0, 0.08, np.abs((u * bands) % 1.0 - 0.5) * 2.0 - 0.92 + 0.08)
    twill = wale ** 0.8 - 0.25 * seam + 0.18 * streaks(N, 1.2, 1.2)
    keep("twill", level(twill, 0.075))
    # bark: broad ridges with narrow dark fissures running down
    fresh("bark")
    grain = streaks(N, 5.0, 46.0)
    fissure = 1.0 - step(0.04, 0.62, np.abs(grain))
    bark = 0.58 - 0.42 * fissure + 0.1 * np.tanh(streaks(N, 2.0, 20.0)) + 0.05 * streaks(N, 6.0, 2.0)
    keep("bark", level(bark, 0.085))
    # fog: soft cloud, nothing in it small (mist, smoke, a body of shadow)
    fresh("fog")
    keep("fog", level(cloud(N, 1.75), 0.095, 0.2, 0.8))
    # timber: wood as a body carries it (a bow, a shield, a stock): the figure of the grain in
    # long bands down the picture, and the pores along it
    fresh("timber")
    figure = (0.5 + 0.5 * np.sin((u * 7.0 + 0.3 * streaks(N, 14.0, 60.0)) * 2.0 * np.pi)) ** 1.4
    timber = 0.52 * (figure - figure.mean()) / figure.std() + 0.42 * np.tanh(1.5 * streaks(N, 1.1, 34.0)) + 0.26 * streaks(N, 5.0, 90.0)
    keep("timber", level(timber, 0.08))
    # creased: worn leather: a crackle of creases, and a fine pebble between them
    fresh("creased")
    f1, f2 = cells(N, 5, 0.95)
    g1, g2 = cells(N, 21, 0.9)
    creased = 0.5 - 0.4 * (1.0 - step(0.0, 0.2, f2 - f1)) ** 1.5 + 0.08 * (1.0 - step(0.0, 0.6, g1)) - 0.1 * (1.0 - step(0.0, 0.22, g2 - g1)) + 0.11 * cloud(N, 1.9)
    keep("creased", level(smooth(creased, 0.7, 0.7), 0.085))
    # brushed: metal drawn along a stone: fine scratches down the picture, a few of them deep
    fresh("brushed")
    deep = streaks(N, 0.8, 70.0)
    brushed = 0.6 * np.tanh(1.3 * streaks(N, 0.9, 42.0)) + 0.3 * streaks(N, 3.5, 100.0) - 0.5 * step(2.1, 2.9, deep) + 0.12 * cloud(N, 1.5)
    keep("brushed", level(brushed, 0.07))
    # rock: stone as a body carries it (slate, clay, coal, old bone): a rough mottle, pits, a few cracks
    fresh("rock")
    f1, f2 = cells(N, 4, 1.0)
    g1, g2 = cells(N, 13, 1.0)
    pick = smooth(rng2.random((N, N)), 6.0, 6.0)
    pits = (1.0 - step(0.05, 0.2, g1)) * step(0.0, 0.004, pick - np.median(pick))
    rock = 0.5 + 0.22 * cloud(N, 1.3) - 0.3 * pits - 0.4 * (1.0 - step(0.0, 0.05, f2 - f1)) * step(-0.2, 0.5, cloud(N, 2.0))
    keep("rock", level(smooth(rock, 0.6, 0.6), 0.075))


# --- what a place is built of (data/style.json, materials.places) -------------------------------
# The third pass (docs/graphics-comparison.md): a floor, a wall and a roof wear grains made as
# carefully as a body's. They are 512 square: a place's grain is laid a metre or two to the
# picture, and the camera stands on it. Where a kit models its joints (the Academy's flags, its
# boards) the grain is the SURFACE of the thing (tooling, pits, figure); where a kit leaves a
# broad plane (a wall of stone, a roof, the wild's ground) the grain carries the joints too.

P = 512


def angled(n, su, sv, angle):
    """Noise drawn out into streaks su wide and sv long, lying at an angle; of unit spread."""
    f = np.fft.fft2(rng2.standard_normal((n, n)))
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    c, s = np.cos(angle), np.sin(angle)
    a = np.real(np.fft.ifft2(f * np.exp(-2.0 * np.pi ** 2 * (((fx * c + fy * s) * su) ** 2 + ((-fx * s + fy * c) * sv) ** 2))))
    return a / a.std()


def coursed(n, rows, least, most, bond=None):
    """Courses of blocks: `rows` courses to the picture, each cut into blocks between `least`
    and `most` of the picture wide (or, with bond, that many equal blocks a course, every other
    course half a block along). For every pixel: how far the nearest joint is (in pixels), and
    a number of its own for the block it is in (0 to 1). Each course wraps, so it tiles."""
    y, x = np.mgrid[0:n, 0:n].astype(float)
    h = n / float(rows)
    row = np.floor(y / h).astype(int)
    dy = np.minimum(y - row * h, (row + 1) * h - y)
    dx = np.full((n, n), 1e9)
    tone = np.zeros((n, n))
    for r in range(rows):
        if bond:
            w = n / float(bond)
            cuts = (np.arange(bond) * w + (0.5 * w if r % 2 else 0.0)) % n
        else:
            cuts = [rng2.uniform(0, n)]
            while True:
                nxt = cuts[-1] + rng2.uniform(least, most) * n
                if nxt > cuts[0] + n - least * n:
                    break
                cuts.append(nxt)
            cuts = np.array(cuts) % n
        cuts = np.sort(cuts)
        tones = rng2.random(len(cuts))
        xs = x[r == row[:, 0]][0]
        idx = (np.searchsorted(cuts, xs, side="right") - 1) % len(cuts)
        lo = cuts[idx]
        hi = cuts[(idx + 1) % len(cuts)]
        d = np.minimum((xs - lo) % n, (hi - xs) % n)
        sel = row[:, 0] == r
        dx[sel, :] = d[None, :]
        tone[sel, :] = tones[idx][None, :]
    return np.minimum(dx, dy), tone


def places():
    v, u = np.mgrid[0:P, 0:P] / float(P)
    # flagstone: the face of a worn paving stone (the joints are the kit's): a mottle, the mason's
    # tooling, pits, a crack here and there, polished pale where feet have gone
    fresh("flagstone")
    f1, f2 = cells(P, 3, 1.0)
    g1, g2 = cells(P, 26, 1.0)
    pick = smooth(rng2.random((P, P)), 9.0, 9.0)
    pits = (1.0 - step(0.04, 0.24, g1)) * step(0.0, 0.004, pick - np.median(pick))
    crack = (1.0 - step(0.0, 0.03, f2 - f1)) * step(0.3, 0.9, cloud(P, 2.0))
    tool = np.tanh(1.3 * angled(P, 1.3, 16.0, 0.55))
    flag = 0.5 + 0.2 * cloud(P, 1.6) + 0.085 * tool + 0.06 * streaks(P, 1.0, 1.0) - 0.34 * pits - 0.42 * crack
    keep("flagstone", level(smooth(flag, 0.7, 0.7), 0.085))
    # ashlar: a wall of dressed stone in courses: every block its own tone, its face tooled, its
    # arrises worn, the joints dark and fine
    fresh("ashlar")
    d, tone = coursed(P, 4, 0.2, 0.42)
    joint = 1.0 - step(1.0, 5.0, d)
    arris = step(4.0, 16.0, d)
    tool = np.tanh(1.2 * angled(P, 1.4, 12.0, -0.5))
    ashlar = 0.5 + 0.34 * (tone - 0.5) + 0.1 * (arris - 0.7) + 0.09 * cloud(P, 1.5) + 0.06 * tool - 0.62 * joint
    keep("ashlar", level(smooth(ashlar, 0.7, 0.7), 0.09))
    # brick: a running bond, the bricks of one clay and many firings, the mortar raked back
    fresh("brick")
    d, tone = coursed(P, 8, 0, 0, bond=4)
    joint = 1.0 - step(1.5, 5.0, d)
    brick = 0.5 + 0.4 * (tone - 0.5) + 0.08 * cloud(P, 1.2) + 0.05 * streaks(P, 5.0, 1.0) - 0.5 * joint
    keep("brick", level(smooth(brick, 0.7, 0.7), 0.09))
    # plaster: limewash over rubble: the sweep of the float, blotches where damp has been, hairline cracks
    fresh("plaster")
    f1, f2 = cells(P, 4, 1.0)
    crack = (1.0 - step(0.0, 0.02, f2 - f1)) * step(0.6, 1.3, cloud(P, 2.0))
    sweep = 0.6 * np.tanh(angled(P, 3.0, 40.0, 0.3)) + 0.4 * np.tanh(angled(P, 3.0, 34.0, -0.9))
    plaster = 0.5 + 0.24 * cloud(P, 2.0) + 0.1 * sweep + 0.04 * streaks(P, 1.0, 1.0) - 0.5 * crack
    keep("plaster", level(smooth(plaster, 0.6, 0.6), 0.08))
    # planks: sawn boards (the joints are the kit's): the figure in long bands ACROSS the picture
    # (a floor's boards run that way), pores, a knot or two
    fresh("planks")
    k1, k2 = cells(P, 3, 1.0)
    knot = 1.0 - step(0.0, 0.16, k1)
    figure = (0.5 + 0.5 * np.sin((v * 7.0 + 0.3 * streaks(P, 120.0, 26.0) + 0.35 * knot) * 2.0 * np.pi)) ** 1.4
    planks = 0.5 * (figure - figure.mean()) / figure.std() + 0.42 * np.tanh(1.5 * streaks(P, 64.0, 1.2)) + 0.3 * streaks(P, 180.0, 8.0) - 0.5 * step(0.55, 1.0, knot)
    keep("planks", level(planks, 0.085))
    # slate: riven slate (a roof, a dark floor): the cleft's fine steps like the lines of a map,
    # and the nicks along them
    fresh("slate")
    lay = cloud(P, 2.3)
    cleft = np.abs(((lay * 2.6) % 1.0) - 0.5) * 2.0
    slate = 0.5 + 0.07 * lay + 0.1 * cloud(P, 1.2) - 0.3 * (1.0 - step(0.0, 0.16, cleft)) + 0.08 * np.tanh(angled(P, 1.0, 9.0, 0.2)) + 0.05 * streaks(P, 1.0, 1.0)
    keep("slate", level(smooth(slate, 0.7, 0.7), 0.08))
    # cobble: small stones set close (the bed of the line, a lane): each one domed and worn pale on top
    fresh("cobble")
    f1, f2 = cells(P, 12, 0.9)
    tone = smooth(rng2.random((P, P)), 5.0, 5.0)
    cobble = 0.5 + 0.26 * (1.0 - step(0.0, 0.55, f1)) - 0.44 * (1.0 - step(0.0, 0.16, f2 - f1)) + 2.2 * (tone - tone.mean()) + 0.05 * streaks(P, 1.0, 1.0)
    keep("cobble", level(smooth(cobble, 0.9, 0.9), 0.09))
    # earth: trodden ground: grit, a scatter of small stones each with its shadow, the hollows of old prints
    fresh("earth")
    g1, g2 = cells(P, 20, 1.0)
    pick = smooth(rng2.random((P, P)), 7.0, 7.0)
    stone = (1.0 - step(0.08, 0.3, g1)) * step(0.0, 0.006, pick - np.median(pick))
    lit = np.roll(stone, 2, axis=0) - stone
    earth = 0.5 + 0.22 * cloud(P, 1.7) + 0.1 * streaks(P, 1.1, 1.1) + 0.3 * stone - 0.3 * np.maximum(lit, 0.0) + 0.07 * np.tanh(angled(P, 2.0, 14.0, 1.1))
    keep("earth", level(smooth(earth, 0.6, 0.6), 0.085))
    # grass: turf from above: blades lying every way in tufts, light tips over the dark between
    fresh("grass")
    f1, f2 = cells(P, 9, 1.0)
    way = cloud(P, 2.4)
    blades = np.zeros((P, P))
    for i, ang in enumerate((0.2, 0.9, 1.6, 2.3, 2.9)):
        blades += np.tanh(1.8 * angled(P, 1.0, 10.0, ang)) * np.exp(-((way - (i - 2) * 0.7) / 0.6) ** 2)
    grass = 0.5 + 0.3 * blades + 0.14 * (1.0 - step(0.0, 0.6, f1)) - 0.16 * (1.0 - step(0.0, 0.2, f2 - f1)) + 0.12 * cloud(P, 1.6)
    keep("grass", level(smooth(grass, 0.6, 0.6), 0.09))


if __name__ == "__main__":
    import sys
    if "--places" in sys.argv:
        places()      # the first twenty stay as they were made
    else:
        main()
        more()
        places()
