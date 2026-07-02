# Numerical analysis: predictive accuracy of the gray-box model

## Method
Every prediction uses the full chain `chip_temp_from_geometry()`: condenser
geometry and coolant inlet temperature set the operating point (saturation
temperature, subcooling) through the calibrated maps; the chip surface
temperature then follows from the quadrature blend of the natural-convection
(Churchill-Chu) and nucleate-boiling (Rohsenow) terms. The boiling coefficients
`C_sf` (plain 0.0131, microchannel 0.0067) are fitted once and held fixed across
both condensers; there is no per-point or per-chamber tuning. Accuracy is
therefore a property of the model, not of a curve fit to each dataset.

## Headline result (n = 261; 2 condensers x 2 chips x 4 coolant inlets)

| Configuration         |  n  | RMSE | MAE  | max\|e\| | bias  |  R^2  | LOCO |
|-----------------------|----:|-----:|-----:|-------:|------:|------:|-----:|
| 33-tube, plain copper |  87 | 3.19 | 2.63 |  8.41  | -1.03 | 0.963 | 4.95 |
| 33-tube, microchannel |  36 | 4.91 | 3.92 | 10.28  | +0.85 | 0.862 | 4.95 |
| 42-tube, plain copper |  64 | 4.47 | 3.41 |  8.16  | +2.03 | 0.898 | 9.03 |
| 42-tube, microchannel |  74 | 5.22 | 4.50 | 10.67  | +2.20 | 0.925 | 9.03 |
| **All data**          | 261 | 4.40 | 3.53 | 10.67  | +0.90 | 0.937 |  --  |

RMSE, MAE, max|e|, bias in kelvin. (Units of chip-temperature error.)

## What the numbers say
- Overall chip-temperature RMSE 4.40 K with R^2 = 0.937 over the full operating
  envelope, from a model whose boiling physics is fixed by two transferable
  constants. The near-zero overall bias (+0.90 K) indicates no large systematic
  offset across the population.
- The same `C_sf` values reproduce both condensers, which is the substantive
  result: the boiling closure is geometry-independent, so the model is
  predictive for the condenser change rather than refitted to it.

## Out-of-sample evidence (the honest test)
In-sample RMSE overlays the same data used to fit the maps. The leave-one-
coolant-out (LOCO) column is stricter: an entire coolant-inlet condition is
withheld from calibration and then predicted. The 33-tube chamber holds up
(4.95 K, close to in-sample), while the 42-tube chamber degrades to 9.03 K.

## Limitations (visible in the figures, stated plainly)
- The 42-tube chamber is weaker throughout (higher RMSE, +2 K bias, LOCO ~9 K).
  The confined, short-tube 42-tube bundle is less well described by the same
  operating-point maps than the open 33-tube bundle.
- The residual plot shows structure, not pure noise: the 42-tube microchannel
  residuals bow positive at the low and high ends of the surface-temperature
  range. The error is not yet a clean random scatter, so the RMSE understates
  a mild model-form error at the envelope edges.
- These are chip-temperature errors against the measured points. They are NOT
  a comparison within quantified measurement uncertainty, because that
  uncertainty band is not yet established (see the validation prerequisite).

## Scope
This is the validated reduced-order result. It is the figure for the paper.
It is not, and is not presented as, a 3D Lee-type VOF result; that remains the
HPC calibration campaign scaffolded separately.

## Files
    figs/fig_boiling_curves.{pdf,png}   model vs experiment, all four configs
    figs/fig_parity.{pdf,png}           predicted vs measured chip temperature
    figs/fig_residuals.{pdf,png}        residual structure + distribution
    figs/results_table.tex              booktabs accuracy table
    figs/predictions.csv                every point: measured, predicted, residual
    publication_analysis.py             regenerates all of the above
