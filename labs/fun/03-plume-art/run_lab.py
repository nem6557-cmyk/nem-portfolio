"""FUN-3: generative art from thermal plumes.

The velocity field is honest fluid intuition: three buoyant plumes
(Gaussian updraft cores with entrainment inflow at their flanks)
superposed with a divergence-free curl-noise field. Thirty thousand
particles advect through it; their trails accumulate on a canvas,
colored by the local plume 'temperature' from deep teal in the cold
far field to orange in the rising cores. Same code, two seeds, two
pieces. Art, but the field would pass a code review.
"""
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "site" / "assets"
BG = "#0e1626"
W, H = 1150, 900
CMAP = LinearSegmentedColormap.from_list(
    "plume", ["#123", "#1b4f5e", "#4FD1C5", "#e8edf4", "#FF8A5B", "#ff5f3c"])

def make_piece(seed):
    rng = np.random.default_rng(seed)
    # curl-noise streamfunction
    psi = gaussian_filter(rng.standard_normal((H // 4, W // 4)), 9)
    gy, gx = np.gradient(psi)
    def curl(x, y):
        i = np.clip((y / 4).astype(int), 0, H // 4 - 1)
        j = np.clip((x / 4).astype(int), 0, W // 4 - 1)
        return 55 * gy[i, j], -55 * gx[i, j]
    plumes = [(rng.uniform(0.2, 0.8) * W, rng.uniform(45, 95),
               rng.uniform(1.6, 2.6)) for _ in range(3)]
    def field(x, y):
        u, v = curl(x, y)
        temp = np.zeros_like(x)
        for cx, w, s in plumes:
            r = (x - cx) / w
            core = np.exp(-r * r)
            v = v - s * 60 * core * (0.35 + 0.65 * (1 - y / H))
            u = u + s * 22 * r * core
            temp = np.maximum(temp, core * (0.3 + 0.7 * (1 - y / H)))
        return u, v, temp
    n = 30000
    x = rng.uniform(0, W, n); y = rng.uniform(0, H, n)
    dens = np.zeros((H, W)); heat = np.zeros((H, W))
    dt = 0.06
    for _ in range(340):
        u, v, temp = field(x, y)
        x = (x + u * dt) % W
        y = (y + v * dt) % H
        xi = x.astype(int) % W; yi = y.astype(int) % H
        np.add.at(dens, (yi, xi), 1.0)
        np.add.at(heat, (yi, xi), temp)
    t = heat / np.maximum(dens, 1)
    a = (dens / dens.max()) ** 0.42
    rgba = CMAP(gaussian_filter(t, 1.4))
    bgc = np.array([14, 22, 38]) / 255
    img = rgba[..., :3] * a[..., None] + bgc * (1 - a[..., None])
    return img

fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.15), dpi=150)
fig.patch.set_facecolor(BG)
for ax, seed, name in ((axes[0], 12, "rise i"), (axes[1], 47, "rise ii")):
    ax.imshow(make_piece(seed), origin="lower")
    ax.set_axis_off()
    ax.set_title(name, color="#dbe4f0", fontsize=11, style="italic", pad=8)
fig.tight_layout()
for p in (ASSETS / "f3-plume-art.png", HERE / "f3-plume-art.png"):
    fig.savefig(p, bbox_inches="tight", facecolor=BG)
(HERE / "RESULTS.txt").write_text(
    "FUN-3 plume art: 30k particles, 340 advection steps through three "
    "buoyant plumes + curl noise; two seeds rendered (12, 47).\n")
print("plume art rendered")
