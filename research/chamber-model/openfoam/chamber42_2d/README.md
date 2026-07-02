# chamber42_2d — 2D phase-change demonstration (workstation-scale)

A **2D cross-section** of the 42-tube chamber for `interCondensatingEvaporatingFoam`
(OpenFOAM v1912/ESI). Its job is to produce **real, converged 2D fields** and a
**simulated boiling curve** so the Lee phase-change coefficients can be calibrated
against the measured 42-tube / plain-copper data, at a cost that runs on a desktop
rather than an HPC cluster.

## What this is, and is not
- **Mesh:** `blockMesh` only, one cell thick in *y* (empty front/back ⇒ 2D). The chip is a
  native floor patch via a 3-block *x* split (left-floor / chip / right-floor); no
  `snappyHexMesh`, no STL, no `topoSet`/`createPatch`. This is deliberately robust and
  fully reproducible.
- **Condenser is idealised** as the cold top surface at the bundle-top height (z = 24 mm,
  held at the coolant temperature). The **resolved 42-tube bundle is the 3D framework's
  domain** (`../chamber42_3d`); resolving 42 circular tubes in 2D would need `snappyHexMesh`,
  whose isotropic refinement breaks a one-cell-thick mesh.
- **2D is a demonstration.** Bubbles are infinite cylinders in 2D and the Lee coefficient
  interacts with interface cell size, so the **calibrated 2D coefficients do not transfer
  quantitatively to 3D**. They verify the pipeline and give a converged cross-section.

## Operating point (42-tube / plain / 20 °C coolant)
- Saturation `TSat = 322 K` (49 °C), the measured chamber saturation at this condition
  (`constant/thermophysicalProperties`).
- Condenser/coolant surface `T = 293 K` (20 °C); chip `T` swept over the measured Tsurf range
  (default 358 K, varied by the calibrator).
- Liquid fill to z = 16.8 mm (40 %); domain 80 mm (x) × 24 mm (z).
- Chip footprint x ∈ [22.75, 57.25] mm (34.5 mm, 11.04 cm²).
Set `TSat` and the condenser temperature to the measured conditions of whatever
configuration you calibrate; the values above are for 42-plain / 20 °C.

## Workflow (on the workstation, via Claude Code)
1. **Base run + mesh sanity**
   ```
   ./Allrun            # blockMesh, checkMesh, setFields, interCondensatingEvaporatingFoam
   ```
2. **Check stationarity** (is the run long enough to read a boiling-curve point?)
   ```
   python calibration/post_convergence.py chipHeatFlux.dat --tail 0.3
   ```
   Extend `endTime` in `system/controlDict` if the running mean of q'' has not levelled.
3. **Render fields** (T, alpha.water, |U|, p_rgh on the x-z plane)
   ```
   python calibration/post_contours.py .
   ```
4. **Calibrate the Lee coefficients** against the measured curve + CHF
   ```
   python calibration/calibrate_lee_2d.py --runner local --max-iter 15
   ```
   Nelder-Mead on (coeffE, coeffC). coeffE is the primary boiling-branch knob; coeffC
   mainly affects the condensing side. Writes `calibrated_coeffs.json`.
5. **Overlay CFD vs experiment**
   ```
   python calibration/post_overlay.py --runs cal_runs --targets calibration/targets_42plain.json
   ```

## Cost and parallelism
Each objective evaluation runs one solve **per probe wall temperature** (default 6:
48–85 °C) to quasi-stationarity. The probe cases are **independent** and can run in
parallel across cores/nodes; the Nelder-Mead outer loop is sequential. For a quick
pipeline check, reduce `PROBE_TWALL_C` to 3 points and `--max-iter` to ~6, or run a
single (coeffE, coeffC) pair by calling `simulate_curve` directly. Each 2D solve can
itself be decomposed (`decomposePar` + `mpirun`) if desired.

## Return contract (bring these back to fold into the paper)
- `calibrated_coeffs.json` — fitted (coeffE, coeffC) and final objective.
- `chipHeatFlux.dat` from the base run and from each `cal_runs/*Tw*` case (q'' histories).
- `convergence.png` — stationarity evidence for at least one representative solve.
- `fields_2d.png` — the converged T / alpha.water / |U| / p_rgh cross-section.
- `cfd_vs_experiment_42plain.png` — simulated vs measured boiling curve.

## Requirements
OpenFOAM v1912 (ESI) with `interCondensatingEvaporatingFoam`; Python with numpy, scipy,
matplotlib, and (for contours) pyvista.
