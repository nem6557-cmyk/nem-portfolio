# Refine -> calibrate -> run -> validate (HPC workflow)

This is the path from the working 3D demonstration case to a *validated* result.
None of steps 2-4 below can run in a single-core sandbox; they are HPC jobs. This
document specifies them so the campaign is reproducible.

## Scope and honesty
The base case (`../`) is a working 3D VOF + phase-change pipeline on the real
42-tube geometry, **not** a validated result. Its short, coarse, uncalibrated
fields carry non-physical spikes. The steps here are what turn it into a result
you can put in a paper. Do not report the demonstration fields as physical.

---

## 1. Refine the mesh (~0.1-0.3 mm near chip and tubes, snapping + layers)
`../system/snappyHexMeshDict` is set up for this: surface refinement level (3 4)
on the tubes (~0.125-0.25 mm), a feature level of 4, a refinement box over the
chip (level 4) and around the bundle/interface (level 3), feature **snapping on**,
and **5 prism layers** on the tubes and the heated floor.

Verified in the build sandbox (coarser variant, level (1 2)): snapping on all 42
tubes produces a complete body-fitted mesh, **299,656 cells, checkMesh "Mesh OK",
max skewness 1.57** — i.e. snapping does not produce the sliver-cell failure that
castellation-only was avoiding. Layer addition reached 100% cell addition and
99.9% face extrusion. The full (3 4) mesh is several million cells and is an HPC
build (the sandbox reached ~1.2M cells mid-refinement before its time limit).

On the cluster:
    blockMesh && surfaceFeatureExtract && snappyHexMesh -overwrite
    checkMesh   # require Mesh OK; tighten maxNonOrtho/skewness if needed
Tune `maxGlobalCells`, surface levels, and `nSurfaceLayers` for your node memory.

## 2. Calibrate the phase-change coefficients against measured data
The Lee-type `constant` model coefficients (coeffE evaporation, coeffC
condensation) are uncalibrated placeholders (1.0 / 0.1). Calibrate them against
the measured 42-plain boiling curve and CHF.

- Targets (from your data): `calibration/targets_42plain.json`,
  `calibration/validation_target_42plain.{png,csv}` — 64 measured (q'', Tsurf)
  points across coolant temperatures, measured CHF 65 W/cm^2.
- Heat-flux probe: `../system/chipHeatFlux` (coded functionObject) writes
  `chipHeatFlux.dat` = time, q''[W/m^2], q''[W/cm^2], Q[W] on the chip patch
  (phase-weighted conductivity). **Confirm it compiles against your build.**
- Driver: `calibration/calibrate_phase_change.py` runs a wall-temperature sweep
  per candidate (coeffE, coeffC), builds the simulated boiling curve, and
  minimises RMS misfit + a CHF turn-over penalty (Nelder-Mead).

      python calibrate_phase_change.py --targets targets_42plain.json \
          --template ../ --runner slurm --max-iter 25

  Each objective evaluation = one wall-T sweep = several full 3D solves. This is
  an HPC campaign, not an interactive call. The mapping is mesh-dependent;
  re-calibrate if the mesh changes.

## 3. Run to (quasi-)steady state
VOF boiling is inherently transient, so "steady" means a statistically
stationary, time-averaged state, not a frozen field.
- In `controlDict`: extend `endTime` well past the thermal/flow transient,
  keep `adjustTimeStep` with `maxCo 0.4`/`maxAlphaCo 0.4`, and add a
  `fieldAverage` functionObject over the stationary window for T, U, alpha.water.
- Judge stationarity from `chipHeatFlux.dat` (running mean of q'' flat to within
  noise) and a steady time-averaged liquid fraction.
- Parallel: `decomposePar` (scotch) -> `mpirun -np N interCondensatingEvaporatingFoam -parallel` -> `reconstructPar`.

## 4. Compare within measurement uncertainty
- Build the simulated boiling curve from the time-averaged chip q'' at each wall
  temperature and overlay it on `validation_target_42plain.png`.
- Validation passes only if the simulated curve lies **within the measurement
  uncertainty band**, point by point, and the turn-over matches CHF.
- The uncertainty band is **not yet quantified** — it is a prerequisite, not a
  formality. Propagate instrument and repeatability uncertainty
  (thermocouples, heat-flux/area, fluid properties) onto q'' and Tsurf first.
  Without that band, "agreement" is not defined.

---

## File map
    ../system/snappyHexMeshDict          refined mesh (snap + layers, 0.1-0.3 mm)
    ../system/chipHeatFlux               chip wall-heat-flux functionObject
    calibrate_phase_change.py            calibration orchestrator
    targets_42plain.json                 measured boiling-curve + CHF targets
    validation_target_42plain.png/.csv   validation reference (with tolerance note)
