"""PV-2: two manifold generations, one comparative frame.

Loads the converged fields of the 42-tube (faithful top-fed manifolds,
flow CoV 10%) and 66-tube (simplified centreline feed, CoV 57% with
that caveat) cases and renders matched mid-plane speed slices plus
pressure slices into a single four-panel comparison. The point of the
lab is visualization craft: matched cameras, matched color ranges per
row, so the eye compares physics instead of colormap artifacts.
"""
from pathlib import Path
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

pv.OFF_SCREEN = True
HERE = Path(__file__).resolve().parent
BASE = Path("/home/claude/expansion/chamber_model_final/openfoam")
CASES = {
    "42-tube, faithful manifold (CoV 10%)":
        BASE / "condenser_manifold_42_v3/run42_results/VTK/run42_500/internal.vtu",
    "66-tube, simplified centreline feed (CoV 57%*)":
        BASE / "condenser_manifold_66_v3/run66_results/VTK/run66_500/internal.vtu",
}
ASSETS = HERE.parents[2] / "site" / "assets"
BG = "#ffffff"

panels = {}
ranges = {"speed": 0.0, "p": [np.inf, -np.inf]}
grids = {}
for name, path in CASES.items():
    g = pv.read(path).cell_data_to_point_data()
    g["speed"] = np.linalg.norm(g.point_data["U"], axis=1)
    grids[name] = g
    ranges["speed"] = max(ranges["speed"], float(g["speed"].max()))
    ranges["p"] = [min(ranges["p"][0], float(g["p"].min())),
                   max(ranges["p"][1], float(g["p"].max()))]
    print(name, "| cells:", g.n_cells, "| speed max:",
          round(float(g['speed'].max()), 3))

for name, g in grids.items():
    for field, clim, cmap in (("speed", [0, ranges["speed"]], "turbo"),
                              ("p", ranges["p"], "coolwarm")):
        sl = g.slice(normal="y")
        pl = pv.Plotter(off_screen=True, window_size=(1400, 620))
        pl.set_background(BG)
        pl.add_mesh(sl, scalars=field, cmap=cmap, clim=clim,
                    scalar_bar_args=dict(
                        title=("speed (m/s)" if field == "speed"
                               else "kinematic p (m2/s2)"),
                        color="#17212F", title_font_size=13,
                        label_font_size=11))
        pl.add_mesh(g.extract_surface(algorithm=None), color="#64748B",
                    opacity=0.05)
        pl.camera_position = "xz"
        pl.camera.zoom(1.55)
        fn = HERE / f"panel_{field}_{name[:2]}.png"
        pl.screenshot(fn)
        pl.close()
        panels[(field, name)] = fn

fig, axes = plt.subplots(2, 2, figsize=(12.6, 6.6), dpi=140)
fig.patch.set_facecolor(BG)
for j, name in enumerate(CASES):
    for i, field in enumerate(("speed", "p")):
        ax = axes[i, j]
        ax.imshow(plt.imread(panels[(field, name)]))
        ax.set_axis_off()
        if i == 0:
            ax.set_title(name, color="#17212F", fontsize=11.5, pad=8)
fig.suptitle("Mid-plane speed (top) and pressure (bottom), matched scales "
             "per row", color="#17212F", fontsize=12.5, y=0.99)
fig.tight_layout()
for p in (ASSETS / "pv2-generation-compare.png",
          HERE / "pv2-generation-compare.png"):
    fig.savefig(p, bbox_inches="tight", facecolor=BG)
print("wrote pv2-generation-compare.png")
