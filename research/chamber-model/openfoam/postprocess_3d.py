#!/usr/bin/env python3
"""
Post-process the 3D subcooled pool-boiling chamber OpenFOAM case
(solver: interCondensatingEvaporatingFoam) with PyVista.

Renders four 3D views of the boiling field at the latest time step:
  view1_overview      chamber + tube bundle + chip + liquid/vapour interface
  view2_temperature   temperature on a vertical mid-plane slice
  view3_velocity      velocity magnitude on a vertical mid-plane slice
  view4_interface     the liquid/vapour interface (alpha.water = 0.5), coloured by height

Usage
-----
    python postprocess_3d.py [CASE_DIR] [OUT_DIR]

Headless (no display attached), e.g. on a cluster login node:
    xvfb-run -a python postprocess_3d.py [CASE_DIR] [OUT_DIR]

Requires: pyvista, numpy   (pip install pyvista)
Reads the case directly via the OpenFOAM reader; if that is unavailable it
falls back to the output of `foamToVTK` (the VTK/ folder in the case).

NOTE on physical validity: the temperature and velocity fields are clamped for
display because this short, coarse, uncalibrated run carries non-physical
hot-spot and parasitic-velocity spikes. The clamping is visualization only; it
does not fix the underlying field, which is not converged or validated.
"""
import os
import sys
import glob
import numpy as np
import pyvista as pv

CASE = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "."
os.makedirs(OUT, exist_ok=True)

pv.OFF_SCREEN = True
pv.global_theme.background = "white"
pv.global_theme.font.color = "black"

T_CLAMP = (305.0, 360.0)   # K; physical band (condenser 305 K, chip 358 K)
SLICE_NORMAL = "y"         # cut through the tube-axis mid-plane


def load_latest(case):
    """Return (internal_mesh, {patch_name: mesh}, time_label) for the latest time."""
    foam = os.path.join(case, "case.foam")
    try:
        open(foam, "a").close()
        r = pv.OpenFOAMReader(foam)
        r.set_active_time_value(r.time_values[-1])
        m = r.read()
        internal = m["internalMesh"]
        bnd = m["boundary"]
        patches = {n: bnd[n] for n in bnd.keys()}
        return internal, patches, f"{r.time_values[-1]:.2e} s"
    except Exception:
        vtms = sorted(glob.glob(os.path.join(case, "VTK", "*_*.vtm")),
                      key=lambda f: int(f.split("_")[-1].split(".")[0]))
        if not vtms:
            raise FileNotFoundError("No case.foam readable and no VTK/ output found. "
                                    "Run `foamToVTK` in the case first.")
        m = pv.read(vtms[-1])
        internal = m["internal"]
        bnd = m["boundary"]
        patches = {n: bnd[n] for n in bnd.keys()}
        return internal, patches, vtms[-1].split("/")[-1]


def add_outline(p, mesh):
    p.add_mesh(mesh.outline(), color="black", line_width=1)


def iso_camera(p):
    p.camera_position = "iso"
    p.camera.azimuth = 25
    p.camera.elevation = 12
    p.camera.zoom(1.25)


def main():
    internal, patches, tlabel = load_latest(CASE)
    tubes = patches.get("condenser")
    chip = patches.get("chip")
    pts = internal.cell_data_to_point_data()          # point data for contouring

    # --- view 1: geometry + liquid interface overview ---
    iface = pts.contour([0.5], scalars="alpha.water")
    p = pv.Plotter(off_screen=True, window_size=(1100, 950))
    add_outline(p, internal)
    if tubes is not None:
        p.add_mesh(tubes, color="#aeb4bf", smooth_shading=True)
    if chip is not None:
        p.add_mesh(chip, color="#c0392b")
    if iface.n_points:
        p.add_mesh(iface, color="#2c7fb8", opacity=0.55, smooth_shading=True)
    p.add_text(f"chamber + 42-tube bundle + liquid interface   ({tlabel})",
               font_size=10, color="black")
    iso_camera(p)
    p.screenshot(os.path.join(OUT, "view1_overview.png"))
    p.close()

    # --- view 2: temperature on a vertical slice ---
    sl = internal.slice(normal=SLICE_NORMAL)
    p = pv.Plotter(off_screen=True, window_size=(1100, 760))
    p.add_mesh(sl, scalars="T", cmap="inferno", clim=T_CLAMP,
               scalar_bar_args=dict(title="T [K]  (clamped)", color="black"))
    if tubes is not None:
        p.add_mesh(tubes.slice(normal=SLICE_NORMAL), color="black", line_width=2)
    p.add_text("temperature, mid-plane slice", font_size=10, color="black")
    p.view_xz()
    p.camera.zoom(1.3)
    p.screenshot(os.path.join(OUT, "view2_temperature.png"))
    p.close()

    # --- view 3: velocity magnitude on a vertical slice ---
    sl = internal.slice(normal=SLICE_NORMAL)
    umag = np.linalg.norm(sl["U"], axis=1)
    sl["|U|"] = np.clip(umag, 0, np.percentile(umag, 95))
    p = pv.Plotter(off_screen=True, window_size=(1100, 760))
    p.add_mesh(sl, scalars="|U|", cmap="viridis",
               scalar_bar_args=dict(title="|U| [m/s]  (clamped)", color="black"))
    if tubes is not None:
        p.add_mesh(tubes.slice(normal=SLICE_NORMAL), color="white", line_width=2)
    p.add_text("velocity magnitude, mid-plane slice", font_size=10, color="black")
    p.view_xz()
    p.camera.zoom(1.3)
    p.screenshot(os.path.join(OUT, "view3_velocity.png"))
    p.close()

    # --- view 4: liquid interface coloured by height ---
    iface = pts.contour([0.5], scalars="alpha.water")
    p = pv.Plotter(off_screen=True, window_size=(1100, 950))
    add_outline(p, internal)
    if tubes is not None:
        p.add_mesh(tubes, color="#d8dce3", opacity=0.45, smooth_shading=True)
    if iface.n_points:
        iface["height [mm]"] = iface.points[:, 2] * 1e3
        p.add_mesh(iface, scalars="height [mm]", cmap="ocean", smooth_shading=True,
                   scalar_bar_args=dict(title="height [mm]", color="black"))
    p.add_text("liquid / vapour interface  (alpha.water = 0.5)",
               font_size=10, color="black")
    iso_camera(p)
    p.screenshot(os.path.join(OUT, "view4_interface.png"))
    p.close()

    print(f"wrote 4 views ({tlabel}) to {OUT}")


if __name__ == "__main__":
    main()
