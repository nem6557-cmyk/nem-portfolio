# 3D pool-boiling chamber, 42-tube condenser (OpenFOAM VOF + phase change)

A 3D volume-of-fluid case with phase change for the closed subcooled pool-boiling
chamber with the partially submerged 42-tube condenser bundle.
Solver: `interCondensatingEvaporatingFoam` (OpenFOAM v1912).

## Geometry and conditions
- Chamber 80 x 80 x 42 mm (x width, y tube axis, z height; gravity -z).
- 42 condenser tubes, OD 3.175 mm, length 62.6 mm, at the real CAD (x,z) positions.
- Heated chip 34.5 x 32 mm on the floor.
- Liquid fill ~40% by volume (z < 16.8 mm); the bundle straddles the interface.
- BCs: chip wall T = 358 K (superheated, boiling), condenser walls T = 305 K
  (subcooled, condensing), saturation TSat = 338 K. Water / vapour properties and a
  constant-coefficient phase-change model (coeffC, coeffE) are in `constant/`.

## Run
Source your OpenFOAM environment, then `./Allrun`. The mesh is built by
`blockMesh` + `snappyHexMesh` in castellation-only mode (no snapping), which
produces a staircased but robust mesh for VOF; the chip patch is cut from the
floor with `topoSet` + `createPatch`.

## Post-process
`postprocess_3d.py` (PyVista) reads the case and renders four views: a geometry
+ liquid-interface overview, a temperature slice, a velocity slice, and the
liquid/vapour interface coloured by height.
    pip install pyvista
    xvfb-run -a python3 postprocess_3d.py . post      # headless
    python3 postprocess_3d.py . post                  # with a display

## What this is, and is NOT
This is a working 3D pipeline on the real geometry, not a validated result.
It is a short (0.8 ms), single-core, coarse (74k-cell staircased) transient with
uncalibrated phase-change coefficients. The raw temperature and velocity fields
carry non-physical hot-spot and parasitic-velocity spikes (T to ~610 K, |U| to
~36 m/s); the post-processor clamps these for display only.

To turn this into a validated simulation:
1. refine to ~0.1-0.3 mm near the chip and tubes, add prism layers, enable snapping;
2. calibrate coeffC / coeffE against the measured boiling curve and CHF;
3. run to steady state on HPC (this is days of wall time, not a sandbox run);
4. compare against the data within the measurement uncertainty.

## Refine / calibrate / validate (HPC)
See `calibration/REFINE_CALIBRATE_VALIDATE.md` for the path to a validated result:
refined snapped+layered mesh, phase-change calibration against the measured boiling
curve and CHF, run-to-steady, and comparison within measurement uncertainty.
