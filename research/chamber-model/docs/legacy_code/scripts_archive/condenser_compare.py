"""
Condenser geometry comparison harness
=====================================

Give it a set of condenser geometries and ONE flow rate; it runs the verified
conjugate solver (condenser_solver.py) on each and reports, side by side:

  efficiency  : effectiveness epsilon = Q / (m_dot cp (T_sat - T_in)), and NTU
  condenser-side performance:
      - per-tube and bank duty Q  [W]
      - system thermal resistance R = (T_sat - T_in)/Q_bank  [K/W]
      - mean condensation coefficient h_cond  [W/m2K]
      - condensate throughput  [g/s]
      - coolant temperature rise  [K]
      - coolant-side pressure drop and pumping power  [kPa, W]
      - internal heat-transfer area and duty-per-pumping figure of merit

Flow handling: the given flow rate is the TOTAL pump delivery, split evenly over
the n_tubes of each geometry (so geometries with more tubes run at lower per-tube
flow -> the comparison is at equal pump duty). Set FLOW_IS_TOTAL=False to instead
interpret it as per-tube.

The 4 geometries below are EXAMPLES spanning tube size / count / length / material.
Replace GEOMETRIES with your own 3-4.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import condenser_solver as cs
from condenser_solver import Geometry, Operating, Mesh

# ----------------------------------------------------------------------
# USER INPUTS  -- replace with your study
# ----------------------------------------------------------------------
FLOW_TOTAL_LMIN = 2.0          # given coolant flow rate [L/min]   <-- REPLACE
FLOW_IS_TOTAL   = True         # True: split over tubes; False: per-tube
T_IN_C          = 40.0         # coolant inlet temperature [C]      <-- REPLACE
P_KPA           = 12.0         # chamber pressure [kPa]             <-- REPLACE
T_SAT_C         = 49.4         # vapor saturation temperature [C]   <-- REPLACE
COND_MODEL      = "nusselt_tube"   # "nusselt_tube" (physical) or "constant_h"

# wall conductivities [W/mK]
K_COPPER, K_SS, K_AL = 385.0, 16.0, 237.0

GEOMETRIES = {
    "G1 baseline":      Geometry(r_i=3.0e-3, r_o=4.0e-3, L=0.150, k_wall=K_COPPER, n_tubes=10),
    "G2 compact x20":   Geometry(r_i=2.0e-3, r_o=3.0e-3, L=0.150, k_wall=K_COPPER, n_tubes=20),
    "G3 long bank":     Geometry(r_i=3.0e-3, r_o=4.0e-3, L=0.250, k_wall=K_COPPER, n_tubes=10),
    "G4 stainless":     Geometry(r_i=3.0e-3, r_o=4.5e-3, L=0.150, k_wall=K_SS,    n_tubes=10),
}

MESH = Mesh(n_rf=22, n_rw=9, n_z=200)


# ----------------------------------------------------------------------
# Coolant-side pressure drop & pumping power
# ----------------------------------------------------------------------
def pressure_drop(res, geo):
    """Fully developed single-tube pressure drop; laminar (64/Re) or Blasius turbulent."""
    D = 2 * geo.r_i
    U = res["U_mean"]; rho = res["rho"]; mu = res["mu"]; Re = res["Re"]
    if Re < 2300:
        f = 64.0 / Re
    else:
        f = 0.316 * Re ** -0.25                      # Blasius
    dp = f * (geo.L / D) * 0.5 * rho * U ** 2         # Pa, per tube
    Q_tube = res["U_mean"] * np.pi * geo.r_i ** 2     # m3/s per tube
    P_pump_total = dp * Q_tube * geo.n_tubes          # W (parallel tubes, equal flow)
    return dp, P_pump_total


# ----------------------------------------------------------------------
# Run one geometry at the given flow rate
# ----------------------------------------------------------------------
def run_one(name, geo, op_base):
    op = Operating(**op_base.__dict__)
    per_tube = (FLOW_TOTAL_LMIN / geo.n_tubes) if FLOW_IS_TOTAL else FLOW_TOTAL_LMIN
    op.Q_per_tube_Lmin = per_tube

    if COND_MODEL == "nusselt_tube":
        res = cs.solve_with_nusselt(geo, op, MESH)
    else:
        op.cond_model = "constant_h"
        res = cs.solve_field(geo, op, MESH)

    bk = cs.bank_duty(res, geo)
    dp, P_pump = pressure_drop(res, geo)

    A_int = 2 * np.pi * geo.r_i * geo.L * geo.n_tubes          # internal HT area [m2]
    h_cond = float(np.mean(res["h_ext_field"]))
    Q_bank = bk["Q_bank"]

    return dict(
        name=name,
        per_tube_Lmin=per_tube,
        Re=res["Re"],
        regime="laminar" if res["Re"] < 2300 else "turbulent",
        eps=res["eps"],
        NTU=res["NTU"],
        Q_tube=res["Q_ext"],
        Q_bank=Q_bank,
        h_cond=h_cond,
        R_sys=(op.T_sat - op.T_in) / Q_bank,
        mdot_cond_bank=bk["mdot_cond_bank"] * 1e3,            # g/s
        dT_cool=res["T_out"] - op.T_in,
        dp_kPa=dp / 1e3,
        P_pump_W=P_pump,
        A_int_cm2=A_int * 1e4,
        FOM=Q_bank / P_pump if P_pump > 0 else np.inf,        # W rejected per W pumped
    )


# ----------------------------------------------------------------------
# Comparison table
# ----------------------------------------------------------------------
def print_table(rows):
    names = [r["name"] for r in rows]
    metrics = [
        ("per-tube flow [L/min]", "per_tube_Lmin", "{:.3f}"),
        ("internal Re",            "Re",            "{:.0f}"),
        ("regime",                 "regime",        "{:s}"),
        ("effectiveness eps",      "eps",           "{:.4f}"),
        ("NTU",                    "NTU",           "{:.4f}"),
        ("duty per tube [W]",      "Q_tube",        "{:.2f}"),
        ("bank duty [W]",          "Q_bank",        "{:.1f}"),
        ("cond. HTC [W/m2K]",      "h_cond",        "{:.0f}"),
        ("system R [K/W]",         "R_sys",         "{:.4f}"),
        ("condensate [g/s]",       "mdot_cond_bank","{:.4f}"),
        ("coolant dT [K]",         "dT_cool",       "{:.3f}"),
        ("pressure drop [kPa]",    "dp_kPa",        "{:.3f}"),
        ("pump power [W]",         "P_pump_W",      "{:.4f}"),
        ("int. area [cm2]",        "A_int_cm2",     "{:.1f}"),
        ("FOM Q/Ppump [-]",        "FOM",           "{:.0f}"),
    ]
    w = 16
    hdr = f"{'metric':<24}" + "".join(f"{n[:w]:>{w}}" for n in names)
    print(hdr); print("-" * len(hdr))
    for label, key, fmt in metrics:
        cells = ""
        for r in rows:
            v = r[key]
            cells += f"{(fmt.format(v)):>{w}}"
        print(f"{label:<24}{cells}")


# ----------------------------------------------------------------------
# Comparison plots
# ----------------------------------------------------------------------
def make_plots(rows, path="/home/claude"):
    names = [r["name"] for r in rows]
    x = np.arange(len(names))
    colors = plt.cm.viridis(np.linspace(0.15, 0.85, len(names)))

    # panel of bars
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    def bars(a, key, title, ylab, scale=1.0):
        vals = [r[key] * scale for r in rows]
        a.bar(x, vals, color=colors)
        a.set_xticks(x); a.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
        a.set_title(title, fontsize=11); a.set_ylabel(ylab, fontsize=9)
        for xi, v in zip(x, vals):
            a.text(xi, v, f"{v:.3g}", ha="center", va="bottom", fontsize=8)
    bars(ax[0, 0], "eps",      "Effectiveness (efficiency)", "epsilon")
    bars(ax[0, 1], "Q_bank",   "Bank duty",                  "Q [W]")
    bars(ax[1, 0], "R_sys",    "System thermal resistance",  "R [K/W]")
    bars(ax[1, 1], "P_pump_W", "Coolant pumping power",      "P_pump [W]")
    fig.suptitle(f"Condenser comparison at {FLOW_TOTAL_LMIN} L/min total, "
                 f"T_in={T_IN_C} C, P={P_KPA} kPa", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(f"{path}/cmp_bars.png", dpi=140); plt.close(fig)

    # Pareto: duty vs pumping power
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for r, c in zip(rows, colors):
        ax.scatter(r["P_pump_W"], r["Q_bank"], s=140, color=c, zorder=3)
        ax.annotate(r["name"], (r["P_pump_W"], r["Q_bank"]),
                    textcoords="offset points", xytext=(8, 4), fontsize=9)
    ax.set_xlabel("coolant pumping power  [W]  (lower is better)")
    ax.set_ylabel("bank duty  [W]  (higher is better)")
    ax.set_title("Performance vs pumping cost  (upper-left is best)")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(f"{path}/cmp_pareto.png", dpi=140); plt.close(fig)

    return [f"{path}/cmp_bars.png", f"{path}/cmp_pareto.png"]


# ----------------------------------------------------------------------
if __name__ == "__main__":
    op_base = Operating(T_in=T_IN_C + 273.15, P_kPa=P_KPA, T_sat=T_SAT_C + 273.15,
                        cond_model=COND_MODEL)

    print("=" * 92)
    print(f"CONDENSER GEOMETRY COMPARISON   |   total flow {FLOW_TOTAL_LMIN} L/min "
          f"({'split over tubes' if FLOW_IS_TOTAL else 'per tube'})   |   "
          f"T_in {T_IN_C} C, P {P_KPA} kPa, T_sat {T_SAT_C} C   |   model: {COND_MODEL}")
    print("=" * 92)

    rows = [run_one(name, geo, op_base) for name, geo in GEOMETRIES.items()]
    print_table(rows)

    # quick verdicts
    best_duty = max(rows, key=lambda r: r["Q_bank"])
    best_R    = min(rows, key=lambda r: r["R_sys"])
    best_fom  = max(rows, key=lambda r: r["FOM"])
    print("\nverdicts:")
    print(f"  highest bank duty     : {best_duty['name']}  ({best_duty['Q_bank']:.1f} W)")
    print(f"  lowest system R       : {best_R['name']}  ({best_R['R_sys']:.4f} K/W)")
    print(f"  best duty/pump (FOM)  : {best_fom['name']}  ({best_fom['FOM']:.0f})")

    figs = make_plots(rows)
    print("\nfigures:", *figs, sep="\n  ")
    print("\nNote: internal field model is laminar; any geometry showing 'turbulent' "
          "needs a turbulent internal closure before its number is trusted.")
