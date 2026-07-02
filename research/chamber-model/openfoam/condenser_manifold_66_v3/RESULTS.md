# 66-tube manifold v3 — solved results (simpleFoam, step 500, converged)

Single-pass, SIMPLIFIED inlet/outlet (thin plenum across the tube face + Ø5 axial centreline feed).
Forecast geometry (no 66-tube validation data). Water ~40 C, 4 L/min.

## Headline numbers
- Mass balance: inlet 4000 mL/min, outlet ~3962 mL/min (closes to ~1%, post-proc integration)
- Per-tube: mean 63, min 26, max 249 mL/min, CoV 57%
- Pressure drop ~12 kPa mean inlet->outlet (local jet spikes higher); tubes ~0.6 kPa, rest at ports
- Umax ~4.0 m/s (Ø5 feed); mean ~0.5 m/s

## IMPORTANT - the CoV 57% is largely a SIMPLIFICATION ARTIFACT
The simplified thin plenum cannot spread the Ø5 centreline jet, so it plows straight into the
~3-4 central tubes (X~0, Z~7) at 200-249 mL/min, while the other ~60 tubes sit fairly uniform at
~50-60 and the edges starve to 26. The headline CoV is dominated by those few jet-hit tubes; the
"background" bundle is actually reasonably even.

The REAL manifolds are LOFTED diffusers (Ø5 hole expanding to the flush tube face). That loft exists
precisely to spread this jet across the tube face. Modelling the true loft would very likely cut the
CoV dramatically (plausibly toward the 42-tube's ~10%). So treat CoV 57% as the SIMPLIFIED-inlet
result, NOT a prediction of the real 66-tube apparatus. Building the loft is the clean next step.

## Figures (figures/)
- per_tube_distribution.png: centred jet over-feeds the middle tubes; bulk ~50-60, spikes to 249.
- velocity_plane_centreline_jet.png: the Ø5 jet hitting the central tubes (thin plenum, no room to spread).
- pressure_along_length.png: gentle ~0.6 kPa along the wide ID1.6 tubes; drop dominated by Ø5 outlet port.

VTK in run66_results/VTK.
