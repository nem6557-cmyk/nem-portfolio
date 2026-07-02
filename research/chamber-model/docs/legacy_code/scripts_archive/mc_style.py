"""Shared professional figure style + palette for the microchannel deliverables."""
import matplotlib as mpl
import matplotlib.pyplot as plt

# ---- palette ----
C33   = "#1A5276"   # 33-tube primary (deep blue)
C33L  = "#AED6F1"   # 33-tube light
C42   = "#A93226"   # 42-tube primary (deep red)
C42L  = "#F5B7B1"   # 42-tube light
INK   = "#212F3D"   # text / spines
MUTE  = "#7F8C8D"   # muted gray
GRID  = "#E6E8EB"
ACC   = "#CA6F1E"   # orange accent (predictions / highlights)
GOOD  = "#1E8449"   # green (calibrated / confirmed)
PANEL = "#FBFCFD"   # near-white panel

COOL = {  # color by coolant inlet temperature
    "20C": "#1A5276", "30C": "#2E86C1", "40C": "#CA6F1E", "50C": "#A93226",
    "20": "#1A5276", "30": "#2E86C1", "40": "#CA6F1E", "50": "#A93226",
}

def apply():
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
        "font.size": 11, "text.color": INK,
        "axes.titlesize": 12.5, "axes.titleweight": "bold", "axes.titlecolor": INK,
        "axes.titlepad": 10,
        "axes.labelsize": 11, "axes.labelcolor": INK, "axes.labelpad": 6,
        "axes.edgecolor": "#AEB6BF", "axes.linewidth": 1.1,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.facecolor": "white", "axes.axisbelow": True,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.9,
        "xtick.color": INK, "ytick.color": INK,
        "xtick.labelsize": 10, "ytick.labelsize": 10,
        "xtick.major.size": 4, "ytick.major.size": 4,
        "xtick.major.width": 1.0, "ytick.major.width": 1.0,
        "legend.fontsize": 9.5, "legend.frameon": True, "legend.framealpha": 0.96,
        "legend.edgecolor": "#D5DBDB", "legend.borderpad": 0.7, "legend.labelspacing": 0.5,
        "figure.facecolor": "white", "figure.dpi": 150, "savefig.dpi": 160,
        "savefig.bbox": "tight", "savefig.facecolor": "white",
        "lines.linewidth": 2.4, "lines.markeredgewidth": 0.8,
    })

def title_block(fig, title, subtitle=None, x=0.012, y=0.985):
    fig.text(x, y, title, ha="left", va="top", fontsize=15, fontweight="bold", color=INK)
    if subtitle:
        fig.text(x, y-0.052, subtitle, ha="left", va="top", fontsize=10.5, color=MUTE)

def footnote(fig, text, x=0.012, y=0.012):
    fig.text(x, y, text, ha="left", va="bottom", fontsize=8.3, color=MUTE, style="italic")

def style_ax(ax):
    ax.tick_params(length=4, width=1.0)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#AEB6BF")
    return ax
