"""Bespoke figures for the research and software pages.

Every number in the CHF and coolant charts comes from Table 7 and
Sec. 3.3 of Mustafa & Kandlikar, ASME J. Heat Mass Transfer (in press,
DOI 10.1115/1.4072138). The ABB image is the author's OpenSCAD render
with the default cream background keyed to the site navy.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image
from pathlib import Path

A = Path(__file__).resolve().parent.parent / "site" / "assets"
BG, FG, GRID = "#ffffff", "#17212F", "#D9E2EC"
TEAL, ORANGE, FAINT = "#0F766E", "#C2410C", "#8593A8"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.45,
})

# ---- CHF summary across configurations (Table 7) -----------------------
widths = ["381", "500", "762", "1000"]
water_nt = [185.31, 108.19, 177.65, 167.03]
water_t  = [125.47,  77.26, 138.75, 131.85]
novec_nt = [ 36.7,   29.6,   37.2,   35.7 ]
novec_t  = [ 51.0,   41.1,   51.4,   42.2 ]

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), dpi=150, sharey=False)
x = np.arange(4); w = 0.38
for ax, nt, t, name, peak in (
    (axes[0], water_nt, water_t, "Water, 12 kPa", "185.3"),
    (axes[1], novec_nt, novec_t, "Novec 7000, 1 atm", "51.4"),
):
    ax.bar(x - w/2, nt, w, color=TEAL, label="no taper")
    ax.bar(x + w/2, t,  w, color=ORANGE, label="with taper")
    ax.set_xticks(x); ax.set_xticklabels([f"{s}" for s in widths])
    ax.set_xlabel("microchannel width (um)")
    ax.set_title(name, fontsize=11)
axes[0].set_ylabel("critical heat flux (W/cm$^2$)")
axes[0].legend(framealpha=0.15)
axes[0].annotate("185.3", (0 - w/2, 185.31), ha="center", va="bottom",
                 fontsize=9, color=TEAL, xytext=(0, 3),
                 textcoords="offset points")
axes[1].annotate("51.4", (2 + w/2, 51.4), ha="center", va="bottom",
                 fontsize=9, color=ORANGE, xytext=(0, 3),
                 textcoords="offset points")
fig.suptitle("CHF on 11.04 cm$^2$ substrates, 20 $^\\circ$C coolant: "
             "the taper helps the dielectric and hurts water", y=1.02)
fig.tight_layout()
fig.savefig(A / "r-chf-summary.png", bbox_inches="tight")
plt.close(fig)

# ---- coolant-temperature study (Sec. 3.3 / Table 7) ---------------------
fig, ax = plt.subplots(figsize=(6.8, 4.0), dpi=150)
tw = [20, 40, 45, 50]; chf_w = [125.47, 147.63, 195.32, 136.83]
tn = [20, 40];         chf_n = [51.4, 66.0]
ax.plot(tw, chf_w, "o-", color=TEAL, lw=2.2, ms=7,
        label="water, 381 um taper (12 kPa)")
ax.plot(tn, chf_n, "s-", color=ORANGE, lw=2.2, ms=7,
        label="Novec 7000, 762 um taper (1 atm)")
ax.annotate("195.3 W/cm$^2$ at 45 $^\\circ$C", (45, 195.32),
            xytext=(28.5, 199), fontsize=9.5, color=TEAL,
            arrowprops=dict(arrowstyle="->", color=TEAL, lw=1.2))
ax.annotate("condenser\nsaturates", (50, 136.83), xytext=(51.2, 155),
            fontsize=8.5, color=FAINT, ha="left",
            arrowprops=dict(arrowstyle="->", color=FAINT, lw=1))
ax.annotate("66: highest reported\nfor HFE-7000 above 1 cm$^2$", (40, 66),
            xytext=(30.5, 88), fontsize=8.5, color=ORANGE,
            arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1))
ax.set_xlabel("coolant inlet temperature ($^\\circ$C)")
ax.set_ylabel("critical heat flux (W/cm$^2$)")
ax.set_xlim(17, 58); ax.set_ylim(30, 215)
ax.legend(framealpha=0.15, loc="lower right", fontsize=9)
ax.set_title("Warmer coolant raises CHF until the condenser saturates")
fig.tight_layout()
fig.savefig(A / "r-coolant-study.png", bbox_inches="tight")
plt.close(fig)

# ---- LittleJourney architecture ----------------------------------------
fig, ax = plt.subplots(figsize=(9.8, 4.4), dpi=150)
ax.axis("off"); ax.set_xlim(0, 14); ax.set_ylim(0, 7); ax.grid(False)

def box(x, y, w, h, text, color, fs=9.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                                fc=color, ec="none", alpha=0.18))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                                fc="none", ec=color, lw=1.4))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            fontsize=fs, color=FG, linespacing=1.5)

def arrow(x1, y1, x2, y2, color, label=None, dy=0.18):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="<->",
                 mutation_scale=12, color=color, lw=1.4))
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + dy, label, fontsize=8,
                ha="center", color=color)

box(0.3, 2.4, 3.4, 2.2, "React Native app\nExpo 54 / React 19 / TS 5.9\n24 screens, 3 roles\nReact Query + Context", TEAL, 9)
box(5.3, 2.4, 3.6, 2.2, "Supabase\nPostgres + RLS\nAuth / Realtime / Storage\n9 migrations", FG, 9)
box(10.6, 4.4, 3.1, 1.9, "Edge Functions (10)\ncheckout / invoices /\nwebhooks / push /\ndata export + deletion", ORANGE, 8.4)
box(10.6, 0.6, 3.1, 1.6, "Stripe &middot; Expo Push\nSentry".replace("&middot;", "\u00b7"), FAINT, 9)
arrow(3.7, 3.5, 5.3, 3.5, TEAL, "realtime + REST")
arrow(8.9, 4.1, 10.6, 5.0, ORANGE, "authz-checked calls")
arrow(12.15, 4.4, 12.15, 2.2, FAINT)
ax.text(7, 0.25, "row-level security on every table; edge functions "
        "re-verify role claims server-side before Stripe and data-privacy "
        "operations", fontsize=8.6, ha="center", style="italic", alpha=0.85)
ax.set_title("LittleJourney: three-role daycare platform, "
             "19.5k lines TS/SQL, 100 unit tests", fontsize=11.5, pad=10)
fig.tight_layout()
fig.savefig(A / "sw-lj-architecture.png", bbox_inches="tight")
plt.close(fig)

# ---- ABB IRB760 OpenSCAD render: key cream background to navy ----------
im = np.asarray(Image.open("/mnt/user-data/uploads/ABB_IRB760_Assembly_Isometric.png").convert("RGB"), dtype=float)
cream = np.array([255.0, 255.0, 229.0])
d = np.sqrt(((im - cream) ** 2).sum(-1))
t0, t1 = 18.0, 60.0                       # feathered key
alpha = np.clip((d - t0) / (t1 - t0), 0, 1)[..., None]
navy = np.array([14.0, 22.0, 38.0])
out = im * alpha + navy * (1 - alpha)
Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(A / "sw-abb-openscad.png")
print("expansion figures written:",
      [p.name for p in sorted(A.glob('r-ch*.png'))] +
      ["r-coolant-study.png", "sw-lj-architecture.png", "sw-abb-openscad.png"])
