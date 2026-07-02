"""NG-1: the motor thermal network as a SPICE circuit.

The electro-thermal analogy maps temperature to voltage, heat flow to
current, thermal resistance to resistance, and heat capacity to
capacitance. Project 2's two-node motor network (winding + case)
becomes a two-RC circuit, and ngspice becomes the thermal solver.

Two cross-checks anchor it:
 1. transient: ngspice vs the project's own RK4 integrator on an
    open-loop 4 N m hold (same ODEs, so agreement is the test of both)
 2. steady state: a SPICE DC sweep of dissipated power recovers the
    continuous torque rating, compared against the closed form 2.77 N m
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "project-2-thermal-actuator" / "src"))
from thermal_actuator import ThermalActuator, ThermalActuatorParams

P = ThermalActuatorParams()
TAU = 4.0
POWER = P.c_loss * TAU**2          # 54.4 W at 4 N m

BG, FG, GRID = "#0e1626", "#dbe4f0", "#22304a"
TEAL, ORANGE, FAINT = "#4FD1C5", "#FF8A5B", "#7083A6"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.45,
})
ASSETS = REPO / "site" / "assets"

# ---- transient netlist (voltages = temperature rise above ambient) -----
net = HERE / "thermal_transient.cir"
net.write_text(f"""* Two-node motor thermal network, electro-thermal analogy
* node tw = winding rise (K), node tc = case rise (K), gnd = ambient
Ipow 0 tw DC {POWER}
Cw   tw 0  {P.Cw}
Rwc  tw tc {P.R_wc}
Cc   tc 0  {P.Cc}
Rca  tc 0  {P.R_ca}
.tran 0.1 300 uic
.control
run
wrdata {HERE}/transient.dat v(tw) v(tc)
.endc
.end
""")
subprocess.run(["ngspice", "-b", str(net)], capture_output=True, check=True)
d = np.loadtxt(HERE / "transient.dat")
t_sp, tw_sp, tc_sp = d[:, 0], d[:, 1] + P.T_ambient, d[:, 3] + P.T_ambient

# ---- reference: the project's own RK4 model, open loop ------------------
act = ThermalActuator(P)
dt = 0.05
t_py = np.arange(0, 300 + dt, dt)
tw_py, tc_py = np.empty_like(t_py), np.empty_like(t_py)
for i, _ in enumerate(t_py):
    tw_py[i], tc_py[i] = act.Tw, act.Tc
    act.step(TAU, dt)

tw_i = np.interp(t_py, t_sp, tw_sp)
tc_i = np.interp(t_py, t_sp, tc_sp)
err_w = np.abs(tw_i - tw_py).max()
err_c = np.abs(tc_i - tc_py).max()

fig, ax = plt.subplots(figsize=(7.4, 4.2), dpi=150)
ax.plot(t_py, tw_py, color=TEAL, lw=2.4, label="winding, Python RK4 (project 2)")
ax.plot(t_sp, tw_sp, "--", color=FG, lw=1.4, label="winding, ngspice")
ax.plot(t_py, tc_py, color=ORANGE, lw=2.4, label="case, Python RK4")
ax.plot(t_sp, tc_sp, "--", color=FAINT, lw=1.4, label="case, ngspice")
ax.axhline(P.T_derate, color=FAINT, ls=":", lw=1)
ax.text(210, P.T_derate + 1.2, "derate threshold 90 C", fontsize=8.5, color=FAINT)
ax.set_xlabel("time (s)"); ax.set_ylabel("temperature (degC)")
ax.set_title(f"Same network, two solvers: max deviation "
             f"{max(err_w, err_c)*1000:.1f} mK over 300 s")
ax.legend(framealpha=0.15, fontsize=9)
fig.tight_layout()
fig.savefig(ASSETS / "ng1-transient.png", bbox_inches="tight")
fig.savefig(HERE / "ng1-transient.png", bbox_inches="tight")
plt.close(fig)

# ---- steady state: DC sweep of power -> continuous rating ---------------
net2 = HERE / "thermal_dc.cir"
net2.write_text(f"""* steady-state winding rise vs dissipated power
Ipow 0 tw DC 1
Rwc  tw tc {P.R_wc}
Rca  tc 0  {P.R_ca}
.dc Ipow 1 130 0.25
.control
run
wrdata {HERE}/dc.dat v(tw)
.endc
.end
""")
subprocess.run(["ngspice", "-b", str(net2)], capture_output=True, check=True)
d2 = np.loadtxt(HERE / "dc.dat")
p_sw, tw_ss = d2[:, 0], d2[:, 1] + P.T_ambient
tau_sw = np.sqrt(p_sw / P.c_loss)
tau_cont_spice = float(np.interp(P.T_derate, tw_ss, tau_sw))
tau_cont_closed = np.sqrt((P.T_derate - P.T_ambient)
                          / (P.c_loss * (P.R_wc + P.R_ca)))

fig, ax = plt.subplots(figsize=(6.6, 4.2), dpi=150)
ax.plot(tau_sw, tw_ss, color=TEAL, lw=2.4)
ax.axhline(P.T_derate, color=FAINT, ls=":", lw=1.2)
ax.axvline(tau_cont_spice, color=ORANGE, ls="--", lw=1.6)
ax.annotate(f"continuous rating\nSPICE sweep: {tau_cont_spice:.3f} N m\n"
            f"closed form: {tau_cont_closed:.3f} N m",
            (tau_cont_spice, 47), xytext=(1.15, 62), fontsize=9.5,
            color=ORANGE,
            arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.2))
ax.set_xlabel("sustained torque (N m)")
ax.set_ylabel("steady-state winding temperature (degC)")
ax.set_title("DC sweep recovers the project 2 rating")
ax.set_xlim(0.9, 6.1)
fig.tight_layout()
fig.savefig(ASSETS / "ng1-rating.png", bbox_inches="tight")
fig.savefig(HERE / "ng1-rating.png", bbox_inches="tight")
plt.close(fig)

summary = f"""NG-1 electro-thermal analogy: results
transient max |SPICE - RK4|: winding {err_w*1000:.2f} mK, case {err_c*1000:.2f} mK
continuous rating from SPICE DC sweep: {tau_cont_spice:.3f} N m
continuous rating, closed form:        {tau_cont_closed:.3f} N m
agreement: {abs(tau_cont_spice-tau_cont_closed)/tau_cont_closed*100:.3f}%
"""
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
