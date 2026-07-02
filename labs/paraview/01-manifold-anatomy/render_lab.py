"""PV-1: anatomy of a bad manifold, rendered from the real fields.

Loads the converged simpleFoam solution of the 33-tube condenser
manifold (the single-centred-port generation whose flow CoV measured
131%) and builds the visualization that explains the number: inlet-
seeded streamlines colored by speed over the ghosted tube bundle, and
a velocity-magnitude slice through the feed plane. Rendered headless
through the VTK pipeline; a pvpython twin of this script is alongside
for ParaView proper.
"""
from pathlib import Path
import numpy as np
import pyvista as pv

pv.OFF_SCREEN = True
HERE = Path(__file__).resolve().parent
DATA = Path("/home/claude/expansion/chamber_model_final/openfoam"
            "/condenser_manifold_33_FINISHED/VTK/manifold_33_500")
ASSETS = HERE.parents[2] / "site" / "assets"
BG = "#0e1626"

grid = pv.read(DATA / "internal.vtu").cell_data_to_point_data()
grid["speed"] = np.linalg.norm(grid.point_data["U"], axis=1)
print("cells:", grid.n_cells, "| speed max:", float(grid["speed"].max()))

inlet = pv.read(DATA / "boundary" / "inlet.vtp")
pts = inlet.points
sub = pts[:: max(1, len(pts) // 60)].copy()
inward = np.array(grid.center) - np.array(inlet.center)
inward = inward / np.linalg.norm(inward)
sub += 1.5e-3 * inward                     # nudge seeds into the domain
seed = pv.PolyData(sub)
stream = grid.streamlines_from_source(
    seed, vectors="U", max_length=1.0, integration_direction="forward")
if stream.n_points == 0:
    raise RuntimeError("no streamlines generated from inlet seeds")
stream["speed"] = np.linalg.norm(stream["U"], axis=1)
print("streamline points:", stream.n_points)

pl = pv.Plotter(off_screen=True, window_size=(1500, 950))
pl.set_background(BG)
pl.add_mesh(grid.extract_surface(algorithm=None), color="#8fa2bf", opacity=0.06)
pl.add_mesh(stream.tube(radius=0.0006), scalars="speed", cmap="turbo",
            scalar_bar_args=dict(title="speed (m/s)", color="#dbe4f0",
                                 title_font_size=14, label_font_size=12))
pl.camera_position = "iso"
pl.camera.zoom(1.25)
pl.screenshot(HERE / "pv1-streamlines.png")
pl.close()

sl = grid.slice(normal="y")
pl = pv.Plotter(off_screen=True, window_size=(1500, 700))
pl.set_background(BG)
pl.add_mesh(sl, scalars="speed", cmap="turbo",
            scalar_bar_args=dict(title="speed (m/s)", color="#dbe4f0",
                                 title_font_size=14, label_font_size=12))
pl.add_mesh(grid.extract_surface(algorithm=None), color="#8fa2bf", opacity=0.05)
pl.camera_position = "xz"
pl.camera.zoom(1.6)
pl.screenshot(HERE / "pv1-slice.png")
pl.close()

# composite the two views into one site figure
from PIL import Image
a = Image.open(HERE / "pv1-streamlines.png")
c = Image.open(HERE / "pv1-slice.png")
W = 1500
canvas = Image.new("RGB", (W, a.height + c.height), BG)
canvas.paste(a, (0, 0)); canvas.paste(c, (0, a.height))
canvas.save(ASSETS / "pv1-manifold-anatomy.png")
canvas.save(HERE / "pv1-manifold-anatomy.png")
print("wrote pv1-manifold-anatomy.png", canvas.size)
