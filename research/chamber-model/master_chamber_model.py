#!/usr/bin/env python3
"""
================================================================================
 master_chamber_model.py
 Closed subcooled pool-boiling chamber with a submerged tube-bundle condenser
 Consolidated analysis code -- RIT Thermal Analysis Laboratory
================================================================================

ONE FILE, FOUR TOOLS. This consolidates the canonical pipeline built across the
project. Run a tool from the command line, or import any function.

  python master_chamber_model.py model              # reproduce metrics + model figures
  python master_chamber_model.py figures            # publication boiling curves + error analysis
  python master_chamber_model.py postprocess C O    # render 3D OpenFOAM fields (PyVista) from case C to dir O
  python master_chamber_model.py calibrate [opts]   # phase-change calibration orchestrator (HPC)

Sections:
  A  VALIDATED THERMAL MODEL   gray-box reduced-order model. Churchill-Chu natural
                               convection + Rohsenow nucleate boiling (quadrature
                               blend), calibrated geometry-independent C_sf, empirical
                               operating-point maps, Hausen condenser hydraulics.
                               Calibration re-derived from data; predictive validation
                               (overall chip-temp RMSE 4.40 K; leave-one-coolant-out
                               4.95 K 33-tube / 9.03 K 42-tube); 66-tube and HFE-7000
                               forecasts. Requires CoolProp, scipy, numpy, matplotlib.
  B  PUBLICATION ANALYSIS      boiling curves (model vs experiment), parity, residual
                               structure + distribution, LaTeX results table, CSV.
  C  3D OPENFOAM POST-PROCESS  PyVista rendering of the interCondensatingEvaporatingFoam
                               VOF case (overview, temperature/velocity slices,
                               liquid/vapour interface). Requires pyvista (optional).
  D  PHASE-CHANGE CALIBRATION  orchestrator that calibrates the Lee-type coeffC/coeffE
                               against the measured boiling curve + CHF. Each evaluation
                               is a full 3D solve: this drives an HPC campaign, it does
                               not run interactively.

NOTE ON SCOPE. Sections A-B are the validated reduced-order result (the figures for
the paper). Sections C-D are the 3D-CFD route, which is a scaffold requiring HPC
calibration and converged runs; its sandbox output is an unconverged demonstration,
not a validated result, and is labelled as such.

The OpenFOAM solver itself (interCondensatingEvaporatingFoam) is a compiled C++
application configured by the text dictionaries in the accompanying openfoam/ case;
it is not Python and is not part of this file.
"""

# ---- shared / optional imports -------------------------------------------------
try:
    import pyvista as pv          # optional: only Section C needs it
except Exception:
    pv = None


################################################################################
#  SECTION A  -  VALIDATED THERMAL MODEL
################################################################################
"""
================================================================================
 chamber_model.py
 Reduced-order predictive thermal model of a closed subcooled pool-boiling
 chamber with a submerged tube-bundle condenser.  Single self-contained file:
 it embeds the experimental data, the geometry, the calibrated constants, the
 physics, the calibration, the validation/analysis, the 66-tube and HFE-7000
 predictions, and regenerates every methods/results figure.

 Author : [Author Name], Thermal Analysis Laboratory, RIT
 Run    : python chamber_model.py        (writes PNG figures to ./figures/)
 Deps   : numpy, scipy, matplotlib, CoolProp
          pip install numpy scipy matplotlib CoolProp

 Parameter STATUS (kept explicit on purpose):
   C_sf (plain/micro)  CALIBRATED, TRANSFERABLE boiling coefficients
   area  (micro)       GEOMETRIC area augmentation (Cooke-Kandlikar)
   F_nc                CALIBRATED, GEOMETRY-SPECIFIC single-phase factor
   CHF                 MEASURED anchor (micro = plain + additive increment)
   operating-point     CALIBRATED per chamber (coolant-side-limited condenser)
   66-tube / HFE-7000  PREDICTIONS under stated assumptions (no data yet)
================================================================================
"""
import base64, gzip, json
import numpy as np

# ---- SECTION 1: embedded experimental data (gzip+base64 of opdata.json) ----
_DATA_B64 = (
    "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"
    "AfxT4qqW0AAA"
)
def _sanitize(opdata):
    """Drop placeholder/corrupted log rows (Tsat sentinel ~1 C, null-flow stubs).
    These survive in the raw export; clean_experimental_data.py fixes the on-disk
    JSON. Real points have Tsat >= 49 C, so Tsat > 5 cleanly separates them."""
    keep = lambda p: (p.get("Tsat", 0) or 0) > 5.0 and not (
        p.get("flow") is None and p.get("q", 0) < 2.0)
    return {k: {t: [p for p in rows if keep(p)] for t, rows in series.items()}
            for k, series in opdata.items()}

OPDATA = _sanitize(json.loads(gzip.decompress(base64.b64decode(_DATA_B64))))

# ---- SECTION 2: CAD-extracted condenser tube centers [mm] ----
C33_COORDS = np.array([[6.054545453082483e-05, -6.454545454545439], [16.749794045454536, -3.204545454545439], [27.91639404545454, 3.045454545454561], [11.166727045454536, 0.04545454545456096], [-33.49993945454546, -6.454545454545439], [6.054545453082483e-05, 6.545454545454561], [-16.750005954545465, 3.045454545454561], [-27.91660595454546, 3.045454545454561], [-22.333272954545464, 6.545454545454561], [-22.333272954545464, 0.04545454545456096], [-5.583405954545462, 3.045454545454561], [-16.750005954545465, -3.204545454545439], [5.583194045454533, -3.204545454545439], [33.50006054545453, 6.545454545454561], [22.33339404545454, 0.04545454545456096], [-11.16660595454546, -6.454545454545439], [11.166727045454536, -6.454545454545439], [33.50006054545453, -6.454545454545439], [33.50006054545453, 0.04545454545456096], [16.749794045454536, 3.045454545454561], [5.583194045454533, 3.045454545454561], [6.054545453082483e-05, 0.04545454545456096], [-11.16660595454546, 6.545454545454561], [-33.49993945454546, 0.04545454545456096], [-33.49993945454546, 6.545454545454561], [-27.91660595454546, -3.204545454545439], [-11.16660595454546, 0.04545454545456096], [-5.583405954545462, -3.204545454545439], [11.166727045454536, 6.545454545454561], [22.33339404545454, 6.545454545454561], [27.91639404545454, -3.204545454545439], [-22.333272954545464, -6.454545454545439], [22.33339404545454, -6.454545454545439]])
C42_COORDS = np.array([[-23.399999999997647, 22.087499999993703], [-18.199999999997647, 22.087499999995405], [-12.999999999997646, 22.087499999996705], [-7.799999999997676, 22.087499999998002], [-2.5999999999976655, 22.087499999999004], [2.5999999999992944, 22.087500000000002], [7.799999999999294, 22.087500000000002], [12.999999999999254, 22.087500000000002], [18.199999999999253, 22.087500000000002], [25.999999999999254, 17.587500000000002], [23.399999999999253, 22.087500000000002], [20.799999999999255, 17.587500000000002], [15.599999999999254, 17.587500000000002], [10.399999999999254, 17.587500000000002], [5.199999999999294, 17.587500000000002], [-7.02011151018307e-13, 17.587500000000002], [-5.200000000000706, 17.587500000000002], [-10.400000000000746, 17.587500000000002], [-15.600000000000746, 17.587500000000002], [-20.800000000000747, 17.587500000000002], [-26.000000000000746, 17.587500000000002], [-23.399999999997647, 13.087499999993703], [-18.199999999997647, 13.087499999995403], [-12.999999999997646, 13.087499999996703], [-7.799999999997676, 13.087499999998004], [-2.5999999999976655, 13.087499999999004], [2.5999999999992944, 13.087500000000004], [7.799999999999294, 13.087500000000004], [12.999999999999254, 13.087500000000004], [18.199999999999253, 13.087500000000004], [25.999999999999254, 8.587500000000004], [23.399999999999253, 13.087500000000004], [20.799999999999255, 8.587500000000004], [15.599999999999254, 8.587500000000004], [10.399999999999254, 8.587500000000004], [5.199999999999294, 8.587500000000004], [-7.02011151018307e-13, 8.587500000000004], [-5.200000000000706, 8.587500000000004], [-10.400000000000746, 8.587500000000004], [-15.600000000000746, 8.587500000000004], [-20.800000000000747, 8.587500000000004], [-26.000000000000746, 8.587500000000004], [-23.399999999997647, -22.087499999993696], [-18.199999999997647, -22.087499999995398], [-12.999999999997646, -22.087499999996698], [-7.799999999997676, -22.087499999997995], [-2.5999999999976655, -22.087499999998997], [2.5999999999992944, -22.087499999999995], [7.799999999999294, -22.087499999999995], [12.999999999999254, -22.087499999999995], [18.199999999999253, -22.087499999999995], [25.999999999999254, -17.587499999999995], [23.399999999999253, -22.087499999999995], [20.799999999999255, -17.587499999999995], [15.599999999999254, -17.587499999999995], [10.399999999999254, -17.587499999999995], [5.199999999999294, -17.587499999999995], [-7.02011151018307e-13, -17.587499999999995], [-5.200000000000706, -17.587499999999995], [-10.400000000000746, -17.587499999999995], [-15.600000000000746, -17.587499999999995], [-20.800000000000747, -17.587499999999995], [-26.000000000000746, -17.587499999999995], [-23.399999999997647, -13.087499999993696], [-18.199999999997647, -13.087499999995396], [-12.999999999997646, -13.087499999996696], [-7.799999999997676, -13.087499999997997], [-2.5999999999976655, -13.087499999998997], [2.5999999999992944, -13.087499999999997], [7.799999999999294, -13.087499999999997], [12.999999999999254, -13.087499999999997], [18.199999999999253, -13.087499999999997], [25.999999999999254, -8.587499999999997], [23.399999999999253, -13.087499999999997], [20.799999999999255, -8.587499999999997], [15.599999999999254, -8.587499999999997], [10.399999999999254, -8.587499999999997], [5.199999999999294, -8.587499999999997], [-7.02011151018307e-13, -8.587499999999997], [-5.200000000000706, -8.587499999999997], [-10.400000000000746, -8.587499999999997], [-15.600000000000746, -8.587499999999997], [-20.800000000000747, -8.587499999999997], [-26.000000000000746, -8.587499999999997]])

# ============================================================================
# SECTION 3  -  CALIBRATED CONSTANTS  (status labels are load-bearing)
# ============================================================================
G = 9.81
A_FOOT = 11.04          # chip footprint [cm^2];  Q[W] = q''[W/cm^2] * A_FOOT
K_CU   = 400.0          # copper conductivity [W/m K]

# --- chip boiling coefficients (geometry-independent, TRANSFERABLE) ---
C_SF_PLAIN = 0.0131     # CALIBRATED  Rohsenow C_sf, water / polished Cu (lit 0.0128-0.0130)
C_SF_MC    = 0.0067     # CALIBRATED  open-microchannel C_sf (~ scored Cu 0.0068)
AREA_MC    = 2.17       # GEOMETRIC   microchannel wetted/footprint area augmentation
CHF_INC_MC = 60.0       # MEASURED    additive microchannel CHF increment [W/cm^2]

# --- per-chamber single-phase factor (GEOMETRY-SPECIFIC, does not transfer) ---
NC_FACTOR = {"33": 9.0, "42": 3.5}

# --- measured CHF [W/cm^2]  (micro = plain + additive increment) ---
CHF = {"33": {"plain": 114, "micro": 174},
       "42": {"plain": 65,  "micro": 125}}

# --- calibrated operating-point maps:  T_sat = a*T_in + b*Q + c  [C] ---
#                                       subcool = d*T_in + e*Q + f  [K] ---
OP_TSAT = {"33-tube": (0.2618, 0.005994, 44.81),
           "42-tube": (0.7098, 0.024088, 33.14)}
OP_SUB  = {"33-tube": (-0.6275, -0.006221, 40.1427),   # re-derived on clamped subcooling (>=0)
           "42-tube": (-0.2359,  0.000221, 20.2469)}

# --- condenser geometry (66-tube has CAD but NO experimental data yet) ---
GEOM = {
    "33-tube": dict(N=33, ID=3.14e-3, OD=4.76e-3, L=95e-3,   mdot_gps=78,   layout="open"),
    "42-tube": dict(N=42, ID=1.39e-3, OD=3.175e-3, L=62.6e-3, mdot_gps=36,   layout="confined"),
    "66-tube": dict(N=66, ID=1.8e-3,  OD=2.0e-3,  L=95e-3,   mdot_gps=78,   layout="open"),
}
OPEN_FACTOR = 0.78      # measured real/ideal condenser-resistance factor for open bundles
# Effective (real) pool->coolant resistance = geometric coolant-side * layout factor.
# 0.78 (open) is the high-flux real/ideal ratio backed out from 33-tube water AND
# HFE-7000 runs; 1.63 (confined) from 42-tube water; 0.78 transferred to 66-tube (open).
RCOND_LAYOUT = {"33-tube": OPEN_FACTOR, "42-tube": 1.63, "66-tube": OPEN_FACTOR}

OUT = "figures"         # output directory for figures

# ============================================================================
# SECTION 4  -  FLUID PROPERTIES
# ============================================================================
from CoolProp.CoolProp import PropsSI

_pc = {}
def props(Tsat_c, fluid="Water"):
    """Saturated liquid/vapor properties, cached."""
    key = (round(Tsat_c, 1), fluid)
    if key in _pc:
        return _pc[key]
    T = Tsat_c + 273.15
    p = dict(rho_l=PropsSI("D", "T", T, "Q", 0, fluid), rho_v=PropsSI("D", "T", T, "Q", 1, fluid),
             hfg=PropsSI("H", "T", T, "Q", 1, fluid) - PropsSI("H", "T", T, "Q", 0, fluid),
             sigma=PropsSI("I", "T", T, "Q", 0, fluid), mu_l=PropsSI("V", "T", T, "Q", 0, fluid),
             k_l=PropsSI("L", "T", T, "Q", 0, fluid), cp_l=PropsSI("C", "T", T, "Q", 0, fluid),
             beta=PropsSI("ISOBARIC_EXPANSION_COEFFICIENT", "T", T, "Q", 0, fluid))
    p["Pr"] = p["mu_l"] * p["cp_l"] / p["k_l"]
    _pc[key] = p
    return p

def coolant(Tc=30.0):
    """Single-phase water coolant properties at atmospheric pressure."""
    T = Tc + 273.15
    return dict(rho=PropsSI("D", "T", T, "P", 101325, "Water"), mu=PropsSI("V", "T", T, "P", 101325, "Water"),
                k=PropsSI("L", "T", T, "P", 101325, "Water"), cp=PropsSI("C", "T", T, "P", 101325, "Water"))

# HFE-7000 (Novec 7000) literature properties at ~40 C  (CoolProp lacks this fluid)
HFE_PROPS = dict(mu_l=3.8e-4, hfg=138e3, rho_l=1375.0, rho_v=9.0, sigma=0.011, cp_l=1320.0, Pr=6.9)

# ============================================================================
# SECTION 5  -  CORRELATIONS
# ============================================================================
L_CHIP = 8.3e-3         # chip characteristic length A/P (34.5 x 32 mm)

def q_natural_convection(T_surf, T_pool, p, NC, L=L_CHIP):
    """Enhanced McAdams / Churchill-Chu single-phase term [W/m^2]."""
    dT = max(T_surf - T_pool, 1e-9)
    nu = p["mu_l"] / p["rho_l"]; al = p["k_l"] / (p["rho_l"] * p["cp_l"])
    Ra = G * p["beta"] * dT * L ** 3 / (nu * al)
    Nu = 0.15 * Ra ** (1 / 3.) if Ra > 1e7 else 0.54 * Ra ** 0.25
    Nu = max(Nu, 0.27 * Ra ** 0.25)
    return NC * Nu * p["k_l"] / L * dT

def q_nucleate_boiling(T_surf, T_sat, p, C_sf, s=1.0):
    """Rohsenow nucleate-boiling term [W/m^2]; zero below saturation. s=1 water, 1.7 others."""
    dsup = T_surf - T_sat
    if dsup <= 0:
        return 0.0
    return p["mu_l"] * p["hfg"] * (G * (p["rho_l"] - p["rho_v"]) / p["sigma"]) ** 0.5 * \
           (p["cp_l"] * dsup / (C_sf * p["hfg"] * p["Pr"] ** s)) ** 3

def hausen_nu(Re, Pr, Di, L):
    """Developing-laminar internal-flow Nusselt number (Hausen)."""
    Gz = (Di / L) * Re * Pr
    return 3.66 + 0.0668 * Gz / (1 + 0.04 * Gz ** (2 / 3.))

# ============================================================================
# SECTION 6  -  SOLVER  (chip surface temperature + predictive chain)
# ============================================================================
from scipy.optimize import brentq, least_squares

CHIPS = {"plain": dict(area=1.00, C_sf=C_SF_PLAIN), "micro": dict(area=AREA_MC, C_sf=C_SF_MC)}

def surface_temp(q_wcm2, T_sat, subcooling, NC, C_sf, area=1.0, fluid="Water", s=1.0, hfe=None):
    """Solve q'' = sqrt(q_nc^2 + q_nb^2) for chip surface temperature [C]."""
    T_pool = T_sat - subcooling
    p = HFE_PROPS if hfe else props(T_sat, fluid)
    if hfe:  # HFE has no beta in this property set; natural convection is minor near CHF
        q = q_wcm2 * 1e4
        f = lambda Ts: area * q_nucleate_boiling(Ts, T_sat, p, C_sf, s) - q
        try:
            return brentq(f, T_sat + 1e-6, T_sat + 200)
        except ValueError:
            return T_sat
    q = q_wcm2 * 1e4
    f = lambda Ts: np.hypot(area * q_natural_convection(Ts, T_pool, p, NC),
                            area * q_nucleate_boiling(Ts, T_sat, p, C_sf, s)) - q
    for top in (260, 500, 1000):
        try:
            return brentq(f, T_pool + 1e-9, T_sat + top)
        except ValueError:
            continue
    return T_sat + 200.0   # fallback when a trial bracket cannot be closed

def chip_surface_temp(q_wcm2, T_sat, subcooling, NC, chip="plain", fluid="Water"):
    c = CHIPS[chip]
    return surface_temp(q_wcm2, T_sat, subcooling, NC, c["C_sf"], c["area"], fluid)

def predict_operating(q_wcm2, T_in_C, chamber):
    """Predict (T_sat, subcooling) from coolant inlet + heat flux using the calibrated map."""
    Q = q_wcm2 * A_FOOT
    a, b, c = OP_TSAT[chamber]; d, e, f = OP_SUB[chamber]
    return a * T_in_C + b * Q + c, max(d * T_in_C + e * Q + f, 0.0)

def chip_temp_from_geometry(q_wcm2, T_in_C, chamber, NC, chip="plain"):
    """Full predictive chain: geometry + coolant inlet + flux -> chip surface temp [C]."""
    T_sat, sub = predict_operating(q_wcm2, T_in_C, chamber)
    return chip_surface_temp(q_wcm2, T_sat, sub, NC, chip=chip)

def condenser_resistance(chamber, Tc=30.0):
    """Geometric coolant-side condenser resistance (developing-laminar) [K/W]."""
    g = GEOM[chamber]; c = coolant(Tc); mdot = g["mdot_gps"] / 1000.0
    V = (mdot / c["rho"]) / (g["N"] * np.pi / 4 * g["ID"] ** 2)
    Re = c["rho"] * V * g["ID"] / c["mu"]; Pr = c["mu"] * c["cp"] / c["k"]
    Nu = hausen_nu(Re, Pr, g["ID"], g["L"]); hi = Nu * c["k"] / g["ID"]
    Ai = np.pi * g["ID"] * g["L"] * g["N"]
    Rwall = np.log(g["OD"] / g["ID"]) / (2 * np.pi * K_CU * g["L"] * g["N"])
    return dict(Re=Re, Nu=Nu, hi=hi, R=1 / (hi * Ai) + Rwall)

def effective_condenser_resistance(chamber, Tc=30.0):
    """Effective pool->coolant resistance [K/W] = geometric coolant-side * layout factor.
    Single source for the 66-tube forecast, the HFE estimate, and the condenser figure,
    replacing the previously hard-coded 13.5/42.0 mK/W constants."""
    return condenser_resistance(chamber, Tc)["R"] * RCOND_LAYOUT[chamber]

# ============================================================================
# SECTION 7  -  DATA HANDLING + CALIBRATION (re-derive constants from data)
# ============================================================================
def _valid(p):
    return (p["q"] >= 2.0 and p["Tin"] >= 5.0 and p["Tsat"] > p["Tin"] + 1
            and p.get("Tsurf") is not None and p.get("Tliq") is not None)

def points(gk=None, chip=None):
    out = []
    for g in ([gk] if gk else ["33", "42"]):
        for ch in ([chip] if chip else ["plain", "micro"]):
            for t, pl in OPDATA[f"{g}_{ch}"].items():
                for p in pl:
                    if _valid(p):
                        out.append(dict(gk=g, chip=ch, t=t, q=p["q"], Q=p["q"] * A_FOOT,
                                        Tin=p["Tin"], Tsat=p["Tsat"], sub=max(p["Tsat"] - p["Tliq"], 0.0),
                                        Tliq=p["Tliq"], Tsurf=p["Tsurf"]))
    return out

def rmse(a, b):
    a, b = np.asarray(a), np.asarray(b); return float(np.sqrt(np.mean((a - b) ** 2)))

def fit_csf(gk, chip):
    """Re-derive the chip boiling coefficient from data (least squares on surface temp)."""
    pp = points(gk, chip); area = CHIPS[chip]["area"]; NC = NC_FACTOR[gk]
    def res(c):
        return [surface_temp(p["q"], p["Tsat"], p["sub"], NC, c[0], area) - p["Tsurf"] for p in pp]
    return float(least_squares(res, [0.01], bounds=([0.003], [0.03])).x[0])

def fit_operating_maps(gk):
    """Re-derive (a,b,c) and (d,e,f) from data by multilinear least squares."""
    pp = points(gk)
    X = np.array([[p["Tin"], p["Q"], 1.0] for p in pp])
    aT = np.linalg.lstsq(X, np.array([p["Tsat"] for p in pp]), rcond=None)[0]
    aS = np.linalg.lstsq(X, np.array([p["sub"] for p in pp]), rcond=None)[0]
    return tuple(aT), tuple(aS)

# ============================================================================
# SECTION 8  -  VALIDATION + ANALYSIS
# ============================================================================
def predictive_rmse():
    """End-to-end chip-temperature RMSE (geometry + boundary conditions only)."""
    pp = points()
    pred = [chip_temp_from_geometry(p["q"], p["Tin"], f"{p['gk']}-tube", NC_FACTOR[p["gk"]], p["chip"]) for p in pp]
    meas = [p["Tsurf"] for p in pp]
    per = {}
    for g in ["33", "42"]:
        for ch in ["plain", "micro"]:
            sub = [(pr, p["Tsurf"]) for pr, p in zip(pred, pp) if p["gk"] == g and p["chip"] == ch]
            per[f"{g}-{ch}"] = rmse([s[0] for s in sub], [s[1] for s in sub])
    return rmse(pred, meas), per

def leave_one_coolant_out(gk, chip=None):
    """Refit operating maps on the whole chamber minus one coolant inlet, then score
    the held-out points. With chip=None this is the per-chamber LOCO; pass a chip to
    get the per-configuration held-out RMSE (maps still fit on the full chamber)."""
    pp = points(gk); temps = sorted(set(p["t"] for p in pp)); pr = []; me = []
    for t in temps:
        tr = [p for p in pp if p["t"] != t]
        te = [p for p in pp if p["t"] == t and (chip is None or p["chip"] == chip)]
        if not te:
            continue
        X = np.array([[p["Tin"], p["Q"], 1.0] for p in tr])
        aT = np.linalg.lstsq(X, np.array([p["Tsat"] for p in tr]), rcond=None)[0]
        aS = np.linalg.lstsq(X, np.array([p["sub"] for p in tr]), rcond=None)[0]
        for p in te:
            Tsat = aT @ [p["Tin"], p["Q"], 1.0]; sub = max(aS @ [p["Tin"], p["Q"], 1.0], 0.0)
            pr.append(chip_surface_temp(p["q"], Tsat, sub, NC_FACTOR[gk], p["chip"])); me.append(p["Tsurf"])
    return rmse(pr, me)

def sensitivity():
    """Mean |dT_surf| for +/-10% on each constant, over all points."""
    pp = points()
    def pred(csfS=1, fncS=1, aS=1, bS=1, cS=1, arS=1):
        out = []
        for p in pp:
            a, b, c = OP_TSAT[f"{p['gk']}-tube"]; d, e, f = OP_SUB[f"{p['gk']}-tube"]
            Tsat = a * aS * p["Tin"] + b * bS * p["Q"] + c * cS
            sub = max(d * p["Tin"] + e * p["Q"] + f, 0.0)
            base = CHIPS[p["chip"]]; area = base["area"] * (arS if p["chip"] == "micro" else 1.0)
            out.append(surface_temp(p["q"], Tsat, sub, NC_FACTOR[p["gk"]] * fncS, base["C_sf"] * csfS, area))
        return np.array(out)
    nom = pred()
    res = {}
    for name, hi, lo in [("c offset", dict(cS=1.1), dict(cS=0.9)), ("a gain", dict(aS=1.1), dict(aS=0.9)),
                         ("C_sf", dict(csfS=1.1), dict(csfS=0.9)), ("b slope", dict(bS=1.1), dict(bS=0.9)),
                         ("F_nc", dict(fncS=1.1), dict(fncS=0.9)), ("A_r", dict(arS=1.1), dict(arS=0.9))]:
        res[name] = 0.5 * (np.mean(np.abs(pred(**hi) - nom)) + np.mean(np.abs(pred(**lo) - nom)))
    return res

# ============================================================================
# SECTION 9  -  PREDICTIONS (66-tube, HFE-7000)
# ============================================================================
def predict_66tube(Tin=30.0):
    """66-tube performance using its geometric condenser resistance + open-bundle pool behavior."""
    d, e, f = OP_SUB["33-tube"]; Rcond = effective_condenser_resistance("66-tube")
    out = {}
    for chip in ["plain", "micro"]:
        chf = CHF["33"][chip]; Q = chf * A_FOOT
        sub = max(d * Tin + e * Q + f, 0.0); Tbulk = Tin + Q * Rcond; Tsat = Tbulk + sub
        Ts = chip_surface_temp(chf, Tsat, sub, NC_FACTOR["33"], chip)
        out[chip] = dict(chf=chf, Q=Q, Tsat=Tsat, sub=sub, Tsurf=Ts, Rcond=Rcond,
                         Rchip=(Ts - Tbulk) / Q, Rtot=(Ts - Tin) / Q)
    return out

# HFE-7000 boiling coefficients (anchored to El-Genk smooth-Cu HTC ~8200 W/m^2K near CHF)
CSF_HFE = {"plain": 0.0058, "micro": 0.0030}
CHF_HFE = {"plain": 30, "micro": 42}     # El-Genk / apparatus estimate [W/cm^2]

def predict_hfe(gk, Tin=20.0, subcooling=10.0):
    """HFE-7000 estimate: transfer coolant-side condenser resistance, recompute chip with HFE."""
    Rcond = effective_condenser_resistance(f"{gk}-tube"); out = {}
    for chip in ["plain", "micro"]:
        chf = CHF_HFE[chip]; area = AREA_MC if chip == "micro" else 1.0; Q = chf * A_FOOT
        Ts_super = surface_temp(chf, 40.0, 0.0, 9.0, CSF_HFE[chip], area, s=1.7, hfe=True) - 40.0
        Tsat = Tin + Q * Rcond + subcooling; Tsurf = Tsat + Ts_super
        out[chip] = dict(chf=chf, Q=Q, super=Ts_super, Tsat=Tsat, Tsurf=Tsurf,
                         Rcond=Rcond, Rchip=(Ts_super + subcooling) / Q, Rtot=(Tsurf - Tin) / Q)
    return out

# ============================================================================
# SECTION 10  -  FIGURE STYLE
# ============================================================================
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

C33, C42, INK, MUTE = "#1A5276", "#A93226", "#212F3D", "#7F8C8D"
GRID, ACC, GOOD, PANEL = "#E6E8EB", "#CA6F1E", "#1E8449", "#FBFCFD"
COOL = {"20": "#1A5276", "30": "#2E86C1", "40": "#CA6F1E", "50": "#A93226"}
MK = {"20": "o", "30": "s", "40": "^", "50": "D"}
CC = {"33": C33, "42": C42}; LAB = {"33": "33-tube", "42": "42-tube"}
CHIPCOL = {"plain": "#B9770E", "micro": "#138D75"}

def _style():
    matplotlib.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 11, "text.color": INK,
        "axes.titlesize": 12.5, "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlepad": 10,
        "axes.labelsize": 11, "axes.labelcolor": INK, "axes.edgecolor": "#AEB6BF", "axes.linewidth": 1.1,
        "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.9, "xtick.color": INK, "ytick.color": INK,
        "legend.fontsize": 9.5, "legend.frameon": True, "legend.framealpha": 0.96, "legend.edgecolor": "#D5DBDB",
        "figure.facecolor": "white", "savefig.dpi": 150, "savefig.bbox": "tight", "lines.linewidth": 2.4})

def _title(fig, title, sub=None, x=0.04, y=0.985):
    fig.text(x, y, title, ha="left", va="top", fontsize=15, fontweight="bold", color=INK)
    if sub:
        fig.text(x, y - 0.052, sub, ha="left", va="top", fontsize=10.5, color=MUTE)

# ============================================================================
# SECTION 11  -  FIGURE GENERATION
# ============================================================================
def fig_xsec():
    """CAD-extracted condenser cross-sections (33-tube and 42-tube), to common scale."""
    fig, axs = plt.subplots(2, 1, figsize=(9, 8))
    for ax, coords, OD, lab in [(axs[0], C33_COORDS, 4.76, "33-tube: 33 straight tubes (5 staggered rows)"),
                                (axs[1], C42_COORDS[:42], 3.175, "42-tube: 42 straight tubes (one bank, 4 rows)")]:
        for (x, y) in coords:
            ax.add_patch(plt.Circle((x, y), OD / 2, facecolor="#FAD7A0", edgecolor="#B9770E", lw=1.0, zorder=3))
            ax.add_patch(plt.Circle((x, y), OD / 2 * 0.66, facecolor="#D6EAF4", edgecolor="#5DADE2", lw=0.6, zorder=4))
        ax.set_aspect("equal"); ax.set_title(lab, fontsize=10.5, color=INK, pad=4)
        ax.set_xlabel("mm"); ax.autoscale(); ax.margins(0.05); ax.grid(alpha=0.3)
    _title(fig, "Condenser tube layouts (from CAD)",
           "Copper tube walls (amber) and coolant bores (blue), drawn to common scale.")
    fig.subplots_adjust(top=0.88, hspace=0.25); _save(fig, "mc_xsec")

def fig_mve():
    """Model vs experiment for each chip and condenser (q'' vs surface temperature)."""
    fig, axs = plt.subplots(2, 2, figsize=(12, 9.6))
    panels = [("33", "plain"), ("33", "micro"), ("42", "plain"), ("42", "micro")]
    for ax, (gk, chip) in zip(axs.flat, panels):
        for t in ["20", "30", "40", "50"]:
            pp = [p for p in points(gk, chip) if p["t"] == t]
            if not pp:
                continue
            ax.scatter([p["Tsurf"] for p in pp], [p["q"] for p in pp], s=26, marker=MK[t],
                       facecolor=COOL[t], edgecolor="white", lw=0.4, alpha=0.85, zorder=3, label=f"{t} C")
            qs = np.linspace(3, CHF[gk][chip], 80)
            Ts = [chip_temp_from_geometry(q, float(t), f"{gk}-tube", NC_FACTOR[gk], chip) for q in qs]
            ax.plot(Ts, qs, color=COOL[t], lw=1.8, zorder=2)
        ax.axhline(CHF[gk][chip], color=MUTE, ls="--", lw=1.0)
        ax.set_title(f"{LAB[gk]} condenser, {chip} chip", fontsize=10.5, color=INK, pad=4)
        ax.set_xlabel("chip surface temperature [C]"); ax.set_ylabel("heat flux q'' [W/cm$^2$]")
        ax.legend(fontsize=8, title="coolant inlet", ncol=2)
    _title(fig, "Model versus experiment", "Markers: data by coolant inlet. Lines: predictive model swept to CHF (dashed).")
    fig.subplots_adjust(top=0.91, hspace=0.25, wspace=0.2); _save(fig, "mc_mve")

def fig_res():
    """Chip-side and condenser-side resistance vs flux, bulk-liquid referenced."""
    fig, axs = plt.subplots(2, 2, figsize=(12, 9.6))
    panels = [("33", "plain"), ("33", "micro"), ("42", "plain"), ("42", "micro")]
    for ax, (gk, chip) in zip(axs.flat, panels):
        pp = points(gk, chip)
        ax.scatter([p["q"] for p in pp], [(p["Tsurf"] - p["Tliq"]) / p["Q"] * 1e3 for p in pp],
                   s=22, marker="o", facecolor=C42, edgecolor="white", lw=0.3, alpha=0.7, zorder=3, label="chip (data)")
        ax.scatter([p["q"] for p in pp], [(p["Tliq"] - p["Tin"]) / p["Q"] * 1e3 for p in pp],
                   s=22, marker="s", facecolor=C33, edgecolor="white", lw=0.3, alpha=0.7, zorder=3, label="condenser (data)")
        tm = np.median([float(p["t"]) for p in pp]); qs = np.linspace(max(min(p["q"] for p in pp), 5), CHF[gk][chip], 60)
        rch, rcd = [], []
        for q in qs:
            Tsat, sub = predict_operating(q, tm, f"{gk}-tube"); Tb = Tsat - sub; Q = q * A_FOOT
            Ts = chip_surface_temp(q, Tsat, sub, NC_FACTOR[gk], chip)
            rch.append((Ts - Tb) / Q * 1e3); rcd.append((Tb - tm) / Q * 1e3)
        ax.plot(qs, rch, color=C42, lw=2); ax.plot(qs, rcd, color=C33, lw=2)
        ax.set_title(f"{LAB[gk]} condenser, {chip} chip", fontsize=10.5, color=INK, pad=4)
        ax.set_xlabel("heat flux q'' [W/cm$^2$]"); ax.set_ylabel("resistance [mK/W]"); ax.legend(fontsize=8)
    _title(fig, "Thermal resistance breakdown", "Chip side and condenser side vs flux, referenced to bulk liquid. Markers data, lines model.")
    fig.subplots_adjust(top=0.91, hspace=0.25, wspace=0.2); _save(fig, "mc_res")

def fig_endtoend():
    """Predicted vs measured chip temperature, all points."""
    pp = points()
    pr = [chip_temp_from_geometry(p["q"], p["Tin"], f"{p['gk']}-tube", NC_FACTOR[p["gk"]], p["chip"]) for p in pp]
    me = [p["Tsurf"] for p in pp]
    fig, ax = plt.subplots(figsize=(7.2, 7)); _sa(ax)
    lo, hi = min(me + pr) - 3, max(me + pr) + 3
    ax.plot([lo, hi], [lo, hi], color=MUTE, lw=1.2)
    ax.fill_between([lo, hi], [lo * 0.85, hi * 0.85], [lo * 1.15, hi * 1.15], color=MUTE, alpha=0.10)
    for gk in ["33", "42"]:
        idx = [i for i, p in enumerate(pp) if p["gk"] == gk]
        ax.scatter([me[i] for i in idx], [pr[i] for i in idx], s=26, facecolor=CC[gk], edgecolor="white",
                   lw=0.4, alpha=0.8, label=f"{LAB[gk]}")
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    ax.set_xlabel("measured T_surf [C]"); ax.set_ylabel("predicted T_surf [C]")
    ax.legend(loc="upper left"); ax.text(0.97, 0.05, f"RMSE {rmse(pr, me):.1f} K\n(+/-15% band)",
                                         transform=ax.transAxes, ha="right", fontsize=9)
    _title(fig, "End-to-end predictive accuracy", "Chip temperature from geometry and boundary conditions only.")
    fig.subplots_adjust(top=0.9); _save(fig, "mc_endtoend")

def fig_crossval():
    """Out-of-sample: leave-one-coolant-out parity + in-sample vs held-out bars."""
    _, per = predictive_rmse()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 5.6)); _sa(a1); _sa(a2)
    LO = {}
    for gk in ["33", "42"]:
        pp = points(gk); temps = sorted(set(p["t"] for p in pp)); pr = []; me = []
        for t in temps:
            tr = [p for p in pp if p["t"] != t]; te = [p for p in pp if p["t"] == t]
            X = np.array([[p["Tin"], p["Q"], 1.0] for p in tr])
            aT = np.linalg.lstsq(X, np.array([p["Tsat"] for p in tr]), rcond=None)[0]
            aS = np.linalg.lstsq(X, np.array([p["sub"] for p in tr]), rcond=None)[0]
            for p in te:
                Tsat = aT @ [p["Tin"], p["Q"], 1.0]; sub = max(aS @ [p["Tin"], p["Q"], 1.0], 0.0)
                pr.append(chip_surface_temp(p["q"], Tsat, sub, NC_FACTOR[gk], p["chip"])); me.append(p["Tsurf"])
        ins = [chip_temp_from_geometry(p["q"], p["Tin"], f"{gk}-tube", NC_FACTOR[gk], p["chip"]) for p in pp]
        LO[gk] = dict(pr=np.array(pr), me=np.array(me), ho=rmse(pr, me), ins=rmse(ins, [p["Tsurf"] for p in pp]))
    allv = np.concatenate([LO["33"]["me"], LO["33"]["pr"], LO["42"]["me"], LO["42"]["pr"]])
    lo, hi = allv.min() - 3, allv.max() + 3
    a1.plot([lo, hi], [lo, hi], color=MUTE, lw=1.2)
    a1.fill_between([lo, hi], [lo * 0.85, hi * 0.85], [lo * 1.15, hi * 1.15], color=MUTE, alpha=0.10)
    for gk in ["33", "42"]:
        a1.scatter(LO[gk]["me"], LO[gk]["pr"], s=28, facecolor=CC[gk], edgecolor="white", lw=0.4, alpha=0.8,
                   label=f"{LAB[gk]} (held-out {LO[gk]['ho']:.1f} K)")
    a1.set_xlim(lo, hi); a1.set_ylim(lo, hi); a1.set_aspect("equal")
    a1.set_xlabel("measured T_surf [C]"); a1.set_ylabel("predicted T_surf [C] (held-out)")
    a1.legend(loc="upper left", fontsize=8.8); a1.set_title("Leave-one-coolant-inlet-out", fontsize=11, color=INK)
    x = np.arange(2); w = 0.36
    a2.bar(x - w / 2, [LO["33"]["ins"], LO["42"]["ins"]], w, color=GOOD, label="in-sample")
    a2.bar(x + w / 2, [LO["33"]["ho"], LO["42"]["ho"]], w, color=ACC, label="held-out")
    a2.set_xticks(x); a2.set_xticklabels(["33-tube", "42-tube"]); a2.set_ylabel("chip-temperature RMSE [K]")
    a2.legend(loc="upper left", fontsize=8.8); a2.set_title("In-sample vs out-of-sample", fontsize=11, color=INK)
    _title(fig, "Out-of-sample validation", "Chip temperature predicted for a coolant inlet withheld from the fit.")
    fig.subplots_adjust(top=0.84, wspace=0.22); _save(fig, "mc_crossval")

def fig_sensitivity():
    s = sensitivity()
    grp = {"c offset": "op", "a gain": "op", "b slope": "op", "C_sf": "chip", "F_nc": "chip", "A_r": "chip"}
    rows = sorted(s.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(8.6, 5.0)); _sa(ax)
    y = np.arange(len(rows)); vals = [v for _, v in rows]
    cols = [ACC if grp[k] == "op" else C33 for k, _ in rows]
    ax.barh(y, vals, color=cols, edgecolor="white", height=0.62, zorder=3)
    for yi, v in zip(y, vals):
        ax.text(v + 0.04, yi, f"{v:.2f} K", va="center", fontsize=9, color=INK)
    ax.set_yticks(y); ax.set_yticklabels([k for k, _ in rows]); ax.set_xlim(0, max(vals) * 1.18)
    ax.set_xlabel("mean change in predicted T_surf for +/-10% [K]")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=ACC, label="operating-point map"), Patch(fc=C33, label="chip / boiling")],
              loc="lower right", fontsize=9)
    _title(fig, "Parameter sensitivity", "Effect on chip temperature of a +/-10% change in each calibrated constant.")
    fig.subplots_adjust(top=0.85, left=0.2); _save(fig, "mc_sensitivity")

def fig_condscope():
    geo = {g: condenser_resistance(f"{g}-tube")["R"] * 1e3 for g in ["33", "42", "66"]}
    # effective/measured bars come from the single source; 66-tube has no measurement
    meas = {g: effective_condenser_resistance(f"{g}-tube") * 1e3 for g in ["33", "42"]}
    meas["66"] = np.nan
    names = ["33-tube\n(open)", "42-tube\n(confined)", "66-tube\n(open)"]
    fig, ax = plt.subplots(figsize=(8.4, 5.0)); _sa(ax); x = np.arange(3); w = 0.36
    gv = [geo["33"], geo["42"], geo["66"]]; mv = [meas["33"], meas["42"], meas["66"]]
    ax.bar(x - w / 2, gv, w, color=C33, edgecolor="white", label="geometric (coolant side)", zorder=3)
    ax.bar(x + w / 2, [m if not np.isnan(m) else 0 for m in mv], w, color=ACC, edgecolor="white",
           label="measured", zorder=3)
    for xi, v in zip(x, gv):
        ax.text(xi - w / 2, v + 0.7, f"{v:.1f}", ha="center", fontsize=9)
    for xi, m in zip(x, mv):
        if not np.isnan(m):
            ax.text(xi + w / 2, m + 0.7, f"{m:.1f}", ha="center", fontsize=9)
            ax.text(xi + 0.30, min(gv[xi], m), f"real/ideal {m/gv[xi]:.2f}", va="center", fontsize=8.4,
                    bbox=dict(boxstyle="round,pad=0.3", fc=PANEL, ec="#D5DBDB"))
        else:
            ax.text(xi + w / 2, 1.2, "no data\nyet", ha="center", fontsize=8.2, color=MUTE, style="italic")
    ax.set_xticks(x); ax.set_xticklabels(names); ax.set_ylabel("condenser-side resistance [mK/W]"); ax.set_ylim(0, 50)
    ax.legend(loc="upper left", fontsize=8.8)
    _title(fig, "Condenser resistance: geometry vs measurement", "Developing-laminar estimate sets the ranking; a layout factor separates ideal from real.")
    fig.subplots_adjust(top=0.85); _save(fig, "mc_condscope")

def fig_condenser_ops():
    fig, axs = plt.subplots(2, 2, figsize=(12.4, 9.6))
    for ax in axs.flat:
        _sa(ax)
    (a1, a2), (a3, a4) = axs
    P = {g: points(g) for g in ["33", "42"]}
    for gk in ["33", "42"]:
        a, b, c = OP_TSAT[f"{gk}-tube"]
        X = np.array([p["Tin"] for p in P[gk]]); Y = np.array([p["Tsat"] - b * p["Q"] for p in P[gk]])
        a1.scatter(X, Y, s=18, facecolor=CC[gk], edgecolor="white", lw=0.3, alpha=0.7, zorder=3)
        xs = np.linspace(X.min(), X.max(), 40); a1.plot(xs, a * xs + c, color=CC[gk], lw=2, label=f"{LAB[gk]}: a={a:.2f}")
    a1.set_xlabel("coolant inlet [C]"); a1.set_ylabel("$T_{sat}-bQ$ [C]"); a1.legend(fontsize=8.6)
    a1.set_title("Coolant-inlet sensitivity (gain a)", fontsize=10.5, color=INK)
    for gk in ["33", "42"]:
        a, b, c = OP_TSAT[f"{gk}-tube"]
        X = np.array([p["Q"] for p in P[gk]]); Y = np.array([p["Tsat"] - a * p["Tin"] for p in P[gk]])
        a2.scatter(X, Y, s=18, facecolor=CC[gk], edgecolor="white", lw=0.3, alpha=0.7, zorder=3)
        xs = np.linspace(X.min(), X.max(), 40); a2.plot(xs, b * xs + c, color=CC[gk], lw=2, label=f"{LAB[gk]}: b={b*1e3:.1f} mK/W")
    a2.set_xlabel("heat load Q [W]"); a2.set_ylabel("$T_{sat}-aT_{in}$ [C]"); a2.legend(fontsize=8.6)
    a2.set_title("Heat-load sensitivity (resistance b)", fontsize=10.5, color=INK)
    for gk in ["33", "42"]:
        d, e, f = OP_SUB[f"{gk}-tube"]; tm = np.median([p["Tin"] for p in P[gk]])
        X = np.array([p["Q"] for p in P[gk]]); Y = np.array([p["sub"] for p in P[gk]])
        a3.scatter(X, Y, s=18, facecolor=CC[gk], edgecolor="white", lw=0.3, alpha=0.7, zorder=3)
        xs = np.linspace(X.min(), X.max(), 40); a3.plot(xs, np.maximum(d * tm + e * xs + f, 0), color=CC[gk], lw=2, label=LAB[gk])
    a3.set_xlabel("heat load Q [W]"); a3.set_ylabel("subcooling [K]"); a3.legend(fontsize=8.6)
    a3.set_title("Pool subcooling vs load", fontsize=10.5, color=INK)
    for gk in ["33", "42"]:
        X = np.array([p["q"] for p in P[gk]]); R = np.array([(p["Tliq"] - p["Tin"]) / p["Q"] * 1e3 for p in P[gk]])
        a4.scatter(X, R, s=18, facecolor=CC[gk], edgecolor="white", lw=0.3, alpha=0.7, zorder=3, label=f"{LAB[gk]} data")
    a4.set_xlabel("heat flux q'' [W/cm$^2$]"); a4.set_ylabel("condenser R [mK/W]"); a4.set_ylim(0, 60); a4.legend(fontsize=8.6)
    a4.set_title("Condenser-side resistance vs flux", fontsize=10.5, color=INK)
    _title(fig, "Condenser operating behavior", "Saturation temperature and subcooling vs coolant inlet and heat load.")
    fig.subplots_adjust(top=0.9, hspace=0.27, wspace=0.2); _save(fig, "mc_condenser_ops")

def fig_chip_resistance():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 5.6), sharey=True); _sa(a1); _sa(a2)
    for ax, chip, title in [(a1, "plain", "Plain chip"), (a2, "micro", "Microchannel chip")]:
        for gk in ["33", "42"]:
            pp = points(gk, chip)
            if not pp:
                continue
            ax.scatter([p["q"] for p in pp], [(p["Tsurf"] - p["Tliq"]) / p["Q"] * 1e3 for p in pp],
                       s=24, facecolor=CC[gk], edgecolor="white", lw=0.3, alpha=0.65, zorder=3, label=f"{LAB[gk]} data")
            tm = np.median([float(p["t"]) for p in pp]); qs = np.linspace(max(min(p["q"] for p in pp), 5), CHF[gk][chip], 60)
            rm = []
            for q in qs:
                Tsat, sub = predict_operating(q, tm, f"{gk}-tube"); Q = q * A_FOOT
                Ts = chip_surface_temp(q, Tsat, sub, NC_FACTOR[gk], chip); rm.append((Ts - (Tsat - sub)) / Q * 1e3)
            ax.plot(qs, rm, color=CC[gk], lw=2.2, label=f"{LAB[gk]} model")
        ax.set_xlabel("heat flux q'' [W/cm$^2$]"); ax.set_title(title, fontsize=11, color=INK); ax.legend(fontsize=8.6); ax.set_ylim(0, 90)
    a1.set_ylabel("chip-side resistance [mK/W]")
    _title(fig, "Chip-side thermal resistance: model vs experiment", "Microchannel cuts chip-side resistance about threefold; model tracks both surfaces.")
    fig.subplots_adjust(top=0.84, wspace=0.06); _save(fig, "mc_chip_resistance")

def fig_boilingcurve_66():
    d, e, f = OP_SUB["33-tube"]; R66 = condenser_resistance("66-tube")["R"] * OPEN_FACTOR; Tin = 30.0
    def curve(chip, Rcond):
        qs = np.linspace(4, CHF["33"][chip], 200); Ts = []; sup = []
        for q in qs:
            Q = q * A_FOOT; sub = max(d * Tin + e * Q + f, 0.0); Tb = Tin + Q * Rcond; Tsa = Tb + sub
            ts = chip_surface_temp(q, Tsa, sub, NC_FACTOR["33"], chip); Ts.append(ts); sup.append(ts - Tsa)
        return qs, np.array(Ts), np.array(sup)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.8, 5.7)); _sa(a1); _sa(a2)
    a1.axvline(0, color=MUTE, lw=1.0, ls=":")
    for chip in ["plain", "micro"]:
        qs, Ts, sup = curve(chip, R66)
        a1.plot(sup, qs, color=CHIPCOL[chip], lw=2.4, label=f"{chip} chip")
        a1.scatter([sup[-1]], [qs[-1]], s=48, facecolor=CHIPCOL[chip], edgecolor="white", lw=0.8, zorder=5)
    a1.set_xlabel("wall superheat [K]"); a1.set_ylabel("heat flux q'' [W/cm$^2$]"); a1.legend(fontsize=9, loc="center right")
    a1.set_title("Boiling curve (66-tube, predicted)", fontsize=11, color=INK); a1.set_ylim(0, None)
    for chip in ["plain", "micro"]:
        qs, Ts66, _ = curve(chip, R66); _, Ts33, _ = curve(chip, 13.5e-3)
        a2.plot(Ts66, qs, color=CHIPCOL[chip], lw=2.4, label=f"66-tube {chip}")
        a2.plot(Ts33, qs, color=CHIPCOL[chip], lw=1.8, ls="--", alpha=0.85, label=f"33-tube {chip}")
    a2.set_xlabel("chip surface temperature [C]"); a2.set_ylabel("heat flux q'' [W/cm$^2$]"); a2.legend(fontsize=8.2, loc="lower right")
    a2.set_title("Chip temperature: 66-tube vs 33-tube", fontsize=11, color=INK); a2.set_ylim(0, None)
    _title(fig, "Predicted boiling curve for the 66-tube condenser", "Coolant inlet 30 C. CHF taken from the 33-tube pending a 66-tube measurement.")
    fig.subplots_adjust(top=0.85, wspace=0.18); _save(fig, "mc_boilingcurve_66")

def fig_hfe():
    def qroh(dT, P, Csf, s): return P["mu_l"] * P["hfg"] * np.sqrt(G * (P["rho_l"] - P["rho_v"]) / P["sigma"]) * (P["cp_l"] * dT / (Csf * P["hfg"] * P["Pr"] ** s)) ** 3
    def dTq(q, P, Csf, s): return (Csf * P["hfg"] * P["Pr"] ** s / P["cp_l"]) * (q / (P["mu_l"] * P["hfg"] * np.sqrt(G * (P["rho_l"] - P["rho_v"]) / P["sigma"]))) ** (1 / 3)
    W = props(60.0); WAT = dict(mu_l=W["mu_l"], hfg=W["hfg"], rho_l=W["rho_l"], rho_v=W["rho_v"], sigma=W["sigma"], cp_l=W["cp_l"], Pr=W["Pr"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.8, 5.7)); _sa(a1); _sa(a2)
    def bc(P, Csf, chf, s, area=1.0):
        dmax = dTq(chf * 1e4 / area, P, Csf, s); dT = np.linspace(0.3, dmax, 200); return dT, area * qroh(dT, P, Csf, s) / 1e4
    for chip, area in [("plain", 1.0), ("micro", AREA_MC)]:
        dT, q = bc(HFE_PROPS, CSF_HFE[chip], CHF_HFE[chip], 1.7, area); a1.plot(dT, q, color=CHIPCOL[chip], lw=2.4, label=f"HFE {chip}")
        a1.scatter([dT[-1]], [q[-1]], s=46, facecolor=CHIPCOL[chip], edgecolor="white", lw=0.8, zorder=5)
    for chip, Csf, area in [("plain", 0.0131, 1.0), ("micro", 0.0067, AREA_MC)]:
        dT, q = bc(WAT, Csf, CHF["33"][chip], 1.0, area); a1.plot(dT, q, color=CHIPCOL[chip], lw=1.8, ls="--", alpha=0.8, label=f"water {chip}")
    a1.set_xlabel("wall superheat [K]"); a1.set_ylabel("heat flux q'' [W/cm$^2$]"); a1.legend(fontsize=8.4, loc="upper left")
    a1.set_title("Boiling curve: HFE-7000 vs water", fontsize=11, color=INK); a1.set_xlim(0, None); a1.set_ylim(0, 185)
    Rc = {g: effective_condenser_resistance(f"{g}-tube") for g in ("33", "42")}; Tin = 20.0; sub = 10.0
    for chip, area in [("plain", 1.0), ("micro", AREA_MC)]:
        for gk, ls, lw in [("33", "-", 2.2), ("42", "--", 1.7)]:
            qs = np.linspace(2, CHF_HFE[chip], 160); Ts = [Tin + q * A_FOOT * Rc[gk] + sub + dTq(q * 1e4 / area, HFE_PROPS, CSF_HFE[chip], 1.7) for q in qs]
            a2.plot(Ts, qs, color=CHIPCOL[chip], lw=lw, ls=ls, label=f"{gk}-tube {chip}")
    a2.set_xlabel("chip surface temperature [C]"); a2.set_ylabel("heat flux q'' [W/cm$^2$]"); a2.legend(fontsize=8.2, loc="lower right"); a2.set_ylim(0, 48)
    _title(fig, "Predicted HFE-7000 performance (estimate)", "HFE properties from literature, C_sf anchored to El-Genk data, CHF from El-Genk/apparatus, subcooling 10 K.")
    fig.subplots_adjust(top=0.85, wspace=0.18); _save(fig, "mc_hfe_prediction")

# ---- figure helpers ----
import os
def _sa(ax):
    ax.tick_params(length=4, width=1.0)
    return ax
def _save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(f"{OUT}/{name}.png", dpi=150); plt.close(fig); print(f"  wrote {OUT}/{name}.png")

ALL_FIGURES = [fig_xsec, fig_mve, fig_res, fig_endtoend, fig_crossval, fig_sensitivity,
               fig_condscope, fig_condenser_ops, fig_chip_resistance, fig_boilingcurve_66, fig_hfe]

# ============================================================================
# SECTION 12  -  MAIN
# ============================================================================
def run_model():
    _style()
    print("=" * 70)
    print(" Subcooled pool-boiling chamber: gray-box thermal model (reproduction)")
    print("=" * 70)
    n = len(points()); print(f"\nLoaded {n} valid experimental points (2 condensers, 2 chips, 4 coolant inlets).")

    print("\n--- Calibration re-derived from data (vs stored constants) ---")
    for chip in ["plain", "micro"]:
        c33 = fit_csf("33", chip); c42 = fit_csf("42", chip)
        print(f"  C_sf {chip:6s}: 33-tube {c33:.4f}  42-tube {c42:.4f}  (stored {CHIPS[chip]['C_sf']:.4f})")
    for gk in ["33", "42"]:
        aT, aS = fit_operating_maps(gk)
        print(f"  {gk}-tube T_sat map (a,b,c) = ({aT[0]:.3f}, {aT[1]:.5f}, {aT[2]:.2f})  "
              f"stored ({OP_TSAT[f'{gk}-tube'][0]:.3f}, {OP_TSAT[f'{gk}-tube'][1]:.5f}, {OP_TSAT[f'{gk}-tube'][2]:.2f})")

    print("\n--- Predictive validation ---")
    overall, per = predictive_rmse()
    print(f"  Overall chip-temperature RMSE: {overall:.2f} K")
    for k, v in per.items():
        print(f"    {k:10s}: {v:.2f} K")
    for gk in ["33", "42"]:
        print(f"  {gk}-tube leave-one-coolant-out held-out RMSE: {leave_one_coolant_out(gk):.2f} K")

    print("\n--- Parameter sensitivity (mean |dT_surf| for +/-10%) ---")
    for k, v in sorted(sensitivity().items(), key=lambda kv: -kv[1]):
        print(f"    {k:10s}: {v:.2f} K")

    print("\n--- Condenser-side resistance (geometric, developing-laminar) ---")
    for gk in ["33", "42", "66"]:
        r = condenser_resistance(f"{gk}-tube"); print(f"    {gk}-tube: Re={r['Re']:.0f}  Nu={r['Nu']:.2f}  R={r['R']*1e3:.1f} mK/W")

    print("\n--- 66-tube prediction at CHF (Tin=30 C) ---")
    for chip, v in predict_66tube().items():
        print(f"    {chip:6s}: CHF {v['chf']} W/cm2  T_surf {v['Tsurf']:.1f} C  R_tot {v['Rtot']:.4f} K/W")

    print("\n--- HFE-7000 estimate at CHF (Tin=20 C) ---")
    for gk in ["33", "42"]:
        for chip, v in predict_hfe(gk).items():
            print(f"    {gk}-tube {chip:6s}: CHF {v['chf']} W/cm2  T_surf {v['Tsurf']:.1f} C  R_tot {v['Rtot']:.4f} K/W")

    print("\n--- Generating figures ---")
    for fn in ALL_FIGURES:
        try:
            fn()
        except Exception as ex:
            print(f"  [skip] {fn.__name__}: {ex}")
    print(f"\nDone. Figures in ./{OUT}/")



################################################################################
#  SECTION B  -  PUBLICATION ANALYSIS (boiling curves, parity, residuals)
################################################################################
"""
Publication-quality boiling curves and numerical error analysis for the
validated gray-box thermal model of the subcooled pool-boiling chamber.

The model (chamber_model.py) is calibrated to the measured data; this script
quantifies its predictive accuracy and renders the figures for the manuscript:
    fig_boiling_curves   model vs experiment, q'' vs chip surface temperature
    fig_parity           predicted vs measured chip surface temperature
    fig_residuals        residual structure and distribution
plus a LaTeX results table and a per-point CSV.

All predictions use the FULL predictive chain chip_temp_from_geometry():
geometry + coolant inlet + heat flux -> chip surface temperature, with the
fitted, geometry-independent boiling coefficients. No per-point tuning.
"""
import os, csv, importlib.util
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ----------------------------------------------------------------------------
# load the validated model as a module

PUB_OUT = "pub_figs"; os.makedirs(PUB_OUT, exist_ok=True)

# ----------------------------------------------------------------------------
# publication style: STIX (Times-like) text + matched math, vector output
mpl.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix",
    "font.size": 9.5, "axes.labelsize": 10.5, "axes.titlesize": 10.5,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5, "legend.fontsize": 8,
    "axes.linewidth": 0.8, "lines.linewidth": 1.5, "lines.markersize": 4.2,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.minor.visible": True, "ytick.minor.visible": True,
    "xtick.top": True, "ytick.right": True,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.5,
    "savefig.dpi": 300, "savefig.bbox": "tight", "figure.dpi": 150,
})

CT = {"20": "#1f4e79", "30": "#2e7d32", "40": "#e07b00", "50": "#c0392b"}  # coolant inlet colour
CONFIGS = [("33", "plain"), ("33", "micro"), ("42", "plain"), ("42", "micro")]
LABELS = {("33", "plain"): "33-tube, plain copper", ("33", "micro"): "33-tube, microchannel",
          ("42", "plain"): "42-tube, plain copper", ("42", "micro"): "42-tube, microchannel"}
PUB_CHF = {("33", "plain"): 114.0, ("33", "micro"): 174.0, ("42", "plain"): 65.0, ("42", "micro"): 125.0}
MARK = {("33", "plain"): "o", ("33", "micro"): "s", ("42", "plain"): "^", ("42", "micro"): "D"}


def predict(p):
    return chip_temp_from_geometry(p["q"], p["Tin"], f'{p["gk"]}-tube',
                                      NC_FACTOR[p["gk"]], p["chip"])


# ============================================================================
# FIGURE 1 -- boiling curves, model vs experiment (2x2, one panel per config)
# ============================================================================
def fig_boiling():
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.4))
    for ax, cfg in zip(axes.ravel(), CONFIGS):
        gk, chip = cfg
        pts = points(gk, chip)
        for t in ["20", "30", "40", "50"]:
            sub = sorted([p for p in pts if p["t"] == t], key=lambda r: r["Tsurf"])
            if not sub:
                continue
            Tm = [p["Tsurf"] for p in sub]; qm = [p["q"] for p in sub]
            ax.plot(Tm, qm, MARK[cfg], color=CT[t], mfc="white", mew=1.1, zorder=3)
            # model curve over the measured flux range
            qg = np.linspace(min(qm), max(qm), 60)
            Tp = [chip_temp_from_geometry(q, float(t), f"{gk}-tube",
                                             NC_FACTOR[gk], chip) for q in qg]
            ax.plot(Tp, qg, "-", color=CT[t], lw=1.6, zorder=2)
        ax.set_title(LABELS[cfg], pad=4)
        ax.set_xlabel(r"chip surface temperature $T_{\mathrm{surf}}\;[^{\circ}\mathrm{C}]$")
        ax.set_ylabel(r"heat flux $q''\;[\mathrm{W\,cm^{-2}}]$")
        # per-panel RMSE
        pr = [predict(p) for p in pts]; me = [p["Tsurf"] for p in pts]
        ax.text(0.04, 0.95, rf"$\mathrm{{RMSE}}={rmse(pr, me):.2f}\ \mathrm{{K}}$"
                            f"\n$n={len(pts)}$",
                transform=ax.transAxes, va="top", ha="left", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", lw=0.6, alpha=0.9))
        ax.margins(x=0.04)
    # shared legend: coolant inlets + experiment/model proxies
    hc = [Line2D([], [], color=CT[t], lw=1.6, label=rf"$T_{{\mathrm{{in}}}}={t}\,^{{\circ}}\mathrm{{C}}$")
          for t in ["20", "30", "40", "50"]]
    hp = [Line2D([], [], color="0.3", marker="o", mfc="white", mew=1.1, ls="none", label="experiment"),
          Line2D([], [], color="0.3", lw=1.6, label="model")]
    fig.legend(handles=hc + hp, ncol=6, loc="lower center", frameon=False,
               bbox_to_anchor=(0.5, -0.005), columnspacing=1.3, handletextpad=0.5)
    fig.suptitle("Pool-boiling curves: validated gray-box model vs. experiment",
                 fontsize=11, y=0.995)
    fig.tight_layout(rect=(0, 0.035, 1, 0.985))
    fig.savefig(f"{PUB_OUT}/fig_boiling_curves.pdf"); fig.savefig(f"{PUB_OUT}/fig_boiling_curves.png")
    plt.close(fig)


# ============================================================================
# FIGURE 2 -- parity (predicted vs measured chip surface temperature)
# ============================================================================
def fig_parity(stats):
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    allm, allp = [], []
    for cfg in CONFIGS:
        gk, chip = cfg; pts = points(gk, chip)
        me = [p["Tsurf"] for p in pts]; pr = [predict(p) for p in pts]
        allm += me; allp += pr
        ax.plot(me, pr, MARK[cfg], color=CT["30"] if False else None, mfc="none", mew=0.9,
                ms=4.2, label=LABELS[cfg], alpha=0.85)
    lo, hi = min(allm + allp) - 3, max(allm + allp) + 3
    ax.plot([lo, hi], [lo, hi], "k-", lw=1.0, zorder=1)
    for d, ls in [(5, "--"), (-5, "--")]:
        ax.plot([lo, hi], [lo + d, hi + d], color="0.5", ls=ls, lw=0.8, zorder=1)
    ax.text(0.96, 0.10, r"$\pm 5\ \mathrm{K}$", transform=ax.transAxes, ha="right",
            color="0.4", fontsize=8)
    o = stats["overall"]
    ax.text(0.04, 0.96,
            rf"$\mathrm{{RMSE}}={o['rmse']:.2f}\ \mathrm{{K}}$" "\n"
            rf"$\mathrm{{MAE}}={o['mae']:.2f}\ \mathrm{{K}}$" "\n"
            rf"$R^2={o['r2']:.3f}$" "\n"
            rf"$n={o['n']}$",
            transform=ax.transAxes, va="top", ha="left", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="0.7", lw=0.6))
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    ax.set_xlabel(r"measured $T_{\mathrm{surf}}\;[^{\circ}\mathrm{C}]$")
    ax.set_ylabel(r"predicted $T_{\mathrm{surf}}\;[^{\circ}\mathrm{C}]$")
    ax.set_title("Predictive parity (geometry + BC only)", pad=4)
    ax.legend(loc="lower right", frameon=False, fontsize=7.5, handletextpad=0.3)
    fig.tight_layout()
    fig.savefig(f"{PUB_OUT}/fig_parity.pdf"); fig.savefig(f"{PUB_OUT}/fig_parity.png")
    plt.close(fig)


# ============================================================================
# FIGURE 3 -- residual structure + distribution
# ============================================================================
def fig_residuals(stats):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.3),
                                 gridspec_kw=dict(width_ratios=[2, 1]))
    allr = []
    for cfg in CONFIGS:
        gk, chip = cfg; pts = points(gk, chip)
        me = np.array([p["Tsurf"] for p in pts]); pr = np.array([predict(p) for p in pts])
        r = pr - me; allr += list(r)
        a1.plot(me, r, MARK[cfg], color=None, mfc="none", mew=0.9, ms=4.0,
                label=LABELS[cfg], alpha=0.8)
    allr = np.array(allr)
    a1.axhline(0, color="k", lw=0.9)
    a1.axhline(allr.mean(), color="#c0392b", ls="--", lw=0.9)
    a1.fill_between([min([p["Tsurf"] for p in points()]) - 2,
                     max([p["Tsurf"] for p in points()]) + 2],
                    allr.mean() - allr.std(), allr.mean() + allr.std(),
                    color="0.6", alpha=0.18, zorder=0)
    a1.set_xlabel(r"measured $T_{\mathrm{surf}}\;[^{\circ}\mathrm{C}]$")
    a1.set_ylabel(r"residual $T_{\mathrm{pred}}-T_{\mathrm{meas}}\;[\mathrm{K}]$")
    a1.set_title("Residual vs. surface temperature", pad=4)
    a1.legend(loc="upper right", frameon=False, fontsize=7, ncol=2, handletextpad=0.3,
              columnspacing=0.8)
    a1.text(0.03, 0.05, rf"bias $={allr.mean():+.2f}$ K,  $\sigma={allr.std():.2f}$ K",
            transform=a1.transAxes, fontsize=8, va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", lw=0.6, alpha=0.9))

    a2.hist(allr, bins=22, color="#4a6fa5", edgecolor="white", linewidth=0.4, density=True)
    x = np.linspace(allr.min(), allr.max(), 200)
    a2.plot(x, np.exp(-0.5 * ((x - allr.mean()) / allr.std()) ** 2) /
            (allr.std() * np.sqrt(2 * np.pi)), "k-", lw=1.2)
    a2.axvline(0, color="0.4", lw=0.8, ls=":")
    a2.set_xlabel(r"residual $[\mathrm{K}]$"); a2.set_ylabel("density")
    a2.set_title("Distribution", pad=4)
    fig.tight_layout()
    fig.savefig(f"{PUB_OUT}/fig_residuals.pdf"); fig.savefig(f"{PUB_OUT}/fig_residuals.png")
    plt.close(fig)


# ============================================================================
# numerical analysis: per-config + overall metrics, LOCO, table + CSV
# ============================================================================
def analyse():
    rows, allm, allp, csv_rows = [], [], [], []
    for cfg in CONFIGS:
        gk, chip = cfg; pts = points(gk, chip)
        me = np.array([p["Tsurf"] for p in pts]); pr = np.array([predict(p) for p in pts])
        r = pr - me; allm += list(me); allp += list(pr)
        ss_res = float(np.sum(r ** 2)); ss_tot = float(np.sum((me - me.mean()) ** 2))
        rows.append(dict(cfg=LABELS[cfg], n=len(pts), rmse=rmse(pr, me),
                         mae=float(np.mean(np.abs(r))), maxe=float(np.max(np.abs(r))),
                         bias=float(np.mean(r)), std=float(np.std(r)),
                         r2=1 - ss_res / ss_tot))
        for p, pp in zip(pts, pr):
            csv_rows.append([gk + "-tube", chip, p["t"], p["q"], p["Tin"],
                             p["Tsurf"], round(pp, 3), round(pp - p["Tsurf"], 3)])
    allm, allp = np.array(allm), np.array(allp); ar = allp - allm
    overall = dict(n=len(allm), rmse=rmse(allp, allm), mae=float(np.mean(np.abs(ar))),
                   maxe=float(np.max(np.abs(ar))), bias=float(np.mean(ar)), std=float(np.std(ar)),
                   r2=1 - float(np.sum(ar ** 2)) / float(np.sum((allm - allm.mean()) ** 2)))
    loco = {gk: leave_one_coolant_out(gk) for gk in ["33", "42"]}

    # CSV of every prediction
    with open(f"{PUB_OUT}/predictions.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["condenser", "chip", "coolant_C", "q_Wcm2", "Tin_C",
                    "Tsurf_meas_C", "Tsurf_pred_C", "residual_K"])
        w.writerows(csv_rows)

    # LaTeX table (booktabs)
    with open(f"{PUB_OUT}/results_table.tex", "w") as f:
        f.write(r"""\begin{table}[t]
\centering
\caption{Predictive accuracy of the gray-box model for the chip surface
temperature. Predictions use the full geometry-to-temperature chain with
fitted, geometry-independent boiling coefficients; no per-point tuning.
RMSE, MAE and maximum absolute error are in kelvin; bias is the signed mean
residual. The leave-one-coolant-out (LOCO) column is the held-out RMSE when an
entire coolant-inlet condition is withheld from the calibration.}
\label{tab:accuracy}
\begin{tabular}{lrrrrrrr}
\toprule
Configuration & $n$ & RMSE & MAE & $\max|e|$ & bias & $R^2$ & LOCO \\
\midrule
""")
        loco_by = {LABELS[(g, ch)]: leave_one_coolant_out(g, ch)
                   for g in ["33", "42"] for ch in ["plain", "micro"]}
        for r in rows:
            lc = loco_by[r["cfg"]]
            f.write(f"{r['cfg']} & {r['n']} & {r['rmse']:.2f} & {r['mae']:.2f} & "
                    f"{r['maxe']:.2f} & {r['bias']:+.2f} & {r['r2']:.3f} & {lc:.2f} \\\\\n")
        f.write(r"\midrule" "\n")
        f.write(f"\\textbf{{All data}} & {overall['n']} & {overall['rmse']:.2f} & "
                f"{overall['mae']:.2f} & {overall['maxe']:.2f} & {overall['bias']:+.2f} & "
                f"{overall['r2']:.3f} & -- \\\\\n")
        f.write(r"""\bottomrule
\end{tabular}
\end{table}
""")
    return dict(rows=rows, overall=overall, loco=loco)


def run_publication():
    stats = analyse()
    fig_boiling()
    fig_parity(stats)
    fig_residuals(stats)
    o = stats["overall"]
    print("Per-configuration accuracy (chip surface temperature):")
    print(f"{'configuration':28s}{'n':>4}{'RMSE':>7}{'MAE':>7}{'max|e|':>8}{'bias':>7}{'R2':>7}")
    for r in stats["rows"]:
        print(f"{r['cfg']:28s}{r['n']:>4}{r['rmse']:>7.2f}{r['mae']:>7.2f}"
              f"{r['maxe']:>8.2f}{r['bias']:>+7.2f}{r['r2']:>7.3f}")
    print(f"{'ALL DATA':28s}{o['n']:>4}{o['rmse']:>7.2f}{o['mae']:>7.2f}"
          f"{o['maxe']:>8.2f}{o['bias']:>+7.2f}{o['r2']:>7.3f}")
    print(f"\nLeave-one-coolant-out held-out RMSE:  33-tube {stats['loco']['33']:.2f} K,"
          f"  42-tube {stats['loco']['42']:.2f} K")
    print(f"\nFigures + table + CSV in {PUB_OUT}/")




################################################################################
#  SECTION C  -  3D OPENFOAM POST-PROCESSING (PyVista)
################################################################################
"""
Post-process the 3D subcooled pool-boiling chamber OpenFOAM case
(solver: interCondensatingEvaporatingFoam) with PyVista.

Renders four 3D views of the boiling field at the latest time step:
  view1_overview      chamber + tube bundle + chip + liquid/vapour interface
  view2_temperature   temperature on a vertical mid-plane slice
  view3_velocity      velocity magnitude on a vertical mid-plane slice
  view4_interface     the liquid/vapour interface (alpha.water = 0.5), coloured by height

Usage
-----
    python postprocess_3d.py [CASE_DIR] [OUT_DIR]

Headless (no display attached), e.g. on a cluster login node:
    xvfb-run -a python postprocess_3d.py [CASE_DIR] [OUT_DIR]

Requires: pyvista, numpy   (pip install pyvista)
Reads the case directly via the OpenFOAM reader; if that is unavailable it
falls back to the output of `foamToVTK` (the VTK/ folder in the case).

NOTE on physical validity: the temperature and velocity fields are clamped for
display because this short, coarse, uncalibrated run carries non-physical
hot-spot and parasitic-velocity spikes. The clamping is visualization only; it
does not fix the underlying field, which is not converged or validated.
"""
import os
import sys
import glob
import numpy as np



T_CLAMP = (305.0, 360.0)   # K; physical band (condenser 305 K, chip 358 K)
SLICE_NORMAL = "y"         # cut through the tube-axis mid-plane


def load_latest(case):
    """Return (internal_mesh, {patch_name: mesh}, time_label) for the latest time."""
    foam = os.path.join(case, "case.foam")
    try:
        open(foam, "a").close()
        r = pv.OpenFOAMReader(foam)
        r.set_active_time_value(r.time_values[-1])
        m = r.read()
        internal = m["internalMesh"]
        bnd = m["boundary"]
        patches = {n: bnd[n] for n in bnd.keys()}
        return internal, patches, f"{r.time_values[-1]:.2e} s"
    except Exception:
        vtms = sorted(glob.glob(os.path.join(case, "VTK", "*_*.vtm")),
                      key=lambda f: int(f.split("_")[-1].split(".")[0]))
        if not vtms:
            raise FileNotFoundError("No case.foam readable and no VTK/ output found. "
                                    "Run `foamToVTK` in the case first.")
        m = pv.read(vtms[-1])
        internal = m["internal"]
        bnd = m["boundary"]
        patches = {n: bnd[n] for n in bnd.keys()}
        return internal, patches, vtms[-1].split("/")[-1]


def add_outline(p, mesh):
    p.add_mesh(mesh.outline(), color="black", line_width=1)


def iso_camera(p):
    p.camera_position = "iso"
    p.camera.azimuth = 25
    p.camera.elevation = 12
    p.camera.zoom(1.25)


def run_postprocess(case=".", out="."):
    if pv is None:
        raise ImportError("pyvista is required for Section C: pip install pyvista")
    import os
    os.makedirs(out, exist_ok=True)
    pv.OFF_SCREEN = True
    pv.global_theme.background = "white"
    pv.global_theme.font.color = "black"
    internal, patches, tlabel = load_latest(case)
    tubes = patches.get("condenser")
    chip = patches.get("chip")
    pts = internal.cell_data_to_point_data()          # point data for contouring

    # --- view 1: geometry + liquid interface overview ---
    iface = pts.contour([0.5], scalars="alpha.water")
    p = pv.Plotter(off_screen=True, window_size=(1100, 950))
    add_outline(p, internal)
    if tubes is not None:
        p.add_mesh(tubes, color="#aeb4bf", smooth_shading=True)
    if chip is not None:
        p.add_mesh(chip, color="#c0392b")
    if iface.n_points:
        p.add_mesh(iface, color="#2c7fb8", opacity=0.55, smooth_shading=True)
    p.add_text(f"chamber + 42-tube bundle + liquid interface   ({tlabel})",
               font_size=10, color="black")
    iso_camera(p)
    p.screenshot(os.path.join(out, "view1_overview.png"))
    p.close()

    # --- view 2: temperature on a vertical slice ---
    sl = internal.slice(normal=SLICE_NORMAL)
    p = pv.Plotter(off_screen=True, window_size=(1100, 760))
    p.add_mesh(sl, scalars="T", cmap="inferno", clim=T_CLAMP,
               scalar_bar_args=dict(title="T [K]  (clamped)", color="black"))
    if tubes is not None:
        p.add_mesh(tubes.slice(normal=SLICE_NORMAL), color="black", line_width=2)
    p.add_text("temperature, mid-plane slice", font_size=10, color="black")
    p.view_xz()
    p.camera.zoom(1.3)
    p.screenshot(os.path.join(out, "view2_temperature.png"))
    p.close()

    # --- view 3: velocity magnitude on a vertical slice ---
    sl = internal.slice(normal=SLICE_NORMAL)
    umag = np.linalg.norm(sl["U"], axis=1)
    sl["|U|"] = np.clip(umag, 0, np.percentile(umag, 95))
    p = pv.Plotter(off_screen=True, window_size=(1100, 760))
    p.add_mesh(sl, scalars="|U|", cmap="viridis",
               scalar_bar_args=dict(title="|U| [m/s]  (clamped)", color="black"))
    if tubes is not None:
        p.add_mesh(tubes.slice(normal=SLICE_NORMAL), color="white", line_width=2)
    p.add_text("velocity magnitude, mid-plane slice", font_size=10, color="black")
    p.view_xz()
    p.camera.zoom(1.3)
    p.screenshot(os.path.join(out, "view3_velocity.png"))
    p.close()

    # --- view 4: liquid interface coloured by height ---
    iface = pts.contour([0.5], scalars="alpha.water")
    p = pv.Plotter(off_screen=True, window_size=(1100, 950))
    add_outline(p, internal)
    if tubes is not None:
        p.add_mesh(tubes, color="#d8dce3", opacity=0.45, smooth_shading=True)
    if iface.n_points:
        iface["height [mm]"] = iface.points[:, 2] * 1e3
        p.add_mesh(iface, scalars="height [mm]", cmap="ocean", smooth_shading=True,
                   scalar_bar_args=dict(title="height [mm]", color="black"))
    p.add_text("liquid / vapour interface  (alpha.water = 0.5)",
               font_size=10, color="black")
    iso_camera(p)
    p.screenshot(os.path.join(out, "view4_interface.png"))
    p.close()

    print(f"wrote 4 views ({tlabel}) to {out}")




################################################################################
#  SECTION D  -  PHASE-CHANGE CALIBRATION ORCHESTRATOR (HPC)
################################################################################
"""
Calibrate the interCondensatingEvaporatingFoam phase-change coefficients
(coeffE evaporation, coeffC condensation) against the MEASURED 42-tube
plain-copper boiling curve and CHF.

WHAT THIS IS
------------
An ORCHESTRATOR, not a sandbox run. Every objective evaluation launches a set
of full 3D VOF solves (one per wall superheat) on the refined mesh. Each solve
is hours-to-days of HPC wall time, so this script is meant to be driven by a
cluster scheduler, not executed interactively. It is provided so the calibration
loop is fully specified and reproducible.

METHOD
------
The constant (Lee-type) phase-change model relieves interfacial super-heat /
sub-cooling at a rate set by coeffE / coeffC [1/(s.K)]. For a heated chip held
at wall temperature T_w, the resolved interfacial evaporation + conduction +
convection produce a chip heat flux q''(T_w). Sweeping T_w builds a SIMULATED
boiling curve. We adjust (coeffE, coeffC) so that curve matches the measured
Rohsenow curve and so that the simulated curve turns over (vapour blanketing,
wall-T runaway) at the measured CHF.

Note the mapping is indirect and MESH-DEPENDENT: the Lee coefficient interacts
with cell size at the interface. Re-calibrate if the mesh changes. coeffE is the
primary knob for the boiling branch; coeffC mainly affects the condensing tubes.

EXTRACTION
----------
Each case writes chipHeatFlux.dat (see system/chipHeatFlux):
    time   q''[W/m2]   q''[W/cm2]   Q[W]
We take the time-average over the last `avg_window` fraction of the run as the
quasi-steady value. Confirm the functionObject compiles against your build.

USAGE (on a cluster)
--------------------
    python calibrate_phase_change.py --targets targets_42plain.json \
        --template ../ --runner slurm --max-iter 25
"""
import os, re, json, shutil, subprocess, argparse
import numpy as np

# ----- wall temperatures to probe the boiling branch (deg C -> K) -----
# chosen to span the measured Tsurf range; CHF point included to test turn-over
PROBE_TWALL_C = [50, 60, 70, 78, 85, 90]
TSAT_K = 338.0
AVG_WINDOW = 0.3          # average q'' over the last 30% of each run (quasi-steady)
CHF_PENALTY_WEIGHT = 2.0  # weight on reproducing the CHF turn-over


def load_targets(path):
    t = json.load(open(path))
    pts = t["points"]
    Ts = np.array([p["Tsurf_C"] for p in pts])
    q = np.array([p["q_Wcm2"] for p in pts])
    # monotone reference curve q_meas(Tsurf) by sorting + interpolation
    o = np.argsort(Ts)
    return Ts[o], q[o], float(t["CHF_Wcm2"])


def write_coeffs(case, coeffE, coeffC):
    """Patch constant/phaseChangeProperties for this candidate."""
    p = os.path.join(case, "constant", "phaseChangeProperties")
    txt = open(p).read()
    txt = re.sub(r"coeffC coeffC \[[^]]*\] [0-9.eE+-]+",
                 f"coeffC coeffC [0 0 -1 -1 0 0 0] {coeffC:g}", txt)
    txt = re.sub(r"coeffE coeffE \[[^]]*\] [0-9.eE+-]+",
                 f"coeffE coeffE [0 0 -1 -1 0 0 0] {coeffE:g}", txt)
    open(p, "w").write(txt)


def set_chip_Twall(case, Twall_K):
    """Set the chip patch fixedValue temperature in 0/T."""
    p = os.path.join(case, "0", "T")
    txt = open(p).read()
    # assumes a chip { type fixedValue; value uniform <T>; } entry exists
    txt = re.sub(r"(chip\s*\{[^}]*?value\s+uniform\s+)[0-9.eE+-]+",
                 rf"\g<1>{Twall_K:g}", txt, flags=re.S)
    open(p, "w").write(txt)


def run_case(case, runner):
    """Launch one solve. Returns when it finishes (blocking)."""
    if runner == "slurm":
        subprocess.run(["sbatch", "--wait", "Allrun.cluster"], cwd=case, check=True)
    else:  # local (only for a tiny smoke test, NOT a converged run)
        subprocess.run(["./Allrun"], cwd=case, check=True)


def read_steady_q(case):
    """Time-average q''[W/cm2] over the last AVG_WINDOW of chipHeatFlux.dat."""
    f = os.path.join(case, "chipHeatFlux.dat")
    rows = [l.split() for l in open(f) if l.strip() and not l.startswith("#")]
    t = np.array([float(r[0]) for r in rows])
    qcm2 = np.array([float(r[2]) for r in rows])
    n0 = int(len(t) * (1.0 - AVG_WINDOW))
    return float(np.mean(qcm2[n0:]))


def simulate_curve(template, coeffE, coeffC, runner, workdir="cal_runs"):
    """Run the probe set for one (coeffE, coeffC); return (Twall_C, q_sim[W/cm2])."""
    os.makedirs(workdir, exist_ok=True)
    q_sim = []
    for Tc in PROBE_TWALL_C:
        case = os.path.join(workdir, f"E{coeffE:g}_C{coeffC:g}_Tw{Tc}")
        if not os.path.isdir(case):
            shutil.copytree(template, case, ignore=shutil.ignore_patterns(
                "cal_runs", "VTK", "post", "0.0*", "processor*", "*.png"))
        write_coeffs(case, coeffE, coeffC)
        set_chip_Twall(case, Tc + 273.15)
        run_case(case, runner)
        q_sim.append(read_steady_q(case))
    return np.array(PROBE_TWALL_C, float), np.array(q_sim, float)


def objective(params, template, targets, runner):
    coeffE, coeffC = params
    Ts_m, q_m, chf = targets
    Tw, q_s = simulate_curve(template, coeffE, coeffC, runner)
    # interpolate measured curve onto the simulated wall temperatures
    q_m_at = np.interp(Tw, Ts_m, q_m)
    resid = q_s - q_m_at
    # CHF turn-over penalty: simulated curve should not exceed measured CHF before turn-over
    chf_pen = CHF_PENALTY_WEIGHT * max(0.0, q_s.max() - chf)
    rms = float(np.sqrt(np.mean(resid**2)))
    print(f"  coeffE={coeffE:.4g} coeffC={coeffC:.4g} -> RMS={rms:.3f} W/cm2, "
          f"q_sim_max={q_s.max():.1f}, CHFpen={chf_pen:.2f}")
    return rms + chf_pen


def run_calibrate(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="targets_42plain.json")
    ap.add_argument("--template", default="..")
    ap.add_argument("--runner", choices=["slurm", "local"], default="slurm")
    ap.add_argument("--max-iter", type=int, default=25)
    ap.add_argument("--E0", type=float, default=0.1)   # initial coeffE
    ap.add_argument("--C0", type=float, default=1.0)   # initial coeffC
    args = ap.parse_args(argv)

    targets = load_targets(args.targets)
    from scipy.optimize import minimize
    res = minimize(objective, x0=[args.E0, args.C0],
                   args=(args.template, targets, args.runner),
                   method="Nelder-Mead",
                   options={"maxiter": args.max_iter, "xatol": 1e-3, "fatol": 1e-2})
    print("\ncalibrated:", res.x, "final objective:", res.fun)
    json.dump({"coeffE": float(res.x[0]), "coeffC": float(res.x[1]),
               "objective_Wcm2": float(res.fun)},
              open("calibrated_coeffs.json", "w"), indent=1)




################################################################################
#  COMMAND-LINE DISPATCHER
################################################################################
def _usage():
    print(__doc__.split("Sections:")[0].strip())

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "model"
    rest = sys.argv[2:]
    if cmd == "model":
        run_model()
    elif cmd == "figures":
        run_publication()
    elif cmd == "postprocess":
        run_postprocess(rest[0] if rest else ".", rest[1] if len(rest) > 1 else ".")
    elif cmd == "calibrate":
        run_calibrate(rest)
    else:
        _usage()
