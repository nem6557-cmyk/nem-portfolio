"""
Subcooled pool-boiling solver (calibrated reduced-order model).

Heat balance at the chip surface, solved numerically for the surface temperature:

    q'' = sqrt( q_nc^2 + q_nb^2 )

  q_nc = natural-convection / subcooled single-phase term, driven by (T_surf - T_pool)
  q_nb = nucleate-boiling (Rohsenow) term,                 driven by (T_surf - T_sat)

Calibrated constants (this conversation):
  C_sf  = 0.0131   Rohsenow surface-fluid constant  -> TRANSFERS across geometry
  NC    = per-chamber single-phase factor           -> geometry-specific (9.0 for 33-tube, 3.5 for 42-tube)

CHF uses Kandlikar (2001) with a subcooling enhancement. The contact angle and the
subcooling coefficient are PLACEHOLDERS (no burnout data), so CHF magnitude is NOT
calibrated; only the trend (rises with subcooling) is mechanistic.
"""
import numpy as np
from scipy.optimize import brentq
from CoolProp.CoolProp import PropsSI

C_SF = 0.0131
G = 9.81
L_CHAR = 8.3e-3   # A/P for the 34.5 x 32 mm chip

_cache = {}
def water_props(T_sat_c):
    key = round(T_sat_c, 1)
    if key in _cache: return _cache[key]
    T = T_sat_c + 273.15
    pr = dict(
        rho_l=PropsSI('D','T',T,'Q',0,'Water'), rho_v=PropsSI('D','T',T,'Q',1,'Water'),
        hfg=PropsSI('H','T',T,'Q',1,'Water')-PropsSI('H','T',T,'Q',0,'Water'),
        sigma=PropsSI('I','T',T,'Q',0,'Water'), mu_l=PropsSI('V','T',T,'Q',0,'Water'),
        k_l=PropsSI('L','T',T,'Q',0,'Water'), cp_l=PropsSI('C','T',T,'Q',0,'Water'),
        beta=PropsSI('ISOBARIC_EXPANSION_COEFFICIENT','T',T,'Q',0,'Water'))
    pr['Pr'] = pr['mu_l']*pr['cp_l']/pr['k_l']
    _cache[key] = pr
    return pr

def q_nc(T_surf, T_pool, pr, NC, L=L_CHAR):
    dT = max(T_surf - T_pool, 1e-9)
    nu = pr['mu_l']/pr['rho_l']; al = pr['k_l']/(pr['rho_l']*pr['cp_l'])
    Ra = G*pr['beta']*dT*L**3/(nu*al)
    Nu = 0.15*Ra**(1/3.) if Ra > 1e7 else 0.54*Ra**0.25
    Nu = max(Nu, 0.27*Ra**0.25)
    return NC * Nu * pr['k_l']/L * dT

def q_nb(T_surf, T_sat, pr, C_sf=C_SF):
    dsup = T_surf - T_sat
    if dsup <= 0: return 0.0
    return pr['mu_l']*pr['hfg']*(G*(pr['rho_l']-pr['rho_v'])/pr['sigma'])**0.5 * \
           (pr['cp_l']*dsup/(C_sf*pr['hfg']*pr['Pr']))**3

def surface_temp(q_wcm2, T_sat, subcooling, NC, L=L_CHAR, C_sf=C_SF):
    """Solve for chip surface temperature [C] at a given heat flux [W/cm^2]."""
    T_pool = T_sat - subcooling
    pr = water_props(T_sat)
    q = q_wcm2*1e4
    f = lambda Ts: np.hypot(q_nc(Ts, T_pool, pr, NC, L), q_nb(Ts, T_sat, pr, C_sf)) - q
    return brentq(f, T_pool+1e-6, T_sat+160)

def partition(q_wcm2, T_sat, subcooling, NC, L=L_CHAR, C_sf=C_SF):
    """Return (single-phase fraction, boiling fraction) of the heat flux."""
    Ts = surface_temp(q_wcm2, T_sat, subcooling, NC, L, C_sf)
    pr = water_props(T_sat)
    a = q_nc(Ts, T_sat-subcooling, pr, NC, L); b = q_nb(Ts, T_sat, pr, C_sf)
    tot = np.hypot(a, b)
    return a*a/tot/tot*1.0, b*b/tot/tot*1.0   # energy shares (q_i^2 / q_tot^2)

def onb_flux(T_sat, subcooling, NC, L=L_CHAR):
    """Heat flux [W/cm^2] at onset of nucleate boiling (T_surf = T_sat)."""
    pr = water_props(T_sat)
    return q_nc(T_sat, T_sat-subcooling, pr, NC, L)/1e4

def chf_kandlikar(T_sat, subcooling, beta_deg=45.0, phi_deg=0.0, C_sub=0.0535):
    """Kandlikar 2001 CHF [W/cm^2]. ABSOLUTE IS UNCALIBRATED (placeholder beta, C_sub)."""
    pr = water_props(T_sat); b = np.radians(beta_deg); ph = np.radians(phi_deg)
    q_sat = pr['hfg']*pr['rho_v']**0.5*((1+np.cos(b))/16) * \
            (2/np.pi + np.pi/4*(1+np.cos(b))*np.cos(ph))**0.5 * \
            (pr['sigma']*G*(pr['rho_l']-pr['rho_v']))**0.25
    return q_sat/1e4 * (1 + C_sub*subcooling)

if __name__ == "__main__":
    for sc in (5, 15, 25, 35):
        Ts = surface_temp(40, 54, sc, 9.0); sp, bo = partition(40, 54, sc, 9.0)
        print(f"subcool={sc:2d}K @40W/cm2: T_surf={Ts:.1f}C  single-phase={sp*100:.0f}%  boiling={bo*100:.0f}%  CHF~{chf_kandlikar(54,sc):.0f}")
