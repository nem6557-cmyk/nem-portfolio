# Chamber Model — Final Package

Closed subcooled pool-boiling chamber with a submerged tube-bundle condenser, for
data-center immersion cooling. A chip boils a pool; the vapor condenses on a partially
submerged tube bundle carrying single-phase coolant. This package contains the validated
reduced-order model, the OpenFOAM cases, the experimental data, and every analysis figure,
with one self-contained master Python script that runs the model.

RIT Thermal Analysis Laboratory.

---

## 1. Quick start

The model is one standalone file: `master_chamber_model.py`. It embeds its own experimental
data, so it runs from anywhere with no external files.

```bash
pip install -r requirements.txt

python master_chamber_model.py model          # metrics + model figures  -> ./figures/
python master_chamber_model.py figures        # publication boiling curves + error analysis -> ./pub_figs/
python master_chamber_model.py postprocess <case_dir> <out_dir>   # render 3D OpenFOAM fields (PyVista)
python master_chamber_model.py calibrate --help                   # VOF phase-change calibration (HPC)
```

Expected headline from `figures` (this is the validated result):

```
ALL DATA                 261   RMSE 4.34   MAE 3.48   max|e| 10.60   bias +0.89   R2 0.938
Leave-one-coolant-out held-out RMSE:  33-tube 4.87 K,  42-tube 9.09 K
```

Every function in the script is importable, e.g. `from master_chamber_model import surface_temp, condenser_resistance`.

---

## 2. What is in this package

```
master_chamber_model.py     THE model. Standalone, four subcommands, embedded data.
requirements.txt            Python dependencies.

data/                       Experimental data and model reference outputs
  experimental_data.json      261 measured points (also embedded in the script)
  Novec_Microchannel_uncertainty.xlsx, Plain_Chip_data_older_condenser.xlsx
  model_predictions.csv       model output for all points (parity / residuals)
  results_table.tex           per-configuration accuracy table (LaTeX)
  cfd_tube_positions.json     per-tube centroid coordinates for all three condensers

openfoam/                   CFD cases (see openfoam notes below)
  condenser_manifold_33_FINISHED/   single-phase coolant manifold, 33-tube (validated baseline)
  condenser_manifold_42_v3/         single-phase coolant manifold, 42-tube (uniform feed)
  condenser_manifold_66_v3/         single-phase coolant manifold, 66-tube (simplified feed)
  chamber42_2d/, chamber42_3d/      VOF phase-change demonstrations (UNCONVERGED, see scope)
  THREE_WAY_COMPARISON.md           reconciles the three manifold inlet models

geometry/                   CAD: STEP, DXF, and dimensioned PDF drawings for all three condensers

analysis/                   Studies and figures
  condenser_comparison/       33 vs 42 vs 66 thermal comparison (the main result set)
  model_vs_experiment/        parity, boiling curves, residuals vs the 261 points
  condenser_study/            tube-position extraction and per-tube distribution study

figures/                    Model-generated figures (from `model` / `figures`)
pub_figs/                   Publication figure set (parity, boiling curves, residuals) + CSV/LaTeX

paper/                      Integrated paper (PDF + LaTeX + figures)
  condenser_pool_boiling_paper.pdf
  extended_52page/            longer working write-up

docs/                       Flowchart maps (physics + numerical) and legacy/reference code
  legacy_code/                earlier MATLAB-era scaffold and the pre-consolidation modules
```

---

## 3. The system and the model

Three condenser geometries, two chips, two fluids.

| Condenser | tubes | OD / ID (mm) | wall (mm) | length (mm) | status |
|---|---|---|---|---|---|
| 33-tube | 33 | 4.76 / 3.14 | 0.81 | 95 | validated baseline |
| 42-tube | 42 | 3.175 / 1.39 | 0.89 | 62.6 | validated |
| 66-tube | 66 | 2.0 / 1.8 | 0.10 | 95 | forecast (no experimental data) |

Chips: plain copper (2.5 um Ra) and open microchannel (381 um wide, 400 um deep, 250 um fin).
Fluids: water and HFE-7000. Coolant inlet 20/30/40/50 C; liquid fill 40/60/80 percent.

The model is a gray-box reduced-order network: a mechanistic physics backbone (Rohsenow nucleate
boiling with a microchannel area term, natural convection, developing-laminar internal convection,
wall conduction, film condensation) with a small set of globally fitted, geometry-independent
constants. It is calibrated against the full experimental matrix, not per point.

Validated accuracy over 261 points: RMSE 4.34 K, R-squared 0.938, bias +0.89 K. Fitted boiling
coefficients C_sf = 0.0131 (plain) and 0.0067 (microchannel) transfer across both chambers.
Measured CHF (microchannel): 174 W/cm2 (33-tube), 125 W/cm2 (42-tube).

---

## 4. OpenFOAM notes

**Meshes are gzipped.** To save space the large `.msh` files are stored as `*.msh.gz`. Before
meshing a case, `gunzip` it (for example `gunzip openfoam/condenser_manifold_42_v3/fluid_42_v3.msh.gz`),
or regenerate it with the case's `build_manifold_*.py` script. Each case has a `README.md` and an
`Allrun`.

**Manifold cases (single-phase, validated use).** These resolve the coolant distribution and the
pressure budget inside each condenser. Solved with `simpleFoam` (laminar, water, 4 L/min) to the
mesh-limited plateau. Per-tube flow non-uniformity (coefficient of variation): 33-tube 117 percent
(centred-port bullseye), 42-tube 10 percent (top-fed, uniform), 66-tube 57 percent (a simplified
single-pass feed, an artifact of the centreline jet; the production diffuser would distribute more
evenly). Key finding: distribution is set by the feed geometry and is a weak lever on chip
temperature; pressure drop is set by the bore size.

**Chamber VOF cases (`chamber42_*`).** Three-dimensional volume-of-fluid phase-change demonstrations
with `interCondensatingEvaporatingFoam`. These are UNCONVERGED demonstrations, not validated results.
A converged result needs mesh refinement, Lee-coefficient calibration against the measured boiling
curve and CHF, and convergence verification.

**Environment.** Built with ESI OpenFOAM (gmsh mm geometry, scaled to metres with
`transformPoints -scale '(0.001 0.001 0.001)'`, MSH v2.2). The `calibrate` subcommand drives a
phase-change coefficient sweep on a cluster.

---

## 5. Condenser comparison (analysis/condenser_comparison/)

Heat flux and chip surface temperature for the three condensers under matched conditions
(microchannel chip), anchored to the measured 33-tube point (178 W/cm2 at 78 C, 20 C loop) and the
measured 42-tube point. The 66-tube is a geometry-based forecast.

- `boiling_curves_three_condensers.png`, `comparison_table.png` — 20 C loop. Coolant-side resistance
  17.8 / 23.6 / 11.3 mK/W (33 / 42 / 66). The 66-tube has more coolant-side area than the 33-tube
  (355 vs 309 cm2, from many small-bore tubes) and a thin wall, so it runs about 10 C cooler at
  178 W/cm2; the 42-tube saturates the pool and is weakest.
- `comparison_40C_boiling.png`, `comparison_20C_vs_40C_table.png` — 40 C loop. The chamber saturation
  temperature self-regulates to ~62 C, so the warm loop mainly spends the pool subcooling: the chip
  runs ~6 C hotter at the same flux. The weak 42-tube instead drives saturation to ~96 C.
- `flow_boiling_coolant_scenario.png` — a forward-looking scenario. If the secondary coolant
  flow-boiled inside the tubes, the internal resistance (the bottleneck) collapses and the chip
  temperature falls to a floor set by the external film condensation, about 55-58 C. The external
  condensation coefficient is the least-characterized term and is shown as a band.

`SUMMARY.md` in that folder documents the method, the two-anchor calibration, and the caveats.

---

## 6. Scope and honesty

This package distinguishes four kinds of result and never conflates them:

- **Validated**: the reduced-order model against the 261 measured points, and the 33-tube and
  42-tube condensers.
- **In-sample fit**: the global boiling and resistance constants are fitted to the full matrix.
- **Forecast**: anything for the 66-tube (no experimental data exists), and the flow-boiling scenario.
- **Unconverged CFD**: the chamber VOF cases are demonstrations, not validated solutions.

Open items before journal submission: measurement uncertainty quantification; a 66-tube dataset for
leave-one-chamber-out validation; formalizing the CHF mechanism (surface-temperature ceiling vs
classical burnout); and, if VOF is to be a primary contribution, a full converged calibration campaign.

---

## 7. Requirements

Python 3.10+ with the packages in `requirements.txt` (numpy, scipy, matplotlib, CoolProp; pyvista
and vtk only for the `postprocess` subcommand). OpenFOAM (ESI) and gmsh are needed only to run or
re-mesh the CFD cases; the model itself needs neither.
