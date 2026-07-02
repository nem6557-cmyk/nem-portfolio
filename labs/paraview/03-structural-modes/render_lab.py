"""PV-3: mode shapes as a visualization problem.

Rebuilds project 5's three-story steel frame in OpenSees, solves the
eigenproblem, and renders the first three lateral mode shapes as
warped, displacement-colored geometry through the VTK pipeline. The
numbers come from the live eigensolve; the undeformed frame ghosts
behind each mode. Periods print to RESULTS.txt for the site.
"""
import sys
from pathlib import Path
import numpy as np
import pyvista as pv

pv.OFF_SCREEN = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "project-5-opensees-pushover" / "src"))
import openseespy.opensees as ops
import run_pushover as p5

ASSETS = REPO / "site" / "assets"
BG = "#0e1626"

p5.build(braced=False)
lams = ops.eigen(3)
periods = [2 * np.pi / np.sqrt(l) for l in lams]
tags = sorted(ops.getNodeTags())
coords = {t: ops.nodeCoord(t) for t in tags}
modes = {m: {t: ops.nodeEigenvector(t, m) for t in tags} for m in (1, 2, 3)}
ops.wipe()

# frame connectivity from the tag scheme: 10*story + column
def edges():
    e = []
    for col in (1, 2):
        for s in range(p5.N_STORY):
            e.append((10 * s + col, 10 * (s + 1) + col))
    for s in range(1, p5.N_STORY + 1):
        e.append((10 * s + 1, 10 * s + 2))
    return e

idx = {t: i for i, t in enumerate(tags)}
lines = []
for a, b in edges():
    lines += [2, idx[a], idx[b]]

pl = pv.Plotter(off_screen=True, shape=(1, 3), window_size=(1740, 760),
                border=False)
for k, m in enumerate((1, 2, 3)):
    pl.subplot(0, k)
    pl.set_background(BG)
    base = np.array([[coords[t][0], 0.0, coords[t][1]] for t in tags])
    phi = np.array([[modes[m][t][0], 0.0, modes[m][t][1]] for t in tags])
    amp = 0.9 / np.abs(phi[:, 0]).max()
    warped = base + amp * phi
    ghost = pv.PolyData(base, lines=np.array(lines))
    mesh = pv.PolyData(warped, lines=np.array(lines))
    mesh["u"] = np.linalg.norm(amp * phi, axis=1)
    pl.add_mesh(ghost.tube(radius=0.03), color="#3a4a66", opacity=0.5)
    pl.add_mesh(mesh.tube(radius=0.07), scalars="u", cmap="turbo",
                show_scalar_bar=False)
    pl.add_text(f"mode {m}   T = {periods[m-1]:.3f} s",
                color="#dbe4f0", font_size=11, position="upper_edge")
    pl.camera_position = "xz"
    pl.camera.zoom(0.95)
shot = HERE / "pv3-modes.png"
pl.screenshot(shot)
pl.close()

import shutil
shutil.copy2(shot, ASSETS / "pv3-structural-modes.png")
summary = ("PV-3 eigensolve (unbraced frame): "
           + ", ".join(f"T{m}={periods[m-1]:.3f}s" for m in (1, 2, 3))
           + f"; mode-1 period matches project 5's reported "
             f"T1 = {periods[0]:.3f} s by construction (same model).\n")
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
