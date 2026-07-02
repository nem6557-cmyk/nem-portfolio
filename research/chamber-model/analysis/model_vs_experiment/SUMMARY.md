# Model vs experiment — chip temperature comparison

Source: 261 measured points (33/42-tube x plain/micro, coolant 20-50 C) vs the validated
reduced-order gray-box model (pub_figs/predictions.csv).

## Overall fit
RMSE 4.34 K, MAE 3.48 K, R2 0.938, bias +0.89 K, 74% of points within 5 K.

## By configuration
| config         | N  | RMSE | bias  | R2    | <5K |
|----------------|----|------|-------|-------|-----|
| 33-tube plain  | 87 | 3.14 | -0.99 | 0.964 | 91% |
| 33-tube micro  | 36 | 4.82 | +0.88 | 0.867 | 67% |
| 42-tube plain  | 64 | 4.42 | +2.00 | 0.900 | 66% |
| 42-tube micro  | 74 | 5.17 | +2.16 | 0.927 | 65% |

33-tube fits best (plain R2 0.964, 91% within 5 K). 42-tube weaker and biased high (+2 K),
consistent with the leave-one-coolant-out cross-validation finding (33-tube generalises better).

## By coolant temperature
20 C: RMSE 4.90 bias +1.84 | 30 C: 5.29 +2.51 | 40 C: 3.48 +0.58 | 50 C: 3.50 -1.43.
Warmer coolant fits better; bias flips positive->negative as coolant warms.

## Figures
- parity_chip_temperature.png: predicted vs measured, within +-5 K, 33-tube tightest.
- boiling_curves_meas_vs_model.png: q vs wall superheat, measured (filled) vs model (open),
  per config per coolant temp - model captures the coolant-temperature family.
- residual_analysis.png: residuals vs q (no flux trend) + distribution (sigma 4.25 K).
- fit_table_by_config.png + model_vs_experiment.xlsx (predictions + stats sheets).

All in-sample fit on the validated configurations. 66-tube/HFE-7000 remain forecasts (no data).
