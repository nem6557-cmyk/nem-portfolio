"""Figures for project 4, read from results/*.npz only."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
SITE = ROOT.parent / "site" / "assets"

BG, FG, GRID = "#0e1626", "#dbe4f0", "#22304a"
TEAL, ORANGE = "#4FD1C5", "#FF8A5B"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.5,
})

t = np.load(RES / "p4_transfer.npz")
fig, ax = plt.subplots(figsize=(7.0, 4.3), dpi=150)
ax.axvspan(0.30, 0.62, color=ORANGE, alpha=0.07)
ax.plot(t["w"], t["nominal"] * 100, "o-", color=TEAL, lw=2.2, ms=6,
        label="nominal policy (project 3)")
ax.plot(t["w"], t["dr"] * 100, "s-", color=ORANGE, lw=2.2, ms=6,
        label="DR policy (trained at w = 0.30)")
ax.axvline(0.30, color=FG, lw=1, ls="--", alpha=0.5)
ax.text(0.315, 6, "DR training range ends;\nright of this line is extrapolation",
        fontsize=8.5, alpha=0.85)
ax.set_xlabel("parameter shift half-width w of the evaluation systems")
ax.set_ylabel("zero-shot success rate (%)")
ax.set_ylim(0, 100); ax.set_xlim(-0.02, 0.62)
ax.legend(framealpha=0.15, loc="upper right")
ax.set_title("Transfer under dynamics shift: 24 unseen systems x 12 targets per point")
fig.tight_layout()
for p in (RES / "p4-transfer.png", SITE / "p4-transfer.png"):
    fig.savefig(p)
plt.close(fig)

c = np.load(RES / "p4_dr_curve.npz")
p3c = np.load(ROOT.parent / "project-3-rl-reach" / "results" / "p3_shaped_curve.npz")
fig, ax = plt.subplots(figsize=(7.0, 3.9), dpi=150)
ax.plot(p3c["steps"] / 1e3, p3c["succ"] * 100, color=TEAL, lw=2.2,
        label="nominal training (fixed dynamics)")
ax.plot(c["steps"] / 1e3, c["succ"] * 100, color=ORANGE, lw=2.2,
        label="DR training (dynamics redrawn every episode)")
ax.set_xlabel("training steps (thousands)")
ax.set_ylabel("eval success on nominal dynamics (%)")
ax.set_ylim(-3, 100)
ax.legend(framealpha=0.15, loc="lower right")
ax.set_title("The robustness tax: DR learns the same task on shifting ground")
fig.tight_layout()
for p in (RES / "p4-dr-curves.png", SITE / "p4-dr-curves.png"):
    fig.savefig(p)
plt.close(fig)
print("p4 figures written")
