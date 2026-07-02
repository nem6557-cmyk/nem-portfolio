"""AE-2: where to put the tolerance, measured instead of guessed.

A numeric tolerance is a classifier threshold: too tight and honest
solutions fail on numerical noise, too loose and wrong methods pass.
This lab sweeps the tolerance for T1's governing field (phi*Mn) against
two populations: legitimate solutions with realistic numerical scatter,
and wrong-method solutions built from the checker's documented traps
(phi omitted entirely: +11.1%; wrong phi regime 0.65: -27.8%) plus
smaller illustrative method slips at +3% and -2%. The curves locate
the operating band; the pack's chosen 1% sits inside it.
"""
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

GOLD = 443.524
rng = np.random.default_rng(11)
legit = GOLD * (1 + rng.normal(0, 0.003, 4000))          # 0.3% scatter
wrong_rel = np.array([+0.1111, -0.278, +0.03, -0.02])
wrong = GOLD * (1 + wrong_rel)

taus = np.logspace(np.log10(0.0005), np.log10(0.15), 200)
fn = [(np.abs(legit / GOLD - 1) > t).mean() for t in taus]
fp = [(np.abs(wrong / GOLD - 1) <= t).mean() for t in taus]

fig, ax = plt.subplots(figsize=(7.6, 4.4), dpi=150)
ax.semilogx(taus * 100, np.array(fn) * 100, color=TEAL, lw=2.4,
            label="false fail: legit solutions rejected")
ax.semilogx(taus * 100, np.array(fp) * 100, color=ORANGE, lw=2.4,
            label="false pass: wrong methods accepted")
ax.axvline(1.0, color=FG, ls="--", lw=1.4)
ax.annotate("pack's choice: 1%", (1.0, 62), xytext=(1.6, 74),
            fontsize=10, color=FG,
            arrowprops=dict(arrowstyle="->", color=FG, lw=1.1))
i = np.searchsorted(taus, 0.01)
ax.set_xlabel("relative tolerance (%)")
ax.set_ylabel("error rate (%)")
ax.set_title(f"At 1%: false-fail {fn[i]*100:.2f}%, "
             f"false-pass {fp[i]*100:.0f}% of wrong methods")
ax.legend(framealpha=0.15, fontsize=9.5)
fig.tight_layout()
for p in (ASSETS / "ae2-tolerance.png", HERE / "ae2-tolerance.png"):
    fig.savefig(p, bbox_inches="tight")

first_fp = taus[np.argmax(np.array(fp) > 0)]
summary = (f"AE-2 tolerance sweep on T1 phiMn: at the pack's 1% tolerance, "
           f"false-fail {fn[i]*100:.2f}% (of 4000 legit draws at 0.3% "
           f"scatter), false-pass 0% of the four wrong-method values; "
           f"the smallest wrong-method slip (magnitude 2%) first passes at "
           f"tolerance {first_fp*100:.1f}%. Operating band roughly 0.5% to "
           f"2%: below it noise fails honest work, above it minor method "
           f"slips start passing. Populations are synthetic and labeled.\n")
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
