# Task T1: Singly reinforced beam, flexural design check (ACI 318-19)

## Problem statement (what the model sees)

A simply supported rectangular reinforced-concrete beam has:

- width `b = 350 mm`, effective depth `d = 540 mm`
- concrete `f'c = 28 MPa` (normal weight)
- steel `fy = 420 MPa`, `Es = 200,000 MPa`
- tension reinforcement `As = 2,454 mm^2` (5 No. 25 bars, given as area;
  no bar-table lookup is required)
- factored moment demand `Mu = 460 kN-m`

Using ACI 318-19 (equivalent rectangular stress block, Sec. 22.2), compute:

1. `a_mm` - depth of the equivalent stress block [mm]
2. `eps_t` - net tensile strain in the extreme tension steel at nominal
   strength [-] (take `eps_cu = 0.003`)
3. `phi` - strength reduction factor per Table 21.2.2 (linear transition
   between compression- and tension-controlled; `eps_ty = fy/Es`)
4. `phiMn_kNm` - design flexural strength [kN-m]
5. `adequate` - boolean, `phiMn >= Mu`

Report answers in a JSON object with exactly those five keys, units as
given. Assume yielding steel and verify via `eps_t`; do not include
self-weight or any load recomputation.

## Why this task is well-posed

Every input is numeric and closed; no table lookups, no unit ambiguity
(all SI, units in key names), a single load case, and a boolean whose
truth follows deterministically from the numeric answers. The checker
tolerances are 1% relative on numeric fields, which is far wider than
any legitimate rounding path and far tighter than any conceptual error
(e.g., forgetting phi, using d instead of d - a/2, or mixing beta_1).
