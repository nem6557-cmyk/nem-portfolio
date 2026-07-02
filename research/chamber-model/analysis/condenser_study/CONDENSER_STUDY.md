# Condenser parametric study — 33 / 42 / 66 tube (real geometry)

Reduced-physics comparison of the three condenser bundles, with tube positions and
sizes read directly from the CAD in `../geometry/`. Coolant water, 4 L/min total,
40 C inlet, condensing at 12 kPa (T_sat 49.4 C). Reproduce with:

    cd ../scripts_archive && python3 condenser_compare_3way.py

This is an analytical pipeline (Hagen-Poiseuille tube hydraulics + a verified
condensing-mode condenser solver), NOT OpenFOAM CFD. Full numbers in
`comparison_results.txt`; geometry in `tube_positions.json`; figures in `figures/`.

## Geometry (extracted from STEP)
| design  | file                          | tubes | OD/ID/L (mm)        | layout   |
|---------|-------------------------------|-------|---------------------|----------|
| 33-tube | CFD_Next_Gen.step             | 33    | 4.76 / 3.137 / 95   | open     |
| 42-tube | Heat_Exchanger_Design_3.step  | 42    | 3.175 / 1.39 / 62.6 | confined (validated) |
| 66-tube | Full_Assembly_..._66_Tubes    | 66    | 2.0 / 1.6 / 95      | open (next-gen) |

## Hydraulics & thermal (4 L/min, common reference conditions)
| metric                 | 33-tube | 42-tube | 66-tube |
|------------------------|--------:|--------:|--------:|
| coolant flow area mm^2 |  255.1  |   63.7  |  132.7  |
| tube velocity m/s      |  0.261  |  1.046  |  0.502  |
| Reynolds               |  1246   |  2209   |  1221   |
| pressure drop/tube Pa  |  52.7   |  708.2  |  389.6  |
| pumping power mW       |  3.52   |  47.21  |  25.97  |
| external area cm^2     |  469    |  262    |  394    |
| condensation HTC W/m2K |  42195  |  42589  |  46347  |
| bank condensing duty W |  444    |  352    |  684    |

Hydraulic note: the 42-tube runs hardest on the coolant side — smallest bores give
the highest velocity (~1 m/s, Re ~2200 near transition) and by far the largest
per-tube pressure drop (708 Pa). The 66-tube buys the most condensing duty (684 W)
by adding area and velocity, at ~7x the 33-tube pumping power.

## The key finding: geometry does not explain the measured confinement penalty
The reduced-order model calibrates a layout factor f = R_effective / R_geometric
against the boiling data: **33-tube f = 0.78 (measured), 42-tube f = 1.63 (measured),
66-tube f = 0.78 (assumed, forecast only)**.

- The confined 42-tube's effective condenser resistance sits ~63% ABOVE its geometric
  (developing-laminar) value; the open 33/66 bundles sit ~22% BELOW theirs.
- This penalty is **not** captured by any per-tube geometric metric. The 42-tube is
  not even the most tightly pitched (pitch/OD 1.64 vs 1.31 for 33-tube), yet it carries
  the penalty. See `figures/layout_factor_vs_geometry.png`.

Interpretation (speculative, the trend you can defend): the confinement penalty is a
chamber-level effect — restricted condensate drainage and pool circulation around a
bundle that fills more of the chamber — rather than a tube-spacing or area effect.
That is exactly the mechanism a CFD study would resolve and the analytical model can
only carry as an empirical factor.

## Where CFD adds value next (single-phase, workstation-tractable)
1. Coolant manifold + tube-array internal flow (simpleFoam): test whether the inlet
   header distributes flow evenly across the bundle, or whether inertial maldistribution
   starves tubes — a 3D effect the equal-split assumption above cannot see.
2. Pool-side drainage/circulation (eventually two-phase): the actual mechanism behind
   the f = 1.63 penalty.
The geometry to build these is now in `../geometry/`.
