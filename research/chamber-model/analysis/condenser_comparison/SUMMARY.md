# Condenser comparison — heat flux and surface temperature (matched conditions)

Compares 33-, 42-, and 66-tube condensers for the SAME microchannel chip, SAME 20C coolant
loop (Tin=28.7C at high load), SAME flow (62.5 g/s). Anchored to the measured 33-tube point
(178 W/cm2 @ 78C) AND the measured 42-tube point; the 66-tube is a geometry-based forecast.

## Method (based on the OpenFOAM condenser work)
- Coolant-side resistance from the validated developing-laminar correlation (Hausen Nu), per
  the chamber model. CFD per-tube distributions (CoV: 33=117%, 42=10%, 66=57%) characterise the
  internal flow.
- A coolant-side calibration factor phi is fit to BOTH measured condensers: phi_open=0.96 (set
  by the 33-tube, an open bundle) and phi_confined=1.15 (set by the 42-tube). The 66-tube is an
  open bundle, so it uses phi_open.
- R_cond -> Tsat via Tsat = Tin + q*A_foot*R_cond. Tsurf via the validated microchannel Rohsenow
  boiling curve. A_foot=11.04 cm2.

## Result
| quantity | 33-tube | 42-tube | 66-tube |
|---|---|---|---|
| coolant-side area Ai [cm2] | 309 | 115 | 355 |
| wall thickness [mm] | 0.81 | 0.89 | 0.10 |
| condenser resistance [mK/W] | 17.8 | 23.6 | 11.3 |
| Tsurf @ 178 W/cm2 [C] | 76.8 | 86.9* | 66.5 |
| max q'' @ 78C surface [W/cm2] | 185 | 143* | 272 |
| CHF measured [W/cm2] | 174 | 125 | >=174 (forecast) |
*42-tube hits CHF (125) before 178 W/cm2.

## Reading
- The 66-tube has the lowest condenser resistance: it has MORE coolant-side area than the
  33-tube (355 vs 309 cm2, from 66 small-bore tubes) and a much thinner wall (0.10 vs 0.81 mm).
  Both push R_cond down. At 178 W/cm2 it runs ~10C cooler than the 33-tube (66.5 vs 76.8C).
- Equivalently, at a fixed 78C surface it carries ~272 W/cm2 vs the 33-tube's ~185.
- The 42-tube is weakest: ~1/3 the coolant-side area, so it saturates the pool at high flux
  (data shows the 42 pool going to zero/negative subcooling) and crises at 125 W/cm2.
- CHF note: both measured condensers crisis near Tsurf~74-78C, which looks like a surface-
  temperature ceiling for this chip. If that holds, the cooler-running 66-tube reaches the
  ceiling at a much higher flux (upper end of the ~174-272 forecast band). If CHF is instead
  subcooling/burnout-limited, the gain is smaller. This is the open CHF-mechanism question;
  the 66-tube number is a forecast either way (no 66-tube data exists).

## Caveats
- Matched flow (62.5 g/s) loads the narrow-bore 42 and 66 with higher pressure drop than the
  33 (see manifold CFD); the 42's actual experiments ran at ~41 g/s.
- The 66-tube forecast assumes an open bundle (like the 33). If its 66 tubes are densely packed
  (more confined), R_cond would rise toward the 42's regime and the gains shrink.
