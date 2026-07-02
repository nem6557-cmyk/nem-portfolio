"""Additional condenser-manifold contour renders for the research CFD page.

White-background renders from the converged simpleFoam fields:
(1) mid-plane kinematic-pressure contours for all three generations,
    per-case color scales since absolute levels differ by design;
(2) axial speed slices through the 42-tube manifold at three stations,
    matched color scale, showing how evenly the faithful manifold
    feeds the bundle along its height.
"""
from pathlib import Path
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

pv.OFF_SCREEN = True
BASE = Path("/home/claude/expansion/chamber_model_final/openfoam")
A = Path(__file__).resolve().parent.parent / "site" / "assets"
BG, FG = "#ffffff", "#17212F"
CASES = [
    ("33-tube", BASE / "condenser_manifold_33_FINISHED/VTK/manifold_33_500/internal.vtu"),
    ("42-tube", BASE / "condenser_manifold_42_v3/run42_results/VTK/run42_500/internal.vtu"),
    ("66-tube", BASE / "condenser_manifold_66_v3/run66_results/VTK/run66_500/internal.vtu"),
]

grids = {}
for name, path in CASES:
    g = pv.read(path).cell_data_to_point_data()
    g["speed"] = np.linalg.norm(g.point_data["U"], axis=1)
    grids[name] = g
    print(name, g.n_cells, "cells")

def slice_shot(g, field, cmap, fname, clim=None, normal="y", origin=None):
    sl = g.slice(normal=normal, origin=origin)
    pl = pv.Plotter(off_screen=True, window_size=(1200, 620))
    pl.set_background(BG)
    pl.add_mesh(sl, scalars=field, cmap=cmap, clim=clim,
                scalar_bar_args=dict(
                    title="p/rho (m2/s2)" if field == "p" else "speed (m/s)",
                    color=FG, title_font_size=13, label_font_size=11))
    pl.add_mesh(g.extract_surface(algorithm=None), color="#64748B", opacity=0.05)
    pl.camera_position = "xz" if normal == "y" else "xy"
    pl.camera.zoom(1.5 if normal == "y" else 1.25)
    pl.screenshot(fname)
    pl.close()

# ---- figure 1: pressure across generations ------------------------------
panels = []
for name, _ in CASES:
    fn = f"/tmp/press_{name}.png"
    slice_shot(grids[name], "p", "coolwarm", fn)
    panels.append((name, fn))
fig, axes = plt.subplots(1, 3, figsize=(14.4, 3.6), dpi=145)
fig.patch.set_facecolor(BG)
for ax, (name, fn) in zip(axes, panels):
    ax.imshow(plt.imread(fn)); ax.set_axis_off()
    ax.set_title(f"{name} manifold", color=FG, fontsize=11.5, pad=6)
fig.suptitle("Mid-plane kinematic pressure, per-case scales",
             color=FG, fontsize=12.5, y=1.00)
fig.tight_layout()
fig.savefig(A / "rcfd-pressure-generations.png", bbox_inches="tight", facecolor=BG)
print("wrote rcfd-pressure-generations.png")

# ---- figure 2: axial speed stations through the 42-tube ------------------
g42 = grids["42-tube"]
zmin, zmax = g42.bounds[4], g42.bounds[5]
smax = float(g42["speed"].max())
stations = [0.18, 0.50, 0.82]
panels = []
for fz in stations:
    z = zmin + fz * (zmax - zmin)
    fn = f"/tmp/ax_{fz}.png"
    slice_shot(g42, "speed", "turbo", fn, clim=[0, smax], normal="z",
               origin=(g42.center[0], g42.center[1], z))
    panels.append((fz, fn))
fig, axes = plt.subplots(1, 3, figsize=(14.4, 4.6), dpi=145)
fig.patch.set_facecolor(BG)
for ax, (fz, fn) in zip(axes, panels):
    ax.imshow(plt.imread(fn)); ax.set_axis_off()
    ax.set_title(f"station at {fz:.0%} of height", color=FG, fontsize=11.5, pad=6)
fig.suptitle("42-tube manifold: axial speed slices, matched scale",
             color=FG, fontsize=12.5, y=1.00)
fig.tight_layout()
fig.savefig(A / "rcfd-axial-42.png", bbox_inches="tight", facecolor=BG)
print("wrote rcfd-axial-42.png")
