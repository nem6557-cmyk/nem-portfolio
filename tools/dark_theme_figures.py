"""Dark-theme the light matplotlib figures for the site presentation layer.

Hue-preserving lightness inversion (HLS L -> 1-L), then a screen blend
onto the site navy so pure white backgrounds land exactly on #0e1626.
Every data pixel keeps its position; only the theme changes. Project
results/ keep the original light versions as the scientific record.
"""
import colorsys
import numpy as np
from PIL import Image

BG = np.array([14, 22, 38], dtype=float)  # #0e1626

def dark(src, dst):
    im = np.asarray(Image.open(src).convert("RGB"), dtype=float) / 255.0
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    mx, mn = im.max(-1), im.min(-1)
    L = (mx + mn) / 2.0
    c = mx - mn
    s = np.where(c == 0, 0, c / (1 - np.abs(2 * L - 1) + 1e-9))
    # hue
    h = np.zeros_like(L)
    m = (mx == r) & (c > 0); h[m] = ((g - b)[m] / c[m]) % 6
    m = (mx == g) & (c > 0); h[m] = (b - r)[m] / c[m] + 2
    m = (mx == b) & (c > 0); h[m] = (r - g)[m] / c[m] + 4
    h /= 6.0
    L2 = 1.0 - L                               # invert lightness, keep hue/sat
    c2 = (1 - np.abs(2 * L2 - 1)) * s
    x = c2 * (1 - np.abs((h * 6) % 2 - 1))
    z = np.zeros_like(L)
    hp = ((h * 6).astype(int) % 6)[..., None]
    rgb = np.select([hp == 0, hp == 1, hp == 2, hp == 3, hp == 4, hp == 5],
                    [np.stack([c2, x, z], -1), np.stack([x, c2, z], -1),
                     np.stack([z, c2, x], -1), np.stack([z, x, c2], -1),
                     np.stack([x, z, c2], -1), np.stack([c2, z, x], -1)])
    out = (rgb + (L2 - c2 / 2)[..., None]) * 255.0
    out = BG + out * (255.0 - BG) / 255.0      # screen onto navy
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(dst)
    print(f"dark-themed {dst}")

import sys
for name in sys.argv[1:]:
    dark(f"site/assets/{name}", f"site/assets/{name}")  # run from repo root
