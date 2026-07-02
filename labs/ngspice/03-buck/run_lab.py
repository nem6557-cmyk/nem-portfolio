"""NG-3: 12 V to 5 V synchronous-style buck converter transient.

100 kHz switching, L = 100 uH, C = 100 uF with 30 mOhm ESR,
2.5 ohm load. The first version of this lab measured 110 mV of
"ripple" and disagreed with the small-ripple analysis by 30x; the
waveform showed why: the output LC is underdamped (zeta = 0.2,
fn = 1.6 kHz) and its startup transient takes ~12 ms to die, far
longer than the 3 ms window. The lab now runs 25 ms, measures over
the final periods, and checks ripple against the two-term prediction
dV = dI_L * ESR + dI_L / (8 f C), with dI_L computed from the actual
output voltage and diode drop.
"""
import subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "site" / "assets"
BG, FG, GRID = "#ffffff", "#17212F", "#D9E2EC"
TEAL, ORANGE, FAINT = "#0F766E", "#C2410C", "#8593A8"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.45,
})

VIN, VOUT, F, L, C, RL = 12.0, 5.0, 100e3, 100e-6, 100e-6, 2.5
D = VOUT / VIN
net = HERE / "buck.cir"
net.write_text(f"""* async buck 12V -> 5V, {F/1e3:.0f} kHz
Vin  vin 0 DC {VIN}
S1   vin sw ctrl 0 SWMOD
D1   0 sw DPWR
L1   sw out {L}
C1   out cesr {C} ic=0
Resr cesr 0 0.03
Rload out 0 {RL}
Vctl ctrl 0 PULSE(0 5 0 10n 10n {D/F:.6e} {1/F:.6e})
.model SWMOD SW(Ron=0.02 Roff=1e6 Vt=2.5 Vh=0.2)
.model DPWR D(Is=1e-9 Rs=0.01 N=1.05)
.tran 100n 25m 0 200n uic
.control
run
wrdata {HERE}/buck.dat v(out) i(L1)
.endc
.end
""")
subprocess.run(["ngspice", "-b", str(net)], capture_output=True, check=True)
d = np.loadtxt(HERE / "buck.dat")
t, vout, il = d[:, 0], d[:, 1], d[:, 3]
ss = t > 24.90e-3
v_mean = vout[ss].mean()
ripple = vout[ss].max() - vout[ss].min()
il_ripple = il[ss].max() - il[ss].min()
VF = 0.68                                  # diode drop at this current
d_eff = (v_mean + VF) / (VIN + VF)         # volt-second balance w/ diode
il_pred = (VIN - v_mean) * d_eff / (L * F)
ripple_pred = il_pred * 0.03 + il_pred / (8 * F * C)

fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.0), dpi=150)
sub = t < 15e-3
axes[0].plot(t[sub] * 1e3, vout[sub], color=TEAL, lw=1.2)
axes[0].axhline(VOUT, color=FAINT, ls=":", lw=1)
axes[0].set_xlabel("time (ms)"); axes[0].set_ylabel("V_out (V)")
axes[0].set_title(f"Underdamped startup (zeta 0.2) rings for ~12 ms; "
                  f"settled mean {v_mean:.3f} V")
z = (t > 24.97e-3)
axes[1].plot((t[z] - 24.97e-3) * 1e6, vout[z], color=TEAL, lw=1.8)
axes[1].set_xlabel("time (us)"); axes[1].set_ylabel("V_out (V)")
axes[1].set_title(f"Ripple {ripple*1e3:.1f} mVpp "
                  f"(small-ripple analysis: {ripple_pred*1e3:.1f} mVpp)")
fig.tight_layout()
for p in (ASSETS / "ng3-buck.png", HERE / "ng3-buck.png"):
    fig.savefig(p, bbox_inches="tight")
plt.close(fig)

summary = (f"NG-3 buck: settled mean Vout {v_mean:.3f} V (async diode drop "
           f"accounts for the offset from {VOUT} V), output ripple "
           f"{ripple*1e3:.2f} mVpp vs two-term prediction "
           f"{ripple_pred*1e3:.2f} mVpp, inductor ripple {il_ripple:.3f} A "
           f"vs {il_pred:.3f} A predicted. First-cut lesson kept in the "
           f"docstring: a 3 ms window measured the startup transient, not "
           f"the ripple.\n")
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
