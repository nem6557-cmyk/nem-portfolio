"""NG-2: Sallen-Key Butterworth low-pass, nominal Bode + tolerance Monte Carlo.

Design target: 2nd-order Butterworth, fc = 1 kHz, unity gain.
Equal-component design with Q set by the amplifier gain would spoil
unity gain, so this uses the classic unity-gain topology: R1 = R2 = R,
C1 = 2C, C2 = C with Q = 1/sqrt(2) by the capacitor ratio.
R = 11.25k, C = 10 nF gives fc = 1/(2 pi R C sqrt(2)) = 1000.4 Hz.

Then the engineering question: with 5% resistors and 10% capacitors,
what fraction of built units lands within +/-10% of the design cutoff?
300 Monte Carlo netlists answer it.
"""
import subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "site" / "assets"
BG, FG, GRID = "#0e1626", "#dbe4f0", "#22304a"
TEAL, ORANGE, FAINT = "#4FD1C5", "#FF8A5B", "#7083A6"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.45,
})

R, C = 11.25e3, 10e-9

def netlist(r1, r2, c1, c2, out):
    return f"""* Sallen-Key unity-gain LPF
Vin in 0 AC 1
R1 in n1 {r1}
R2 n1 n2 {r2}
C1 n1 out {c1}
C2 n2 0 {c2}
* ideal unity-gain buffer
Eop out 0 n2 out 1e6
.ac dec 60 10 100k
.control
run
wrdata {out} vdb(out) vp(out)
.endc
.end
"""

def run(r1, r2, c1, c2, tag):
    p = HERE / f"{tag}.cir"
    o = HERE / f"{tag}.dat"
    p.write_text(netlist(r1, r2, c1, c2, o))
    subprocess.run(["ngspice", "-b", str(p)], capture_output=True, check=True)
    d = np.loadtxt(o)
    p.unlink(); o.unlink()
    return d[:, 0], d[:, 1], d[:, 3]       # f, dB, phase

f, db, ph = run(R, R, 2 * C, C, "nom")
fc_nom = float(np.interp(-3.0103, db[::-1], f[::-1]))
# slope one decade above cutoff
i1, i2 = np.searchsorted(f, [10e3, 100e3 - 1])
slope = (db[i2] - db[i1]) / np.log10(f[i2] / f[i1])

rng = np.random.default_rng(7)
N = 300
fcs = np.empty(N)
for k in range(N):
    r1, r2 = R * (1 + rng.normal(0, 0.05 / 3, 2))     # 5% ~ 3 sigma
    c1 = 2 * C * (1 + rng.normal(0, 0.10 / 3))
    c2 = C * (1 + rng.normal(0, 0.10 / 3))
    fk, dbk, _ = run(r1, r2, c1, c2, f"mc{k}")
    fcs[k] = np.interp(-3.0103, dbk[::-1], fk[::-1])
inside = np.mean(np.abs(fcs - 1000) / 1000 <= 0.10)

fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.0), dpi=150)
axes[0].semilogx(f, db, color=TEAL, lw=2.2)
axes[0].axhline(-3.0103, color=FAINT, ls=":", lw=1)
axes[0].axvline(fc_nom, color=ORANGE, ls="--", lw=1.4)
axes[0].annotate(f"fc = {fc_nom:.0f} Hz", (fc_nom, -3), xytext=(60, -12),
                 fontsize=9.5, color=ORANGE,
                 arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.1))
axes[0].text(12e3, -28, f"{slope:.1f} dB/decade", fontsize=9.5, color=TEAL)
axes[0].set_xlabel("frequency (Hz)"); axes[0].set_ylabel("|H| (dB)")
axes[0].set_title("Nominal response: textbook Butterworth")
axes[0].set_ylim(-65, 4)
axes[1].hist(fcs, bins=24, color=TEAL, edgecolor=BG)
axes[1].axvline(1000, color=FG, ls="--", lw=1.2)
axes[1].axvspan(900, 1100, color=ORANGE, alpha=0.10)
axes[1].set_xlabel("Monte Carlo cutoff (Hz)")
axes[1].set_ylabel("count of 300 builds")
axes[1].set_title(f"5% R, 10% C tolerances: {inside:.0%} inside +/-10%")
fig.tight_layout()
for p in (ASSETS / "ng2-sallenkey.png", HERE / "ng2-sallenkey.png"):
    fig.savefig(p, bbox_inches="tight")
plt.close(fig)

summary = (f"NG-2 Sallen-Key: nominal fc {fc_nom:.1f} Hz (design 1000.4), "
           f"rolloff {slope:.1f} dB/dec, MC yield inside +/-10%: {inside:.1%}, "
           f"MC fc mean {fcs.mean():.0f} Hz, sigma {fcs.std():.0f} Hz\n")
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
