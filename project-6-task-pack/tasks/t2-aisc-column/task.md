# Task T2: Steel column, flexural buckling capacity (AISC 360-22, E3)

## Problem statement (what the model sees)

A pinned-pinned steel column buckles about its minor axis:

- gross area `A = 13,000 mm^2`, minor-axis radius of gyration `ry = 78 mm`
  (section properties are given; no shape-table lookup)
- effective length `Lc = 4.2 m` about the minor axis
- `Fy = 345 MPa`, `E = 200,000 MPa`
- factored axial demand `Pu = 3,000 kN`

Per AISC 360-22 Chapter E (E3, flexural buckling; the section is
nonslender), compute:

1. `lam` - governing slenderness `Lc/r` [-]
2. `Fe_MPa` - elastic buckling stress [MPa]
3. `Fcr_MPa` - critical stress per E3-2/E3-3 [MPa]
4. `phiPn_kN` - design compressive strength, `phi_c = 0.90` [kN]
5. `adequate` - boolean, `phiPn >= Pu`

Report a JSON object with exactly those keys.

## Why this task is well-posed

Single limit state by construction (properties given, minor axis
stated, nonslender stated), fully SI, and the inelastic/elastic branch
point (`Fy/Fe` vs 2.25) is exercised: this column lands on the
inelastic branch, so pattern-matching the Euler formula alone misses
`Fcr` by a wide margin while passing `Fe`.
