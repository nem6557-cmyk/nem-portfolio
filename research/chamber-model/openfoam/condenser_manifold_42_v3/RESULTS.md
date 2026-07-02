# 42-tube manifold v3 — solved results (simpleFoam, step 500, converged)

STEP-faithful geometry: tubes axis X (62.6mm, ID1.39), vertical top-fed manifolds at X=+-35,
Ø5 top ports at (X=+-35, Y=0). Water ~40 C, 4 L/min (6.667e-5 m^3/s).

## Headline numbers
- Mass balance: inlet 4000 mL/min, outlet 4001 mL/min  (closes exactly)
- Per-tube distribution: mean 98, min 82, max 126 mL/min, **CoV 10%** (uniform)
- Pressure drop inlet->outlet ~ 20 kPa
- Umax 4.28 m/s (in the Ø5 ports), mean ~1.0 m/s

## What it shows (figures/)
- per_tube_distribution.png: top-row tubes near centre-Y get the most flow (inlet port is
  top-centre of the manifold), tapering to the bottom rows and Y-edges. Smooth gradient, CoV 10%.
- sideview_velocity_fulllength.png: inlet manifold energised at top where the jet turns into the
  tubes; 4 tube rows carry steady ~1 m/s across the full 62.6mm; outlet manifold collects.
- pressure_along_length.png: inlet manifold ~14.5 kPa -> sharp entrance drop -> gradual ~1.4 kPa
  drop ALONG the tubes (narrow ID1.39 bores carry real resistance) -> dip at the Ø5 outlet port.

## Contrast with 33-tube
33-tube (centred axial port, ID3.137): bullseye maldistribution, CoV 131%, tubes hydraulically
invisible (drop all at the port). 42-tube (top-fed vertical manifolds, ID1.39): uniform CoV 10%,
tubes carry a measurable share of the drop. The manifold feed geometry governs distribution.

VTK in run42_results/VTK (open VTK/run42_500/... in ParaView).
