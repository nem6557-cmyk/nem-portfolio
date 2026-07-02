"""Figures for project 5. Reads results/p5_curves.npz only; every number
on the site comes from the same arrays the summary was written from."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
SITE = ROOT.parent / "site" / "assets"
d = np.load(RES / "p5_curves.npz")

BG, FG, GRID = "#0e1626", "#dbe4f0", "#22304a"
TEAL, ORANGE = "#4FD1C5", "#FF8A5B"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.5,
})

# ---- capacity curves --------------------------------------------------
fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=150)
ax.plot(d["b_drift"] * 100, d["b_vw"], color=TEAL, lw=2.2,
        label=f"bare frame  (T1 = {float(d['b_T1']):.2f} s)")
ax.plot(d["r_drift"] * 100, d["r_vw"], color=ORANGE, lw=2.2,
        label=f"X-braced retrofit  (T1 = {float(d['r_T1']):.2f} s)")
ax.axhline(0.25, color=FG, lw=1.0, ls="--", alpha=0.55)
ax.text(3.15, 0.27, "comparison demand V/W = 0.25", fontsize=9, alpha=0.8)
ax.set_xlabel("roof drift  (% of building height)")
ax.set_ylabel("base shear / seismic weight  V/W")
ax.set_xlim(0, 4.1); ax.set_ylim(0, 1.32)
ax.legend(loc="center right", framealpha=0.15)
ax.set_title("Pushover capacity: bare moment frame vs braced retrofit")
fig.tight_layout()
for p in (RES / "p5-capacity.png", SITE / "p5-capacity.png"):
    fig.savefig(p)
plt.close(fig)

# ---- story drift profiles at equal demand -----------------------------
def profile(drift, vw, story):
    i = int(np.argmax(vw >= 0.25))
    return story[i] * 100          # % story drift, stories 1..3

bp, rp = profile(d["b_drift"], d["b_vw"], d["b_story"]), \
         profile(d["r_drift"], d["r_vw"], d["r_story"])
floors = np.array([1, 2, 3])
fig, ax = plt.subplots(figsize=(4.6, 4.4), dpi=150)
ax.plot(bp, floors, "o-", color=TEAL, lw=2.2, ms=6, label="bare frame")
ax.plot(rp, floors, "s-", color=ORANGE, lw=2.2, ms=6, label="braced retrofit")
ax.set_yticks(floors); ax.set_yticklabels(["story 1", "story 2", "story 3"])
ax.set_xlabel("peak story drift at V/W = 0.25  (%)")
ax.set_xlim(0, max(bp) * 1.18)
ax.legend(framealpha=0.15)
ax.set_title("Same demand, where the drift goes")
fig.tight_layout()
for p in (RES / "p5-drift.png", SITE / "p5-drift.png"):
    fig.savefig(p)
plt.close(fig)

# ---- frame schematic --------------------------------------------------
fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=150)
ax.grid(False)
L, H = 6.0, 3.5
for x0, braced, tag in ((0.0, False, "bare MRF"), (10.0, True, "X-braced retrofit")):
    for lvl in range(3):
        y = lvl * H
        ax.plot([x0, x0], [y, y + H], color=TEAL, lw=3)
        ax.plot([x0 + L, x0 + L], [y, y + H], color=TEAL, lw=3)
        ax.plot([x0, x0 + L], [y + H, y + H], color=TEAL, lw=2.2)
        if braced:
            ax.plot([x0, x0 + L], [y, y + H], color=ORANGE, lw=1.6)
            ax.plot([x0 + L, x0], [y, y + H], color=ORANGE, lw=1.6)
        ax.annotate("", xy=(x0 - 0.9, y + H), xytext=(x0 - 2.0, y + H),
                    arrowprops=dict(arrowstyle="->", color=FG, lw=1.2))
    ax.plot([x0 - 0.6, x0 + L + 0.6], [0, 0], color=FG, lw=2)
    for xh in np.arange(x0 - 0.6, x0 + L + 0.6, 0.55):
        ax.plot([xh, xh - 0.3], [0, -0.45], color=FG, lw=0.9)
    ax.text(x0 + L / 2, -1.5, tag, ha="center", fontsize=11)
ax.text(-2.15, 2 * H + H / 2 + 0.9, "lateral load\npattern", fontsize=8.5,
        ha="left", alpha=0.85)
ax.set_xlim(-2.6, 17.2); ax.set_ylim(-2.2, 11.4)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("3-story, 1-bay steel frame: two lateral systems, one model change")
fig.tight_layout()
for p in (RES / "p5-frame.png", SITE / "p5-frame.png"):
    fig.savefig(p)
plt.close(fig)
print("p5 figures written")
