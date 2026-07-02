# Numerical model of the closed subcooled pool-boiling chamber

This document specifies the reduced-order ("gray-box") numerical model implemented in
`chamber_model.py` and `chamber_solver_single.py`. It is the model that produces the
boiling curves, the operating-point predictions, and the field reconstructions. It is a
lumped, correlation-based model, not a CFD code; the relationship to CFD is stated at the end.

---

## 1. Scope and philosophy

The model predicts, for a given chip heat flux `q''`, coolant inlet temperature `T_in`,
condenser geometry, and chip surface, the steady chamber operating point and chip
temperature:

    inputs:  q'' [W/cm^2], T_in [C], condenser (33/42/66-tube), chip (plain/micro), fluid
    outputs: T_sat [C], subcooling [K], chip surface temperature T_surf [C]

It is a gray box: mechanistic correlations carry the physics, and a small number of
constants are fitted to data. The constants are split into two classes, and that split is
the central design choice:

- **transferable** constants (the boiling surface coefficients `C_sf`) are fitted once and
  reused across every condenser geometry, because the boiling physics is a property of the
  chip surface, not the chamber;
- **chamber-specific** constants (the single-phase factor `NC` and the operating-point map
  coefficients) are fitted per condenser, because they encode condenser-dependent transport.

A model that needed a new `C_sf` per chamber would be a curve fit. One `C_sf` that works
across chambers is a physical statement, and it is what makes the model predictive for
untested geometries rather than merely descriptive.

Footprint convention throughout: chamber heat load `Q = q'' * A_foot`, with
`A_foot = 11.04 cm^2` (34.5 x 32 mm chip).

---

## 2. Fluid properties

All properties are evaluated at the local saturation temperature with CoolProp
(`props(T_sat)`): liquid and vapour density, latent heat `h_fg`, surface tension `sigma`,
liquid viscosity, conductivity, specific heat, thermal expansion coefficient, and
`Pr = mu c_p / k`. HFE-7000 properties are hardcoded from literature because the CoolProp
build lacks the fluid (`h_fg = 138 kJ/kg`, `sigma = 11 mN/m`, `T_sat ~ 34 C` at 1 atm).

---

## 3. Chip-side heat transfer

The chip dissipates `q''` by two parallel mechanisms whose fluxes add in quadrature. The
surface temperature is the root of

    q''  =  sqrt( q_nc(T_surf)^2  +  q_nb(T_surf)^2 )                              (1)

solved for `T_surf` by Brent's method on `[T_pool, T_sat + 160 K]`. Quadrature blending
gives a smooth transition through the onset of boiling without a switch.

### 3.1 Single-phase natural convection

Enhanced Churchill-Chu / McAdams over the chip, with `Delta T = T_surf - T_pool`:

    Ra = g * beta * Delta T * L^3 / (nu * alpha)
    Nu = 0.15 Ra^(1/3)   if Ra > 1e7 ,   else  0.54 Ra^(1/4)   (floored at 0.27 Ra^(1/4))
    q_nc = NC * Nu * k_l / L * Delta T                                            (2)

`L` is the chip length scale. `NC` is the per-chamber single-phase enhancement factor
(confined-geometry recirculation in the closed chamber), fitted per condenser:
`NC = 9.0` (33-tube), `3.5` (42-tube). It is a chamber property and is unchanged between
chip surfaces.

### 3.2 Nucleate boiling (Rohsenow)

With wall superheat `Delta T_sat = T_surf - T_sat`, and zero below saturation:

    q_nb = mu_l * h_fg * sqrt( g (rho_l - rho_v) / sigma )
           * ( c_pl * Delta T_sat / ( C_sf * h_fg * Pr_l^s ) )^3                  (3)

with `s = 1` (water). `C_sf` is the surface-fluid coefficient, the single fitted boiling
constant. Because `q_nb ~ Delta T_sat^3`, a smaller `C_sf` shifts the boiling curve to lower
superheat (a better-wetting / higher-nucleation surface). Calibrated values:

    C_sf (plain copper, ~2.5 um Ra)        = 0.0131
    C_sf (open microchannel)               = 0.0067

Both land on independently published values for these finishes (polished copper ~0.013;
a scored/rougher surface roughly half), which is external corroboration that (3) is
capturing surface physics, not absorbing chamber error.

### 3.3 Microchannel chip

The open-microchannel chip uses the same chamber machinery with two changes: a geometric
area-augmentation factor `A_r = 2.17` (wetted/footprint) multiplies both transport terms in
(1), and the microchannel `C_sf = 0.0067` replaces the plain value. `NC` is unchanged (it is
a chamber property). The fin/channel geometry is 381 um channel width, 400 um depth, 250 um
fin width.

### 3.4 Critical heat flux

Operationally, CHF is taken from measurement, not predicted:

    CHF (33-tube, plain) = 114 W/cm^2 ,   CHF (42-tube, plain) = 65 W/cm^2
    CHF (microchannel)   = CHF(plain) + 60 W/cm^2   (additive separated-flow increment)

A Kandlikar-2001 CHF correlation is included in code (`chf_kandlikar`) but is an
uncalibrated placeholder (placeholder orientation angle and subcooling coefficient) and is
not used for the operational CHF. **Open question:** in this closed chamber the 33-tube and
66-tube configurations reach similar CHF, which points to a chip surface-temperature ceiling
near 90 C rather than classic boiling burnout. Treating the measured ceiling as a true
burnout CHF would misrepresent the mechanism; this is flagged for resolution before any
journal claim.

---

## 4. Operating-point model (T_sat and subcooling)

The chip model needs `T_sat` and subcooling, which the condenser sets. Mechanistically the
condenser is **coolant-side limited**: the internal coolant flow is developing-laminar in
short tubes (`Re ~ 1000`), film condensation is near-ideal and negligible (2-3 mK/W), and the
condenser conductance improves as the whole system runs warmer (coolant viscosity falls and
the exposed condensing area grows with vapour inventory). The net result is that `T_sat`
tracks coolant inlet with a gain below unity, not 1:1.

This is realized as a calibrated per-chamber linear operating-point map:

    T_sat    = a * T_in + b * Q + c            (Q = q'' * A_foot, in watts)       (4)
    subcool  = max( d * T_in + e * Q + f , 0 )                                    (5)

`a` is the coolant gain, `b` an effective thermal resistance [K/W], `c` an offset.
Calibrated coefficients:

    33-tube:  (a,b,c) = (0.2618, 0.005994, 44.81)   (d,e,f) = (-0.6389, -0.006797, 40.75)
    42-tube:  (a,b,c) = (0.7098, 0.024088, 33.14)   (d,e,f) = (-0.2173, -0.000701, 19.62)

The 66-tube map is uncalibrated (no chamber data yet); from layout its open, tall 2 mm bank
should resemble the 33-tube (low gain, small slope).

The map is empirical and **does not contain coolant flow rate as a variable** (it was fitted
at the experimental flow rate). Flow-rate dependence is handled separately in Section 6.

---

## 5. Predictive chain

The full forward prediction (`chip_temp_from_geometry`) composes the pieces:

    q'', T_in, chamber, chip
        -> predict_operating(q'', T_in, chamber)        -> (T_sat, subcooling)     [eq 4,5]
        -> chip_surface_temp(q'', T_sat, subcooling, NC, chip)  -> T_surf          [eq 1-3]

A boiling curve is this chain swept over `q''` at fixed `T_in`. No measured operating
conditions are required as input; the chain predicts them.

---

## 6. Condenser hydraulics and the flow-rate model

For coolant flow rate `Q_lpm` through `N` tubes of inner diameter `ID`, length `L`:

    V  = (Q_lpm/N) / (pi/4 * ID^2)                         per-tube bulk velocity
    Re = rho V ID / mu
    Nu = 3.66 + 0.0668 (ID/L) Re Pr / ( 1 + 0.04 [ (ID/L) Re Pr ]^(2/3) )   (Hausen)  (6)
    h  = Nu k / ID
    R_coolant = 1 / (h * N pi ID L)                        coolant-side resistance

Hausen (6) is the developing-laminar, constant-wall-temperature Nusselt number; it is used
because the hydrodynamic entrance length `L_h = 0.05 Re ID` exceeds the tube length, so the
flow never fully develops (`L_h ~ 120-150 mm` vs `L ~ 63-95 mm`). Total condenser resistance
adds wall conduction and a small condensation-side term:

    R_total = R_coolant + ln(OD/ID)/(2 pi k_cu L N) + R_shell  ,  R_shell ~ 2.5 mK/W

Geometric resistances at the experimental flow rate: 17.3 mK/W (33-tube), 25.7 mK/W
(42-tube), 8.66 mK/W (66-tube, using an open-bank factor 0.78).

**Flow-rate effect.** Raising flow from 1.8 to 3.75 L/min raises `Re`, hence `Nu`, `h`, and
the conductance `UA = 1/R_total`, while heat-exchanger effectiveness `eps = 1 - exp(-UA/(m_dot
c_p))` falls (the classic trade-off: more flow, lower exit temperature rise, lower
effectiveness, but higher conductance). The net on the chamber is computed as a delta from the
validated 3.75 L/min baseline:

    h:        +29% (33-tube), +30% (42-tube)
    T_sat and chip temperature:  about -3.5 K at q'' = 40 W/cm^2

so higher flow lowers `T_sat` and chip temperature. The 42-tube buys higher `h` at much higher
pumping cost (its small bore gives `Delta P ~ 1500 Pa` vs `~ 100 Pa` for the 33-tube at
3.75 L/min). Absolute chamber temperatures remain anchored to the validated operating-point
map; the mechanistic model supplies only the flow-rate sensitivity.

---

## 7. Numerical methods

- Surface temperature: Brent root-find (`scipy.optimize.brentq`) on equation (1), bracket
  `[T_pool + eps, T_sat + 160 K]` (260 K for microchannel). Robust because the residual is
  monotonic in `T_surf`.
- Calibration: the operating-point coefficients (4)-(5) and `C_sf` are fitted by nonlinear
  least squares on the measured `(q'', T_in, T_sat, T_surf)` points. `C_sf` may be frozen to a
  literature value or fitted; the fitted value is reported because it lands on literature.
- Property caching keyed on rounded `T_sat` avoids repeated CoolProp calls in sweeps.

---

## 8. Calibration data

Calibrated on 261 measured points spanning two evaporator chips (plain ~2.5 um Ra;
open-microchannel), two condensers (33-tube, 42-tube), coolant inlets of 20/30/40/50 C, and
the full flux range to CHF. Reference apparatus: Shukla and Kandlikar, 2024 IEEE ITherm.

---

## 9. Validation and its limits

**In-sample fit.** The model reproduces the measured boiling curves to an overall chip-
temperature RMSE of 4.31 K (n = 261). By configuration: 33-tube plain 3.0 K, 42-tube plain
4.5 K, 33-tube micro 4.7 K, 42-tube micro 5.2 K. This is an in-sample residual: `C_sf` and the
operating-point map were fitted to these same points, so it confirms the model reproduces its
calibration data but is not by itself a blind prediction test.

**Out-of-sample evidence.** Three independent checks support predictive validity:
1. fitted `C_sf` values match published values for the same surface finishes (Section 3.2);
2. cross-chamber generalization: fitting `C_sf` independently on each condenser gives nearly
   the same value (plain 0.0130 for 33-tube, 0.0121 for 42-tube), so one boiling coefficient
   serves both geometries without per-chamber retuning (transferability);
3. leave-one-coolant-out cross-validation (hold out one coolant inlet temperature and predict
   it from the rest) gives a held-out RMSE of 4.95 K for the 33-tube and 9.03 K for the
   42-tube; this is out-of-sample for operating conditions.

So the 33-tube has demonstrated predictive skill; the 42-tube is weaker and its predictions
carry more uncertainty, consistent with its looser operating-point fit and noisier data. Note
the cross-validation withholds a coolant temperature, not a whole condenser; a held-out
condenser test waits on the 66-tube dataset.

**Reported limitations.**
- The operating-point map is empirical and chamber-specific; the 66-tube map is uncalibrated.
- CHF is measured, not predicted, and the burnout-vs-ceiling mechanism is unresolved.
- The model is steady-state and lumped; it returns temperatures, not spatial fields.
- Measurement uncertainty has not yet been quantified; this is a prerequisite for journal-
  level claims, not optional polish.

---

## 10. Relationship to CFD

This model is validated and fast but spatially lumped. The accompanying OpenFOAM case
(`interCondensatingEvaporatingFoam`) is the route to resolved temperature, velocity, and
pressure fields from first principles; it has been demonstrated to run on the true 42-tube
geometry but is not converged or validated, and a validated VOF boiling solution requires a
refined 3D mesh, calibrated phase-change coefficients, and HPC wall-clock. The field
reconstructions in this package map this validated reduced-order model onto the chamber
geometry for visualization; they are model-derived, not CFD solutions. The pressure
contours in particular are the thermodynamic saturation pressure plus hydrostatic head, not a
momentum-resolved field.

---

*Files:* `chamber_model.py` (self-contained: embedded data, geometry, calibration, solver,
figures), `chamber_solver_single.py` (the reduced-order model used by the field tools).
Reproduce all numbers with `python chamber_model.py`.
