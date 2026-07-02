#!/usr/bin/env python3
"""
================================================================================
 chamber_field3d.py
 3D FIELD RECONSTRUCTION of the subcooled pool-boiling chamber for ParaView.

 IMPORTANT - WHAT THIS IS AND IS NOT
   This is NOT a CFD / VOF solution. It does not solve the Navier-Stokes,
   energy, or phase-change equations. It is a model-driven reconstruction:
   the chamber operating point (chip temperature, saturation temperature,
   pool subcooling, coolant temperatures) is taken from the *validated*
   reduced-order model, then mapped onto the 3D chamber geometry with
   physically-motivated spatial profiles (thermal boundary layers, a buoyant
   vapor plume over the chip, condensation at the submerged tube bundle, a
   vapor headspace set by the liquid fill).

   Use it to visualize and compare the configurations in ParaView. Do NOT
   present it as a numerically resolved VOF result. For that, run the
   OpenFOAM case provided alongside this file.

 Output (ParaView, open the .vti / .pvd files):
   fields/snapshot_<cond>_<evap>.vti     steady field for each configuration
   fields/timeseries_42_plain.pvd        bubble-plume animation (one config)

 Run:  python chamber_field3d.py
 Deps: numpy, pyevtk, matplotlib (for the sanity-check slices), CoolProp
================================================================================
"""
import os
import numpy as np
from pyevtk.hl import imageToVTK
import chamber_solver_single as cs

OUT = "fields"
os.makedirs(OUT, exist_ok=True)
os.makedirs(f"{OUT}/ts", exist_ok=True)

# ---- per-condenser enclosure [m] ----
#   33-tube (CFD_Next_Gen.step):  120.5 x 154.2 x 31.8 mm   single 5-row bank, 33 tubes
#   42-tube (per build spec):      80.0 x  80.0 x 42.0 mm   single bank, 42 tubes
#   66-tube (Full_Assembly..):    ~120  x 120   x 40   mm   height approximate
# Enclosure HEIGHT differs by condenser: 33-tube ~32 mm, 42-tube 42 mm.
ENCL = {
    "33": dict(W=0.1205, D=0.1542, H=0.0318, od=0.00476,  L=0.095),
    "42": dict(W=0.0800, D=0.0800, H=0.0420, od=0.003175, L=0.0626),
    "66": dict(W=0.1205, D=0.1205, H=0.0400, od=0.002,    L=0.095),
}
FILL = 0.40    # liquid fill: 40% of the chamber volume is liquid
CHIP_HX, CHIP_HY = 0.01725, 0.016         # 34.5 x 32 mm chip half-extents
G, BETA, LCHIP = 9.81, 4.0e-4, 0.012      # buoyancy scaling
R66 = 11.1 * 0.78e-3

# current-configuration geometry globals (set per condenser before building fields)
W = D = H = XC = YC = LEVEL = ZBAND_C = _OD = _L = None
def set_geometry(cond):
    global W, D, H, XC, YC, LEVEL, ZBAND_C, _OD, _L
    g = ENCL[cond]; W, D, H = g["W"], g["D"], g["H"]; XC, YC = W / 2, D / 2
    LEVEL = FILL * H; ZBAND_C = 0.52 * H; _OD = g["od"]; _L = g["L"]
def grid_counts():
    return max(40, int(W / 0.0015)), max(40, int(D / 0.0016)), max(26, int(H / 0.0011))

CHF = {"33": {"plain": 114, "micro": 174}, "42": {"plain": 65, "micro": 125},
       "66": {"plain": 114, "micro": 174}}

def operating_point(cond, evap, frac=0.60, Tin=30.0):
    """Chip/pool/coolant temperatures from the validated reduced-order model."""
    chf = CHF[cond][evap]; q = frac * chf; Q = q * 11.04
    if cond in ("33", "42"):
        ch = f"{cond}-tube"; Tsat, sub = cs.predict_operating(q, Tin, ch)
        Ts = cs.chip_temp_from_geometry(q, Tin, ch, cs.GEOM[ch]["NC"], chip=evap)
        md = cs.GEOM[ch]["mdot_gps"] / 1000.0
    else:
        d, e, f = cs.OP_SUB["33-tube"]; sub = max(d * Tin + e * Q + f, 0.0)
        Tb = Tin + Q * R66; Tsat = Tb + sub
        Ts = cs.chip_surface_temp(q, Tsat, sub, 9.0, chip=evap); md = 78 / 1000.0
    Tout = Tin + Q / (md * 4180.0)
    return dict(q=q, Tsurf=Ts, Tsat=Tsat, sub=sub, Tbulk=Tsat - sub, Tin=Tin, Tout=Tout)

def tube_centers(cond):
    """Tube centers placed in the chamber cross-section (x,z) [m], at TRUE CAD scale."""
    if cond == "33":
        c = np.load("c33.npy")                          # 33 tubes, single 5-row bank
    elif cond == "42":
        c = np.load("c42.npy")[:42]                     # single bank, 42 tubes
    else:  # 66-tube staggered bundle (generated, ~60 x 12 mm cross-section)
        xs = np.linspace(-30, 30, 11); zs = np.linspace(-6, 6, 6); pts = []
        for j, z in enumerate(zs):
            off = (xs[1] - xs[0]) / 2 if j % 2 else 0
            for x in xs:
                pts.append((x + off, z))
        c = np.array(pts[:66])
    c = (c - c.mean(0)).astype(float) * 1e-3            # mm -> m, true scale (no rescaling)
    return XC + c[:, 0], ZBAND_C + c[:, 1], _OD / 2

def GEOM_OD(cond):
    return {"33": 4.76e-3, "42": 3.175e-3, "66": 2.0e-3}[cond]

def grid(nx, ny, nz):
    x = np.linspace(0, W, nx); y = np.linspace(0, D, ny); z = np.linspace(0, H, nz)
    return x, y, z, (x[1] - x[0], y[1] - y[0], z[1] - z[0])

def nearest_tube_xz(cond, x, z):
    """2D distance to nearest tube wall, and interior mask, in the (x,z) plane."""
    tx, tz, r = tube_centers(cond)
    X, Z = np.meshgrid(x, z, indexing="ij")            # (nx,nz)
    d2 = np.full(X.shape, 1e9)
    for cx, cz in zip(tx, tz):
        d2 = np.minimum(d2, (X - cx) ** 2 + (Z - cz) ** 2)
    dnear = np.sqrt(d2) - r
    return dnear, (dnear < 0.0), r

def build_fields(cond, evap, x, y, z, op, bubbles=None):
    """Construct 3D temperature, vapor fraction, velocity, phase-change fields."""
    nx, ny, nz = len(x), len(y), len(z)
    X = x[:, None, None]; Y = y[None, :, None]; Z = z[None, None, :]
    Tsurf, Tsat, Tb, Tin, Tout = op["Tsurf"], op["Tsat"], op["Tbulk"], op["Tin"], op["Tout"]

    dnear2d, tube_in2d, r = nearest_tube_xz(cond, x, z)        # (nx,nz)
    dnear = dnear2d[:, None, :]; tube_in = tube_in2d[:, None, :]
    L = _L; ty0 = YC - L / 2; ty1 = YC + L / 2
    tube_y = ((Y >= ty0) & (Y <= ty1))                    # tubes span their length along y
    submerged = (Z < LEVEL)
    Tcool = Tin + (Tout - Tin) * np.clip((Y - ty0) / (ty1 - ty0), 0, 1)

    # chip footprint weighting
    chip_xy = np.exp(-(((X - XC) ** 2) / (2 * (CHIP_HX * 0.7) ** 2)
                       + ((Y - YC) ** 2) / (2 * (CHIP_HY * 0.7) ** 2)))
    chip_wide = np.exp(-(((X - XC) ** 2) / (2 * (CHIP_HX * 1.3) ** 2)
                         + ((Y - YC) ** 2) / (2 * (CHIP_HY * 1.3) ** 2)))
    tube_act = tube_in & tube_y                           # tube interior within its length

    # --- temperature ---
    T = np.where(Z > LEVEL, Tsat, Tb) * np.ones((nx, ny, nz))
    T = T + (Tsurf - Tb) * chip_xy * np.exp(-Z / 0.003)               # chip boundary layer
    T = T + 0.20 * (Tsurf - Tb) * chip_wide * np.exp(-Z / (0.40 * H)) * submerged  # warm plume
    cool_layer = np.clip(np.exp(-np.maximum(dnear, 0) / 0.0022), 0, 1) * submerged * tube_y
    T = T - (Tb - Tcool) * cool_layer                                  # tube cooling
    T = np.where(tube_act, Tcool, T)

    # --- vapor fraction (1 = vapor) ---
    vap = np.where(Z > LEVEL, 1.0, 0.0) * np.ones((nx, ny, nz))
    vap = vap + 0.6 * chip_xy * np.exp(-Z / 0.0025)                    # vapor film at chip
    rise = np.clip(Z / LEVEL, 0, 1)
    plume = 0.35 * chip_wide * (0.5 + 0.5 * rise) * submerged
    if bubbles is not None:
        blob = np.zeros((nx, ny, nz))
        for bx, by, bz, br in bubbles:
            blob += 0.9 * np.exp(-(((X - bx) ** 2 + (Y - by) ** 2 + (Z - bz) ** 2) / (2 * br ** 2)))
        plume = plume + blob
    supp = np.where(tube_y, np.clip((dnear - r) / 0.003, 0, 1), 1.0)   # condense near submerged tubes
    plume = plume * np.where(submerged, supp, 1.0)
    vap = np.clip(vap + plume, 0, 1)
    vap = np.where(tube_act, 0.0, vap)

    # --- velocity (buoyant updraft + gentle recirculation) ---
    Ub = np.sqrt(G * BETA * max(Tsurf - Tb, 1.0) * LCHIP)
    col = chip_wide * (0.3 + 0.7 * rise)
    vz = Ub * col - 0.18 * Ub * (1 - chip_wide) * submerged            # up over chip, down at sides
    vz = vz + 0.05 * (Z > LEVEL)                                       # slow drift in headspace
    vx = -0.4 * Ub * (X - XC) / (W / 2) * np.exp(-((Z - 0.40 * H) ** 2) / (2 * (0.22 * H) ** 2))
    vy = 0.05 * Ub * np.sin(2 * np.pi * (Y - YC) / D) * col
    # --- phase change (evaporation +, condensation -) ---
    evap_rate = 1.0 * chip_xy * np.exp(-Z / 0.002)
    cond_rate = 1.0 * np.clip(np.exp(-np.maximum(dnear, 0) / 0.0022), 0, 1) * submerged * tube_y * (plume > 0.05)
    pchange = evap_rate - cond_rate

    zero = np.zeros((nx, ny, nz))
    tube3d = np.broadcast_to(tube_act, (nx, ny, nz))
    vx = np.where(tube3d, 0.0, vx + zero)
    vy = np.where(tube3d, 0.0, vy + zero)
    vz = np.where(tube3d, 0.0, vz + zero)
    f = lambda a: np.ascontiguousarray((a + zero).astype(np.float32))
    return dict(temperature=f(T), vapor_fraction=f(vap),
                velocity=(f(vx), f(vy), f(vz)), phase_change=f(pchange))

# ============================ STEADY SNAPSHOTS ==============================
def write_snapshots():
    print("Steady snapshots (one per configuration):")
    for cond in ["33", "42", "66"]:
        set_geometry(cond)
        x, y, z, sp = grid(*grid_counts())
        for evap in ["plain", "micro"]:
            op = operating_point(cond, evap)
            flds = build_fields(cond, evap, x, y, z, op)
            imageToVTK(f"{OUT}/snapshot_{cond}_{evap}", origin=(0, 0, 0), spacing=sp, pointData=flds)
            print(f"  {OUT}/snapshot_{cond}_{evap}.vti   H={H*1e3:.0f}mm  "
                  f"(T_surf {op['Tsurf']:.1f}C, T_sat {op['Tsat']:.1f}C, q'' {op['q']:.0f} W/cm2)")

# ========================== TIME SERIES (one config) ========================
def write_timeseries(cond="42", evap="plain", nsteps=14):
    set_geometry(cond)
    x, y, z, sp = grid(*grid_counts())
    op = operating_point(cond, evap)
    rng = np.random.default_rng(7)
    # nucleate bubbles over the chip with staggered birth times
    nb = 30
    bx = XC + rng.uniform(-CHIP_HX, CHIP_HX, nb)
    by = YC + rng.uniform(-CHIP_HY, CHIP_HY, nb)
    tnuc = rng.uniform(0, nsteps, nb); br = rng.uniform(0.0015, 0.0030, nb)
    rise_per_step = (LEVEL - 0.002) / (nsteps * 0.75)     # cross the pool over the run
    pvd = []
    print(f"\nTime series (bubble plume, {cond}-tube {evap}):")
    for k in range(nsteps):
        bubbles = []
        for i in range(nb):
            age = k - tnuc[i]
            if age < 0:
                continue
            zb = 0.002 + rise_per_step * age              # rise from the chip
            if zb > LEVEL + 0.003:
                continue
            shrink = 1.0 if zb < ZBAND_C - 0.005 else max(0.3, 1 - (zb - (ZBAND_C - 0.005)) / 0.012)
            bubbles.append((bx[i], by[i], zb, br[i] * shrink))
        flds = build_fields(cond, evap, x, y, z, op, bubbles=bubbles)
        fn = f"ts/step_{k:04d}"
        imageToVTK(f"{OUT}/{fn}", origin=(0, 0, 0), spacing=sp, pointData=flds)
        pvd.append((float(k), fn + ".vti"))
    with open(f"{OUT}/timeseries_{cond}_{evap}.pvd", "w") as fh:
        fh.write('<?xml version="1.0"?>\n<VTKFile type="Collection" version="0.1" '
                 'byte_order="LittleEndian">\n  <Collection>\n')
        for tt, fn in pvd:
            fh.write(f'    <DataSet timestep="{tt}" file="{fn}"/>\n')
        fh.write('  </Collection>\n</VTKFile>\n')
    print(f"  {OUT}/timeseries_{cond}_{evap}.pvd   ({nsteps} steps)")

# ===================== SANITY-CHECK SLICES (matplotlib) =====================
def sanity_slices():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(3, 2, figsize=(13, 12))
    for row, cond in enumerate(["33", "42", "66"]):
        set_geometry(cond)
        x, y, z, sp = grid(*grid_counts()); jy = len(y) // 2
        op = operating_point(cond, "plain")
        flds = build_fields(cond, "plain", x, y, z, op)
        T = flds["temperature"][:, jy, :].T; V = flds["vapor_fraction"][:, jy, :].T
        ext = [0, W * 1e3, 0, H * 1e3]
        im0 = axs[row, 0].imshow(T, origin="lower", extent=ext, aspect="equal", cmap="inferno")
        axs[row, 0].axhline(LEVEL * 1e3, color="cyan", lw=1, ls="--")
        axs[row, 0].set_title(f"{cond}-tube  (H = {H*1e3:.0f} mm)  temperature [C]"); plt.colorbar(im0, ax=axs[row, 0], shrink=0.9)
        im1 = axs[row, 1].imshow(V, origin="lower", extent=ext, aspect="equal", cmap="Blues_r", vmin=0, vmax=1)
        axs[row, 1].axhline(LEVEL * 1e3, color="red", lw=1, ls="--")
        axs[row, 1].set_title(f"{cond}-tube  (H = {H*1e3:.0f} mm)  vapor fraction"); plt.colorbar(im1, ax=axs[row, 1], shrink=0.9)
        for cc in range(2):
            axs[row, cc].set_xlabel("x [mm]"); axs[row, cc].set_ylabel("z [mm]")
    fig.suptitle("Mid-plane slices, per-condenser height (33-tube 32 mm, 42-tube 42 mm), 40% liquid fill - model-driven, NOT CFD", fontsize=11)
    fig.tight_layout(); fig.savefig(f"{OUT}/_sanity_slices.png", dpi=130); plt.close(fig)
    print(f"\n  {OUT}/_sanity_slices.png  (mid-plane T and vapor for the three condensers)")

if __name__ == "__main__":
    print("=" * 70)
    print(" 3D field reconstruction for ParaView (model-driven, NOT a CFD solve)")
    print("=" * 70 + "\n")
    write_snapshots()
    write_timeseries()
    sanity_slices()
    print("\nOpen the .vti files (snapshots) and the .pvd (animation) in ParaView.")
