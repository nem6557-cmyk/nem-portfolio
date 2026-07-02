# Running the 3D chamber case for ParaView (single workstation)

Prereqs: ESI OpenFOAM v2512 sourced (`which interCondensatingEvaporatingFoam` resolves),
ParaView installed, and you are in this directory (`chamber42_3d/`).

The committed `system/snappyHexMeshDict` is the HPC production mesh (millions of cells, hours).
For a workstation, use the coarse variant via the scripts below (~300k cells, minutes).

## Option A -- resolved mesh only (fast; the strongest honest figure)
```sh
./mesh_coarse.sh
```
Builds blockMesh -> snappyHexMesh (coarse) -> chip patch -> checkMesh, and writes `case.foam`.
Open `case.foam` in ParaView. Colour by `cellZones`/patch, show the `condenser` (tube) surface,
slice to see refinement. This is the resolved 42-tube apparatus -- a real Part II figure.

## Option B -- mesh + short early-transient field
```sh
./run_coarse.sh            # endTime 0.0008 s (preset). Or: ./run_coarse.sh 0.005
```
Adds setFields (40% liquid fill) -> short solve -> `foamToVTK` -> `case.foam`.
Open `case.foam` (or the `VTK/` folder) in ParaView. Useful fields:
- `alpha.water`  : liquid (1) vs vapour (0); threshold or contour at 0.5 for the interface
- `T`            : temperature (chip 358 K, condenser 293 K)
- `U`            : velocity / developing plumes

HONEST SCOPE: at this mesh and these sub-second times the boiling is barely developed
(see paper Sec. 18 and the 2D findings). Option B is an early-transient visualisation of the
apparatus and initial fields, NOT a converged boiling result. Converged boiling is HPC-scale.

## ParaView open, two ways
- Native: `touch case.foam` (the scripts do this) then File > Open > case.foam.
- Portable VTK: `foamToVTK` (run_coarse.sh does this) writes a `VTK/` folder of `.vtm`/`.vtk`.

## Headless render (no GUI), optional
If you have `pvbatch`/`pvpython`, you can script PNG renders. The repo's
`postprocess_3d.py` is a starting point: `xvfb-run -a python3 postprocess_3d.py . post`.

## Driving this with Claude Code
Claude Code runs these on your machine directly: it executes the meshing/solver/VTK steps,
reads the logs, fixes any v2512 dictionary differences on the spot (e.g. surfaceFeatureExtract
vs surfaceFeatures), confirms checkMesh, and can script pvbatch renders. Point it at this
directory and ask it to run Option A first, confirm the mesh, then Option B if wanted.
