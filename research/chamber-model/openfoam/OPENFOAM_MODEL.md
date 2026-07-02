# OpenFOAM CFD Model
## 3D VOF + phase-change simulation of the 42-tube subcooled pool-boiling chamber

Solver: `interCondensatingEvaporatingFoam` (OpenFOAM v1912)
Case: `openfoam/chamber42_3d/`
Scope: forward demonstration of the numerical pipeline on the real geometry. **Not a validated result.**

This document is the single reference for the CFD model. It consolidates the case
`README.md` and `calibration/REFINE_CALIBRATE_VALIDATE.md`. It is separate from
`model/NUMERICAL_MODEL.md`, which documents the Python gray-box reduced-order model;
the two are independent descriptions of the same physical chamber.

---

## 1. Status: what this is and is not

This is a working three-dimensional volume-of-fluid simulation with simultaneous
evaporation and condensation, built on the true 42-tube CAD geometry, that runs end
to end (mesh, solve, post-process). It is a **demonstration of the method, not a
result**:

- Short transient: 0.8 ms of physical time.
- Single core, coarse mesh: 74,044 staircased (castellation-only) cells.
- Uncalibrated phase-change coefficients (placeholders 1.0 / 0.1).
- The raw temperature and velocity fields carry non-physical spikes (T up to ~610 K,
  |U| up to ~36 m/s). The post-processor clamps these **for display only**; the
  clamp does not fix the underlying field, which is neither converged nor validated.

Do not report the demonstration fields as physical. The path to a result you can put
in a paper is the HPC campaign in Section 10, and it requires the measurement
uncertainty band (report Section "Measurement uncertainty") as a prerequisite.

---

## 2. What the ParaView / PyVista views actually show

The post-processor `postprocess_3d.py` uses PyVista, which reads the case through the
same OpenFOAM reader ParaView uses (it opens `case.foam`; it falls back to `foamToVTK`
output if the native reader is unavailable). It renders four views at the last time
step:

| View | Content | Is it geometry or solution? |
|------|---------|------------------------------|
| `view1_overview` | chamber outline + 42-tube bundle (`condenser` patch) + chip (`chip` patch) + liquid/vapour interface (`alpha.water = 0.5` isosurface) | **Geometry / domain** + interface |
| `view4_interface` | the `alpha.water = 0.5` interface coloured by height, tubes shown translucent | **Geometry / domain** + interface |
| `view2_temperature` | `T` on a vertical mid-plane (`y`-normal) slice | **Solution field**, display-clamped to 305-360 K |
| `view3_velocity` | `|U|` on the same slice | **Solution field**, display-clamped to the 95th percentile |

So, to answer the question directly: the overview and interface views **are** the
domain, the chamber box, the tube bundle, the chip, and the liquid surface, drawn from
the real mesh and patches. They are faithful. The temperature and velocity views are
the **simulated fields**, shown inside a clamped colour band because the unconverged
run produces non-physical extremes. They are the solver output, not a validated field,
and the clamp is cosmetic.

To reproduce the same in ParaView: open `case.foam`, go to the last time step, show the
`condenser` and `chip` patches plus a `Contour` of `alpha.water` at 0.5 for the
geometry; use a `Slice` (Y normal) coloured by `T` or `U` for the fields, and set your
own range to suppress the spikes.

---

## 3. Solver and governing equations

`interCondensatingEvaporatingFoam` is an incompressible two-phase (water / vapour) VOF
solver with a phase-change model that handles evaporation and condensation
simultaneously. Flow is laminar (`constant/turbulenceProperties: simulationType laminar`).

**Phase fraction (VOF) transport**, with interface compression term (`cAlpha = 1`) and
the phase-change source $\dot m$:

$$\frac{\partial \alpha}{\partial t} + \nabla\!\cdot(\mathbf{U}\alpha) + \nabla\!\cdot\big(\mathbf{U}_r\,\alpha(1-\alpha)\big) = \frac{\dot m}{\rho_l}$$

where $\alpha=$ `alpha.water` is the liquid fraction and $\mathbf{U}_r$ is the
compression velocity.

**Momentum** (single mixture field, with gravity and CSF surface tension):

$$\frac{\partial(\rho\mathbf{U})}{\partial t} + \nabla\!\cdot(\rho\mathbf{U}\mathbf{U}) = -\nabla p_{rgh} - (\mathbf{g}\!\cdot\!\mathbf{x})\nabla\rho + \nabla\!\cdot\boldsymbol{\tau} + \sigma\kappa\nabla\alpha$$

with mixture density $\rho = \alpha\rho_l + (1-\alpha)\rho_v$ and $p_{rgh} = p - \rho\,\mathbf{g}\!\cdot\!\mathbf{x}$.

**Energy** (temperature form, with the latent heat exchange at phase change):

$$\frac{\partial(\rho c_p T)}{\partial t} + \nabla\!\cdot(\rho c_p \mathbf{U} T) = \nabla\!\cdot(k_{\mathrm{eff}}\nabla T) - \dot m\, h_{fg}$$

**Phase-change mass transfer** (`constant` / Lee-type model). The volumetric mass
transfer rate is proportional to the local departure from saturation $T_{sat}$, with
separate coefficients for the two directions:

$$\dot m_e = C_E\,\alpha\,\rho_l\,(T - T_{sat}) \quad (T > T_{sat}, \text{ evaporation}), \qquad \dot m_c = C_C\,(1-\alpha)\,\rho_v\,(T_{sat} - T) \quad (T < T_{sat}, \text{ condensation})$$

The coefficients $C_E$ (`coeffE`) and $C_C$ (`coeffC`) have units $\mathrm{s^{-1}K^{-1}}$
and are the quantities calibrated against data (Section 10.2). In the demonstration
they are uncalibrated placeholders.

---

## 4. Domain and geometry

Chamber aligned so $x$ is width, $y$ is the tube axis, $z$ is height, gravity along $-z$.

| Item | Value |
|------|-------|
| Chamber box | 80 x 80 x 42 mm ($x \times y \times z$) |
| Condenser | 42 tubes, OD 3.175 mm, length 62.6 mm, at real CAD $(x,z)$ positions |
| Heated chip | 34.5 x 32 mm on the floor |
| Liquid fill | ~40% by volume ($z < 16.8$ mm); the bundle straddles the interface |
| Gravity | $(0, 0, -9.81)\ \mathrm{m/s^2}$ |

The tubes enter as an STL (`constant/triSurface/tubes.stl`) and become the `condenser`
patch via `snappyHexMesh`. The chip is cut from the floor as its own `chip` patch with
`topoSet` + `createPatch`. The initial liquid pool is set by `setFields`
(`alpha.water = 1` for $z < 16.8$ mm).

---

## 5. Mesh

| Mesh | How built | Cells | Notes |
|------|-----------|-------|-------|
| Base | `blockMesh`, 40 x 40 x 21 hex, grading 1 | 33,600 | ~2 mm uniform |
| **Demonstration** | `snappyHexMesh` castellation-only (no snapping) | **74,044** | staircased but robust for VOF; this is what the shipped `0/` fields and the demo views use |
| Verified intermediate | snapping on, surface level (1 2) | 299,656 | `checkMesh` "Mesh OK", max skewness 1.57, layers 100% added; proves snapping does not fail on the 42 tubes |
| Target (refined) | the shipped `snappyHexMeshDict` | several million | HPC build only |

The shipped `system/snappyHexMeshDict` is configured for the **refined** target, not
the demo: surface refinement level (3 4) on the tubes (~0.125-0.25 mm), feature level 4
(~0.125 mm at edges), a refinement box over the chip (level 4) and around the
bundle/interface (level 3), feature **snapping on**, and **5 prism layers** on the
tubes and the heated floor. This is the mesh for Section 10.1; on one core it does not
fit interactive limits.

---

## 6. Boundary and initial conditions

Saturation temperature $T_{sat} = 338$ K (65 C); `pDivU false`
(`constant/thermophysicalProperties`).

| Patch | `T` | `U` | `p_rgh` |
|-------|-----|-----|---------|
| `chip` | fixedValue 358 K (85 C, ~20 K superheat) | noSlip | fixedFluxPressure |
| `condenser` | fixedValue 305 K (32 C, ~33 K subcooling) | noSlip | fixedFluxPressure |
| `floor` | zeroGradient | noSlip | fixedFluxPressure |
| `walls` | zeroGradient | noSlip | fixedFluxPressure |
| `top` | zeroGradient | noSlip | fixedFluxPressure |

Internal fields: `T = 325` K, `U = 0`, `p_rgh = 0`, `alpha.water` from `setFields`.

These wall temperatures are **representative operating conditions for the
demonstration**, not a match to a specific measured point. The fixed $T_{sat} = 65$ C
also differs from the measured chamber saturation for 42-plain (49-54 C). Matching the
model to data is the job of the calibration step (Section 10.2), which compares the
**simulated boiling curve** to the measured one rather than fixing a single point.

---

## 7. Material properties

`constant/transportProperties`, two phases `(water vapour)`:

| Property | Water | Vapour | Unit |
|----------|-------|--------|------|
| $\rho$ | 980 | 0.30 | kg/m^3 |
| $\nu$ | 4.4e-7 | 4.0e-4 | m^2/s |
| $c_p$ | 4190 | 2030 | J/kg/K |
| $c_v$ | 4190 | 1500 | J/kg/K |
| $\kappa$ | 0.66 | 0.025 | W/m/K |
| $h_f$ (latent ref) | 0 | 2.35e6 | J/kg |

Surface tension $\sigma = 0.065$ N/m; turbulent Prandtl $Pr_t = 1.0$.

Phase-change coefficients (`constant/phaseChangeProperties`, `constant` model):
$C_C =$ `coeffC` $= 1.0$, $C_E =$ `coeffE` $= 0.1$ (units $\mathrm{s^{-1}K^{-1}}$).
**Uncalibrated placeholders, the single most important quantity to calibrate.**

---

## 8. Numerics and run control

`system/controlDict`:

| Setting | Value |
|---------|-------|
| application | `interCondensatingEvaporatingFoam` |
| endTime | 8e-4 s |
| deltaT | 1e-6 s (adjustable) |
| adjustTimeStep | yes, `maxCo 0.4`, `maxAlphaCo 0.4`, `maxDeltaT 5e-6` |
| writeInterval | 1e-4 s, ascii |

Discretization (`system/fvSchemes`): `ddt` Euler (first-order implicit); convection
`div(rhoPhi,U)` and `div(rhoPhi,T)` `linearUpwind`; `div(phi,alpha)` `vanLeer` with
`div(phirb,alpha)` `linear` interface compression; Laplacian `Gauss linear corrected`.
Linear solvers (`system/fvSolution`): `p_rgh` PCG/DIC, `alpha.water` MULES
(`MULESCorr yes`, `nAlphaCorr 2`, `cAlpha 1`), `T`/`U` smoothSolver. PIMPLE in PISO
mode (`nOuterCorrectors 1`, `nCorrectors 2`, `momentumPredictor no`, `pRefValue 1e5`).

For a validated run, the first-order/`linearUpwind` setup should be revisited (less
numerical diffusion, e.g. a limited higher-order or Crank-Nicolson blend) once the mesh
is refined and snapped.

---

## 9. Chip heat-flux probe

`system/chipHeatFlux` is a coded `functionObject` that integrates the conductive flux on
the `chip` patch using a phase-weighted conductivity
$k_{\mathrm{eff}} = \alpha\,k_w + (1-\alpha)\,k_v$ and writes `chipHeatFlux.dat` as
`time, q''[W/m^2], q''[W/cm^2], Q[W]`. This is the simulated boiling-curve signal used
by calibration and stationarity checks. It **could not be compile-tested in the build
sandbox**; confirm field names and `kappa` values against your build on the cluster.

---

## 10. Path to a validated result (HPC)

None of these steps runs in a single-core sandbox; they are HPC jobs. See
`calibration/REFINE_CALIBRATE_VALIDATE.md` for the long form.

1. **Refine the mesh** to 0.1-0.3 mm near the chip and tubes with snapping and prism
   layers (the shipped `snappyHexMeshDict`). On the cluster:
   `blockMesh && surfaceFeatureExtract && snappyHexMesh -overwrite && checkMesh` (require
   "Mesh OK"). The level (1 2) variant (299,656 cells) is the proof it meshes cleanly.

2. **Calibrate** $C_E, C_C$ against the measured 42-plain boiling curve and CHF.
   Targets: `calibration/targets_42plain.json` (64 measured $(q'', T_{surf})$ points,
   CHF 65 W/cm^2) and `validation_target_42plain.{csv,png}`. Driver:
   `calibration/calibrate_phase_change.py` runs a wall-temperature sweep per candidate
   $(C_E, C_C)$, builds the simulated boiling curve from `chipHeatFlux.dat`, and minimises
   RMS misfit plus a CHF turn-over penalty (Nelder-Mead). Each objective evaluation is
   several full 3D solves; the mapping is mesh-dependent, so re-calibrate if the mesh
   changes.

3. **Run to quasi-steady state.** VOF boiling is intrinsically transient, so "steady"
   means a statistically stationary, time-averaged state. Extend `endTime` past the
   transient, add a `fieldAverage` over the stationary window, judge stationarity from a
   flat running mean of `chipHeatFlux.dat`, and run in parallel
   (`decomposePar` -> `mpirun -np N ... -parallel` -> `reconstructPar`).

4. **Compare within measurement uncertainty.** Overlay the simulated boiling curve on
   the measured one; validation passes only if it lies inside the measurement
   uncertainty band point by point and the turn-over matches CHF. That band must be
   quantified first (report Section "Measurement uncertainty"): without it, "agreement"
   is undefined.

---

## 11. File map

| Path | Role |
|------|------|
| `README.md` | short case overview |
| `Allrun`, `Allrun.cluster` | build + solve drivers (local / cluster) |
| `system/blockMeshDict` | 80x80x42 mm base box, 33,600 cells |
| `system/snappyHexMeshDict` | refined snapped + layered mesh (HPC target) |
| `system/surfaceFeatureExtractDict` | tube edge features for snapping |
| `system/topoSetDict`, `createPatchDict` | cut the `chip` patch from the floor |
| `system/setFieldsDict` | initial 40% liquid fill |
| `system/controlDict`, `fvSchemes`, `fvSolution` | time control and numerics |
| `system/chipHeatFlux` | chip wall-heat-flux probe |
| `constant/transportProperties` | water/vapour properties, $\sigma$ |
| `constant/thermophysicalProperties` | $T_{sat}$ |
| `constant/phaseChangeProperties` | $C_E$, $C_C$ |
| `constant/g`, `turbulenceProperties` | gravity, laminar |
| `constant/triSurface/tubes.stl`, `tubes.eMesh` | 42-tube geometry |
| `0/{T,U,p,p_rgh,alpha.water}` | initial and boundary fields |
| `postprocess_3d.py` | PyVista four-view renderer |
| `calibration/` | refine/calibrate/validate workflow, targets, driver |

---

## 12. Reproduce the demonstration

```
# build + solve (local, coarse demo)
cd openfoam/chamber42_3d
./Allrun

# render the four views (headless)
xvfb-run -a python3 ../postprocess_3d.py . post
```

The result is the four PNG views of Section 2. They show a working pipeline on the real
geometry. They are not a validated simulation.
