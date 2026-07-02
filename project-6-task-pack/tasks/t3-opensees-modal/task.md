# T3: Modal analysis of a two-story shear building (OpenSees)

## Problem

A two-story shear building is idealized as a lumped-mass chain:

- story 1 lateral stiffness: k1 = 25,000 kN/m
- story 2 lateral stiffness: k2 = 18,000 kN/m
- floor mass, each level:   m  = 20,000 kg

Build the model in OpenSees (or OpenSeesPy), run an eigenvalue
analysis, and report the two natural periods and the fundamental mode
shape ratio.

Work in SI base units (N/m and kg). Mixing kN/m with kg is the classic
failure here and moves both periods by a factor of about 31.6.

## Deliverable

Write `answer.json` with exactly these fields:

```json
{
  "T1_s": 0.0,
  "T2_s": 0.0,
  "phi_ratio": 0.0
}
```

- `T1_s`: fundamental (longest) period, seconds
- `T2_s`: second-mode period, seconds
- `phi_ratio`: |u_roof / u_first| in the fundamental mode (report the
  absolute value; mode-shape scaling does not matter, the ratio does)

## Grading

Machine-checked against an independent closed-form eigensolution
(the checker never runs OpenSees). Relative tolerance 0.5% per field:
T1_s 40 pts, T2_s 30 pts, phi_ratio 30 pts.
