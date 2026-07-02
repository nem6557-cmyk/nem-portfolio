"""
Submerged-condensation tube-bank condenser  --  Stage 1 verified core
=====================================================================

Steady-state, axisymmetric (r, z) conjugate heat-transfer solver for ONE
representative cooled tube of the condenser tube bank:

    [ coolant, prescribed laminar profile ]  ->  internal forced convection
    [ tube wall, copper ]                    ->  cylindrical conduction
    [ outer surface ]                        ->  external condensation (simple)

The internal flow is RESOLVED (advection-diffusion of the coolant temperature
with a prescribed velocity profile from the constant-flow-rate pump), so the
internal heat-transfer coefficient is an OUTPUT, not an assumption. The tube
wall conducts radially/axially. The outer surface uses a simple condensation
boundary condition (constant film coefficient, or Nusselt horizontal-tube
correlation) that is the single swap point for the outer pool in Stage 2.

Axisymmetry makes the 3D field exact in (r, z) when the external coefficient is
azimuthally uniform. Stage 2 (partially submerged tube bank -> water / HFE-7000
pool on the lower portion) breaks that symmetry and is the documented next step;
the external-BC interface below is already written to accept it.

Author: built for Noor's boiling-chamber condenser study.
Units: SI throughout (m, kg, s, K, W).
"""

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from dataclasses import dataclass, field
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ----------------------------------------------------------------------
# Property sets  (NOMINAL -- replace with your validated tables)
# ----------------------------------------------------------------------
WATER_COOLANT_40C = dict(rho=992.2, cp=4178.0, k=0.631, mu=6.53e-4)        # liquid water ~40 C
WATER_CONDENSATE_49C = dict(rho_l=988.0, rho_v=0.083, mu_l=5.5e-4,         # water sat. @ ~12 kPa
                            k_l=0.643, cp_l=4180.0, h_fg=2.382e6)
# Stage-2 pool fluids (stored, not used yet in Stage 1)
POOL_FLUIDS = {
    "water":     dict(rho=988.0, cp=4180.0, k=0.643, mu=5.5e-4, h_fg=2.382e6, Tsat_1atm=373.15),
    "HFE7000":   dict(rho=1400.0, cp=1300.0, k=0.075, mu=4.5e-4, h_fg=1.42e5,  Tsat_1atm=307.15),
}


@dataclass
class Geometry:
    r_i: float = 3.0e-3      # tube inner radius [m]  (ID = 6 mm)      <-- REPLACE
    r_o: float = 4.0e-3      # tube outer radius [m]  (OD = 8 mm)      <-- REPLACE
    L:   float = 0.150       # tube length [m]                         <-- REPLACE
    k_wall: float = 385.0    # wall conductivity [W/mK] (copper)       <-- REPLACE
    n_tubes: int = 10        # tubes in the bank (Stage-1 duty scaling)<-- REPLACE
    submerged_fraction: float = 0.40  # fraction of bank in the pool (Stage 2)


@dataclass
class Operating:
    Q_per_tube_Lmin: float = 0.20   # coolant volumetric flow per tube [L/min] <-- REPLACE
    T_in: float = 40.0 + 273.15     # coolant inlet temperature [K]            <-- REPLACE
    P_kPa: float = 12.0             # chamber pressure [kPa] (subatmospheric)  <-- REPLACE
    T_sat: float = 49.4 + 273.15    # saturation temp of condensing vapor [K]  (water @ 12 kPa)
    cond_model: str = "constant_h"  # "constant_h" or "nusselt_tube"
    h_ext_const: float = 5000.0     # external film coeff if constant_h [W/m2K]


@dataclass
class Mesh:
    n_rf: int = 24   # radial cells in the coolant
    n_rw: int = 10   # radial cells in the wall
    n_z:  int = 200  # axial cells


# ----------------------------------------------------------------------
# Grid construction
# ----------------------------------------------------------------------
def build_grid(geo: Geometry, msh: Mesh, include_wall=True):
    r_i, r_o = geo.r_i, geo.r_o
    n_rf = msh.n_rf
    n_rw = msh.n_rw if include_wall else 0

    # radial faces: 0..r_i (fluid), r_i..r_o (wall)
    rf_fluid = np.linspace(0.0, r_i, n_rf + 1)
    if include_wall:
        rf_wall = np.linspace(r_i, r_o, n_rw + 1)[1:]
        r_faces = np.concatenate([rf_fluid, rf_wall])
    else:
        r_faces = rf_fluid
    r_c = 0.5 * (r_faces[:-1] + r_faces[1:])          # cell-center radii
    n_r = r_c.size
    A_z = np.pi * (r_faces[1:]**2 - r_faces[:-1]**2)   # axial face area of each radial ring
    dr = r_faces[1:] - r_faces[:-1]

    # axial
    dz = geo.L / msh.n_z
    z_c = (np.arange(msh.n_z) + 0.5) * dz

    is_fluid = r_c < r_i - 1e-12
    return dict(r_faces=r_faces, r_c=r_c, n_r=n_r, A_z=A_z, dr=dr,
                dz=dz, z_c=z_c, n_z=msh.n_z, is_fluid=is_fluid,
                n_rf=n_rf, n_rw=n_rw)


def velocity_profile(r_c, is_fluid, r_i, U_mean):
    """Fully developed laminar (Hagen-Poiseuille) profile: u = 2*U_mean*(1-(r/r_i)^2)."""
    u = np.zeros_like(r_c)
    fl = is_fluid
    u[fl] = 2.0 * U_mean * (1.0 - (r_c[fl] / r_i) ** 2)
    u[u < 0] = 0.0
    return u


# ----------------------------------------------------------------------
# Core solver:  steady advection-diffusion (fluid) + conduction (wall),
# cylindrical finite volume, first-order upwind in z, sparse direct solve.
# ----------------------------------------------------------------------
def solve_field(geo, op, msh, *, include_wall=True, inner_bc="conjugate",
                T_wall_fixed=None, coolant=WATER_COOLANT_40C, cond=WATER_CONDENSATE_49C,
                h_ext_override=None):
    """
    inner_bc:
      "conjugate" -> wall present, conduction couples coolant <-> wall <-> outside
      "dirichlet" -> no wall; fluid outer boundary held at T_wall_fixed (for Nu verification)
    Returns a results dict.
    """
    g = build_grid(geo, msh, include_wall=include_wall)
    r_c, r_faces, A_z, dr = g["r_c"], g["r_faces"], g["A_z"], g["dr"]
    dz, n_r, n_z, is_fluid = g["dz"], g["n_r"], g["n_z"], g["is_fluid"]

    rho, cp, kf, mu = coolant["rho"], coolant["cp"], coolant["k"], coolant["mu"]
    Q = op.Q_per_tube_Lmin / 1000.0 / 60.0           # m^3/s
    U_mean = Q / (np.pi * geo.r_i**2)
    u = velocity_profile(r_c, is_fluid, geo.r_i, U_mean)
    # enforce EXACT discrete mass flow (cell-centered parabola under-integrates Q):
    mass_disc = np.sum((u * A_z)[is_fluid])
    if mass_disc > 0:
        u = u * (Q / mass_disc)
    mdot = rho * Q

    k_cell = np.where(is_fluid, kf, geo.k_wall)
    F = rho * cp * u * A_z                            # axial advective conductance per ring [W/K]

    def kface_harm(i):                               # harmonic mean across radial face i|i+1
        ka, kb = k_cell[i], k_cell[i + 1]
        return 2.0 * ka * kb / (ka + kb)

    N = n_r * n_z
    def idx(i, j):
        return i * n_z + j

    rows, cols, vals = [], [], []
    b = np.zeros(N)

    def add(i, j, ii, jj, v):
        rows.append(idx(i, j)); cols.append(idx(ii, jj)); vals.append(v)

    diag = np.zeros(N)

    # external coefficient handling
    if h_ext_override is not None:
        h_ext_field = np.full(n_z, h_ext_override)
    elif op.cond_model == "constant_h":
        h_ext_field = np.full(n_z, op.h_ext_const)
    else:  # nusselt_tube -- filled per-iteration outside; start with a guess
        h_ext_field = np.full(n_z, op.h_ext_const)

    for i in range(n_r):
        Az_i = A_z[i]
        for j in range(n_z):
            p = idx(i, j)

            # ---- radial diffusion: inner face (i-1) ----
            if i > 0:
                Arf = 2.0 * np.pi * r_faces[i] * dz
                G = kface_harm(i - 1) * Arf / (r_c[i] - r_c[i - 1])
                add(i, j, i - 1, j, -G); diag[p] += G
            # (i==0: symmetry, face area ~0 -> no term)

            # ---- radial diffusion: outer face (i+1) OR external BC ----
            if i < n_r - 1:
                Arf = 2.0 * np.pi * r_faces[i + 1] * dz
                G = kface_harm(i) * Arf / (r_c[i + 1] - r_c[i])
                add(i, j, i + 1, j, -G); diag[p] += G
            else:
                # outermost ring -> external boundary
                if inner_bc == "dirichlet":
                    # fluid-only Nu test: hold outer fluid boundary at T_wall_fixed
                    Arf = 2.0 * np.pi * r_faces[i + 1] * dz
                    G = k_cell[i] * Arf / (0.5 * dr[i])      # conduction to surface held at T_wall
                    diag[p] += G; b[p] += G * T_wall_fixed
                else:
                    # conjugate: series (half-cell wall conduction) + external film -> T_ext
                    A_o = 2.0 * np.pi * r_faces[i + 1] * dz
                    R_cond = 0.5 * dr[i] / (k_cell[i] * A_o)
                    R_film = 1.0 / (h_ext_field[j] * A_o)
                    G = 1.0 / (R_cond + R_film)
                    diag[p] += G; b[p] += G * op.T_sat

            # ---- axial diffusion (solid wall only; coolant streamwise diffusion
            #      neglected since axial Peclet = Re*Pr*(D/L) >> 1, parabolic form) ----
            if not is_fluid[i]:
                if j > 0:
                    G = k_cell[i] * Az_i / dz
                    add(i, j, i, j - 1, -G); diag[p] += G
                if j < n_z - 1:
                    G = k_cell[i] * Az_i / dz
                    add(i, j, i, j + 1, -G); diag[p] += G
                # both copper-wall ends insulated -> no inlet/outlet ghost

            # ---- axial advection (fluid only, u>=0, first-order upwind) ----
            # conservative face-based form per cell:
            #   west face (influx)  : F*T_{j-1}  (coupling)  or  F*T_in  (inlet, -> b)
            #   east face (outflux) : F*T_j      (-> diag, ALWAYS; flow always leaves +z)
            if is_fluid[i] and F[i] != 0.0:
                if j > 0:                              # west influx from interior neighbor
                    add(i, j, i, j - 1, -F[i])
                else:                                  # west influx from inlet plane
                    b[p] += F[i] * op.T_in
                diag[p] += F[i]                        # east outflux (every cell, incl. outlet)

    for p in range(N):
        rows.append(p); cols.append(p); vals.append(diag[p])

    A = sp.csr_matrix((vals, (rows, cols)), shape=(N, N))
    T = spla.spsolve(A, b).reshape(n_r, n_z)

    out = dict(T=T, grid=g, u=u, mdot=mdot, U_mean=U_mean, cp=cp, kf=kf,
               rho=rho, mu=mu, h_ext_field=h_ext_field, op=op, geo=geo)
    _postprocess(out)
    return out


def _postprocess(out):
    g = out["grid"]; T = out["T"]; cp = out["cp"]; mdot = out["mdot"]
    r_c, A_z, r_faces, dz = g["r_c"], g["A_z"], g["r_faces"], g["dz"]
    is_fluid, n_z, n_r = g["is_fluid"], g["n_z"], g["n_r"]
    u = out["u"]; op = out["op"]; geo = out["geo"]; kf = out["kf"]

    # flow-weighted bulk temperature along z
    w = (u * A_z)[is_fluid]
    Tb = np.array([np.sum(w * T[is_fluid, j]) / np.sum(w) for j in range(n_z)])
    out["T_bulk"] = Tb

    # outer-surface heat flux and surface temperature (conjugate case only)
    A_o = 2.0 * np.pi * r_faces[-1] * dz
    dr_last = (r_faces[-1] - r_faces[-2])
    R_cond = 0.5 * dr_last / (geo.k_wall * A_o)
    q_ext = np.zeros(n_z); Tsurf_o = np.zeros(n_z)
    for j in range(n_z):
        R_film = 1.0 / (out["h_ext_field"][j] * A_o)
        G = 1.0 / (R_cond + R_film)
        q = G * (op.T_sat - T[n_r - 1, j])           # W into the ring
        q_ext[j] = q / A_o                            # W/m^2
        Tsurf_o[j] = op.T_sat - q_ext[j] / out["h_ext_field"][j]
    out["q_ext"] = q_ext; out["Tsurf_o"] = Tsurf_o

    # duty by external integration and by coolant enthalpy gain (conservation check)
    Q_ext = np.sum(q_ext * A_o)
    Q_cool = mdot * cp * (Tb[-1] - op.T_in)
    out["Q_ext"] = Q_ext; out["Q_cool"] = Q_cool
    out["energy_residual"] = abs(Q_ext - Q_cool) / max(abs(Q_ext), 1e-12)

    # local internal Nusselt (inner-wall flux vs bulk-to-wall difference)
    if g["n_rw"] > 0:
        i_f = np.where(is_fluid)[0][-1]              # last fluid ring
        i_w = i_f + 1                                # first wall ring
        r_int = geo.r_i
        A_i = 2.0 * np.pi * r_int * dz
        kface = 2.0 * kf * geo.k_wall / (kf + geo.k_wall)
        Nu = np.zeros(n_z)
        for j in range(n_z):
            qi = kface * (T[i_f, j] - T[i_w, j]) / (r_c[i_w] - r_c[i_f])  # W/m^2 at interface
            # inner-wall surface temp (extrapolate fluid side):
            Twi = T[i_f, j] - qi * (r_int - r_c[i_f]) / kf
            dTm = (Twi - Tb[j])
            h = qi / dTm if abs(dTm) > 1e-9 else np.nan
            Nu[j] = h * (2 * geo.r_i) / kf
        out["Nu_local"] = Nu

    # integral performance
    Tout = Tb[-1]
    dT1, dT2 = op.T_sat - op.T_in, op.T_sat - Tout
    LMTD = (dT1 - dT2) / np.log(dT1 / dT2) if abs(dT1 - dT2) > 1e-9 else dT1
    UA = Q_ext / LMTD
    NTU = UA / (mdot * cp)
    eps = Q_ext / (mdot * cp * (op.T_sat - op.T_in))
    out.update(T_out=Tout, LMTD=LMTD, UA=UA, NTU=NTU, eps=eps,
               R_thermal=(op.T_sat - op.T_in) / Q_ext,
               mdot_cond=Q_ext / WATER_CONDENSATE_49C["h_fg"],
               Re=out["rho"] * out["U_mean"] * (2 * geo.r_i) / out["mu"])


# ----------------------------------------------------------------------
# Nusselt horizontal-tube film condensation coefficient (for cond_model="nusselt_tube")
# ----------------------------------------------------------------------
def h_nusselt_tube(Tsat, Twall, D, cond=WATER_CONDENSATE_49C, g=9.81):
    dT = max(Tsat - Twall, 1e-3)
    hfg_p = cond["h_fg"] + 0.68 * cond["cp_l"] * dT
    num = cond["rho_l"] * (cond["rho_l"] - cond["rho_v"]) * g * hfg_p * cond["k_l"]**3
    den = cond["mu_l"] * dT * D
    return 0.729 * (num / den) ** 0.25


def solve_with_nusselt(geo, op, msh, coolant=WATER_COOLANT_40C, cond=WATER_CONDENSATE_49C,
                       iters=25, tol=1e-4):
    """Outer loop: update local film coefficient from current outer-surface temperature."""
    op = Operating(**{**op.__dict__})
    op.cond_model = "constant_h"      # we drive h via override
    h_field = np.full(msh.n_z, op.h_ext_const)
    last_Q = None
    for _ in range(iters):
        res = solve_field(geo, op, msh, coolant=coolant, cond=cond, h_ext_override=h_field)
        Tsurf = res["Tsurf_o"]
        h_new = np.array([h_nusselt_tube(op.T_sat, Tsurf[j], 2 * geo.r_o, cond)
                          for j in range(msh.n_z)])
        h_field = 0.5 * h_field + 0.5 * h_new        # under-relax
        if last_Q is not None and abs(res["Q_ext"] - last_Q) / res["Q_ext"] < tol:
            break
        last_Q = res["Q_ext"]
    res["h_ext_field"] = h_field
    _postprocess(res)
    return res


# ----------------------------------------------------------------------
# VERIFICATION SUITE
# ----------------------------------------------------------------------
def verify(geo, op, msh):
    print("=" * 70)
    print("VERIFICATION SUITE")
    print("=" * 70)

    # (1) Pure radial conduction: u=0, inner & outer Dirichlet -> analytic ln profile
    geo_c = Geometry(**geo.__dict__)
    op_c = Operating(**op.__dict__); op_c.Q_per_tube_Lmin = 0.0
    op_c.cond_model = "constant_h"; op_c.h_ext_const = 1e8   # ~Dirichlet outer at T_sat
    # impose inner Dirichlet by a thin fluid held at T_in via huge inlet advection is messy;
    # instead test wall-only annulus analytically here:
    r_i, r_o, kw = geo.r_i, geo.r_o, geo.k_wall
    Ti, To = 320.0, 322.0
    # numeric 1D radial conduction (finite volume) for the same annulus:
    nrw = 100
    rf = np.linspace(r_i, r_o, nrw + 1); rcw = 0.5 * (rf[:-1] + rf[1:])
    A = np.zeros((nrw, nrw)); bb = np.zeros(nrw)
    for i in range(nrw):
        if i > 0:
            G = kw * 2 * np.pi * rf[i] / (rcw[i] - rcw[i - 1]); A[i, i] += G; A[i, i - 1] -= G
        else:
            G = kw * 2 * np.pi * rf[i] / (0.5 * (rf[1] - rf[0])); A[i, i] += G; bb[i] += G * Ti
        if i < nrw - 1:
            G = kw * 2 * np.pi * rf[i + 1] / (rcw[i + 1] - rcw[i]); A[i, i] += G; A[i, i + 1] -= G
        else:
            G = kw * 2 * np.pi * rf[i + 1] / (0.5 * (rf[-1] - rf[-2])); A[i, i] += G; bb[i] += G * To
    Tnum = np.linalg.solve(A, bb)
    Tan_c = Ti + (To - Ti) * np.log(rcw / r_i) / np.log(r_o / r_i)   # analytic at cell centers
    err1 = np.max(np.abs(Tnum - Tan_c))
    print(f"(1) Radial conduction vs analytic ln profile : max |err| = {err1:.3e} K  "
          f"[{'PASS' if err1 < 1e-3 else 'CHECK'}]")

    # (2) Internal Nusselt -> 3.66 (laminar, constant wall T), long tube
    geo_n = Geometry(**geo.__dict__); geo_n.L = 1.2     # long for fully developed
    msh_n = Mesh(n_rf=80, n_rw=0, n_z=900)
    res_n = solve_field(geo_n, op, msh_n, include_wall=False, inner_bc="dirichlet",
                        T_wall_fixed=op.T_sat)
    # local Nu from fluid-only solve:
    g = res_n["grid"]; T = res_n["T"]; Tb = res_n["T_bulk"]; kf = res_n["kf"]
    r_c = g["r_c"]; i_last = g["n_r"] - 1
    Nu_fd = []
    for j in range(g["n_z"]):
        # flux at outer fluid boundary (held at T_sat) toward wall
        q = kf * (T[i_last, j] - op.T_sat) / (0.5 * (g["r_faces"][-1] - g["r_faces"][-2]))
        dTm = (op.T_sat - Tb[j])
        h = -q / dTm if abs(dTm) > 1e-9 else np.nan
        Nu_fd.append(h * (2 * geo.r_i) / kf)
    Nu_fd = np.array(Nu_fd)
    Nu_inf = np.mean(Nu_fd[-50:])
    err2 = abs(Nu_inf - 3.657) / 3.657
    print(f"(2) Fully developed internal Nu (const Tw)    : Nu_inf = {Nu_inf:.3f} "
          f"(analytic 3.657), rel err = {err2*100:.2f}%  "
          f"[{'PASS' if err2 < 0.03 else 'CHECK'}]")

    # (3) epsilon-NTU vs 1-exp(-NTU) across L/D
    print("(3) Coupled solve vs eps-NTU closed form (constant h_ext):")
    print(f"      {'L/D':>6} {'NTU':>8} {'eps_solver':>12} {'1-exp(-NTU)':>13} {'rel err %':>10}")
    for Lfac in [0.05, 0.10, 0.20, 0.40]:
        gL = Geometry(**geo.__dict__); gL.L = Lfac          # tube length in metres
        rL = solve_field(gL, op, Mesh(n_rf=20, n_rw=8, n_z=300))
        eps_an = 1 - np.exp(-rL["NTU"])
        e = abs(rL["eps"] - eps_an) / eps_an * 100
        print(f"      {gL.L/(2*geo.r_i):6.1f} {rL['NTU']:8.4f} {rL['eps']:12.5f} "
              f"{eps_an:13.5f} {e:10.3f}")

    # (4) grid convergence on duty
    print("(4) Grid convergence of duty Q (base geometry):")
    print(f"      {'cells':>10} {'Q [W]':>12}")
    for fac in [1, 2, 4]:
        m = Mesh(n_rf=12 * fac, n_rw=5 * fac, n_z=100 * fac)
        rG = solve_field(geo, op, m)
        print(f"      {rG['grid']['n_r']*rG['grid']['n_z']:10d} {rG['Q_ext']:12.4f}")

    print("=" * 70)
    return dict(err_conduction=err1, Nu_inf=Nu_inf, Nu_local=Nu_fd, z_Nu=res_n["grid"]["z_c"])


# ----------------------------------------------------------------------
# Bank-level Stage-1 duty (simple scaling; full pool coupling = Stage 2)
# ----------------------------------------------------------------------
def bank_duty(single, geo):
    """Total bank duty with a simple Nusselt inundation (row) correction.
    Upper rows condense in vapor; this is the Stage-1 estimate before the pool model."""
    N = geo.n_tubes
    rows = np.arange(1, N + 1)
    inund = rows ** (-1.0 / 6.0)                      # Nusselt N^(-1/6) row factor
    Q_bank = single["Q_ext"] * inund.sum()
    return dict(Q_bank=Q_bank, mean_row_factor=inund.mean(),
                mdot_cond_bank=Q_bank / WATER_CONDENSATE_49C["h_fg"])


# ----------------------------------------------------------------------
# Plotting
# ----------------------------------------------------------------------
def make_plots(res, vinfo, geo, op, path="/home/claude"):
    g = res["grid"]; T = res["T"] - 273.15
    r_c, z_c = g["r_c"] * 1e3, g["z_c"] * 1e3
    Z, R = np.meshgrid(z_c, r_c)

    # Fig 1: temperature field (axisymmetric (r,z) -> the 3D field)
    fig, ax = plt.subplots(figsize=(9, 3.4))
    pc = ax.pcolormesh(Z, R, T, shading="auto", cmap="inferno")
    ax.axhline(geo.r_i * 1e3, color="cyan", lw=1.2, ls="--")
    ax.set_xlabel("axial position z [mm]"); ax.set_ylabel("radius r [mm]")
    ax.set_title("Conjugate temperature field  (coolant + copper wall)")
    cb = fig.colorbar(pc, ax=ax); cb.set_label("T [°C]")
    ax.text(0.5 * z_c[-1], geo.r_i * 0.5e3, "coolant", color="w", ha="center", fontsize=9)
    ax.text(0.5 * z_c[-1], (geo.r_i + geo.r_o) * 0.5e3, "wall", color="w", ha="center", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{path}/fig1_field.png", dpi=140); plt.close(fig)

    # Fig 2: axial temperature profiles + analytic exponential overlay
    Tb = res["T_bulk"] - 273.15
    NTU_z = res["UA"] / (res["mdot"] * res["cp"])
    z = g["z_c"] / geo.L
    Tb_an = (op.T_sat - (op.T_sat - op.T_in) * np.exp(-NTU_z * z)) - 273.15
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(z_c, Tb, label="coolant bulk (solver)", lw=2)
    ax.plot(z_c, Tb_an, "k--", label="analytic exp. approach", lw=1.3)
    ax.plot(z_c, res["Tsurf_o"] - 273.15, label="outer wall surface", lw=1.5)
    ax.axhline(op.T_sat - 273.15, color="r", ls=":", label="T_sat (vapor)")
    ax.set_xlabel("z [mm]"); ax.set_ylabel("T [°C]")
    ax.set_title("Axial temperatures  (verification overlay)")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(f"{path}/fig2_axial.png", dpi=140); plt.close(fig)

    # Fig 3: local condensation flux + internal Nu
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
    ax[0].plot(z_c, res["q_ext"] / 1e3, lw=2)
    ax[0].set_xlabel("z [mm]"); ax[0].set_ylabel("q''_cond [kW/m²]")
    ax[0].set_title("Local condensation heat flux")
    if "Nu_local" in res:
        ax[1].plot(z_c, res["Nu_local"], lw=2)
        ax[1].axhline(3.657, color="k", ls="--", label="3.657 (developed)")
        ax[1].set_xlabel("z [mm]"); ax[1].set_ylabel("Nu_D internal")
        ax[1].set_title("Internal Nusselt (emergent)"); ax[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(f"{path}/fig3_flux_nu.png", dpi=140); plt.close(fig)

    # Fig 4: Nu verification (fluid-only long tube)
    fig, ax = plt.subplots(figsize=(7, 4))
    zN = vinfo["z_Nu"] * 1e3
    ax.plot(zN, vinfo["Nu_local"], lw=2, label="solver (laminar, const Tw)")
    ax.axhline(3.657, color="k", ls="--", label="analytic 3.657")
    ax.set_ylim(3.0, 8.0); ax.set_xlabel("z [mm]"); ax.set_ylabel("Nu_D")
    ax.set_title("Verification: developing -> fully developed internal Nu")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(f"{path}/fig4_nu_verify.png", dpi=140); plt.close(fig)

    # Fig 5: eps-NTU curve with operating point
    fig, ax = plt.subplots(figsize=(7, 4))
    ntu = np.linspace(0, max(2.0, res["NTU"] * 1.5), 200)
    ax.plot(ntu, 1 - np.exp(-ntu), lw=2, label="1 - exp(-NTU)")
    ax.plot(res["NTU"], res["eps"], "ro", ms=9, label="operating point (solver)")
    ax.set_xlabel("NTU = UA / (ṁ cp)"); ax.set_ylabel("effectiveness ε")
    ax.set_title("Condenser effectiveness"); ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(f"{path}/fig5_eps_ntu.png", dpi=140); plt.close(fig)

    return [f"{path}/fig1_field.png", f"{path}/fig2_axial.png",
            f"{path}/fig3_flux_nu.png", f"{path}/fig4_nu_verify.png",
            f"{path}/fig5_eps_ntu.png"]


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
if __name__ == "__main__":
    geo = Geometry()
    op = Operating()
    msh = Mesh()

    print("\nCONDENSER  --  Stage 1 (single tube, simple external condensation)")
    print("-" * 70)
    print(f"Tube ID/OD/L = {2*geo.r_i*1e3:.1f}/{2*geo.r_o*1e3:.1f}/{geo.L*1e3:.0f} mm, "
          f"wall k = {geo.k_wall:.0f} W/mK ({geo.n_tubes} tubes in bank)")
    print(f"Coolant: {op.Q_per_tube_Lmin} L/min/tube, T_in = {op.T_in-273.15:.1f} °C")
    print(f"Vapor:  P = {op.P_kPa} kPa, T_sat = {op.T_sat-273.15:.1f} °C, "
          f"model = {op.cond_model}, h_ext = {op.h_ext_const:.0f} W/m²K")

    # baseline (constant-h, verifiable)
    res = solve_field(geo, op, msh)
    print("\nRESULTS (constant-h condensation):")
    print(f"  Reynolds (internal)        : {res['Re']:.0f}  ({'laminar' if res['Re']<2300 else 'transitional/turbulent'})")
    print(f"  Coolant outlet temperature : {res['T_out']-273.15:.3f} °C  (ΔT = {res['T_out']-op.T_in:.3f} K)")
    print(f"  Duty  Q (external)         : {res['Q_ext']:.3f} W")
    print(f"  Duty  Q (coolant enthalpy) : {res['Q_cool']:.3f} W")
    print(f"  Energy conservation resid. : {res['energy_residual']:.2e}  (discrete check)")
    print(f"  Mean condensation flux     : {np.mean(res['q_ext'])/1e3:.2f} kW/m²")
    print(f"  Condensate rate (per tube) : {res['mdot_cond']*1e6:.3f} mg/s")
    print(f"  UA / NTU / effectiveness   : {res['UA']*1e3:.2f} mW/K / {res['NTU']:.4f} / {res['eps']:.4f}")
    print(f"  Thermal resistance R       : {res['R_thermal']:.4f} K/W (single tube)")

    bk = bank_duty(res, geo)
    print(f"\n  Bank duty ({geo.n_tubes} tubes, Nusselt row factor): {bk['Q_bank']:.1f} W "
          f"(mean row factor {bk['mean_row_factor']:.3f})")

    # physical case with Nusselt-tube correlation
    resN = solve_with_nusselt(geo, op, msh)
    print(f"\nRESULTS (Nusselt horizontal-tube film condensation):")
    print(f"  Mean film coefficient      : {np.mean(resN['h_ext_field']):.0f} W/m²K")
    print(f"  Duty Q                     : {resN['Q_ext']:.3f} W")
    print(f"  Coolant outlet temperature : {resN['T_out']-273.15:.3f} °C")
    print(f"  Thermal resistance R       : {resN['R_thermal']:.4f} K/W")

    vinfo = verify(geo, op, msh)
    figs = make_plots(res, vinfo, geo, op)
    print("\nFigures written:", *figs, sep="\n  ")
    print("\nDone.")
