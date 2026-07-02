"""Figures for project 6. The scorecard runs the real grading pipeline
(subprocess per task) and draws what it returns; nothing hand-entered."""
import json
import re
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent / "site" / "assets"
RES = ROOT / "results"
RES.mkdir(exist_ok=True)

BG, FG, GRID = "#0e1626", "#dbe4f0", "#22304a"
TEAL, ORANGE = "#4FD1C5", "#FF8A5B"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": FG, "font.size": 11,
})

# ---- run the real pipeline -------------------------------------------
tasks = sorted(p for p in (ROOT / "tasks").iterdir() if p.is_dir())
rows = []
for t in tasks:
    subprocess.run([sys.executable, "reference_solution.py"], cwd=t,
                   capture_output=True)
    r = subprocess.run([sys.executable, "checker.py"], cwd=t,
                       capture_output=True, text=True)
    fields = re.findall(r"^\s+(\w+)\s+(PASS|FAIL)", r.stdout, re.M)
    score = int(re.search(r"score: (\d+)/100", r.stdout).group(1))
    rows.append((t.name, fields, score))

# ---- scorecard ---------------------------------------------------------
titles = {"t1-aci-beam": "T1  ACI 318-19 beam flexure",
          "t2-aisc-column": "T2  AISC 360-22 column buckling",
          "t3-opensees-modal": "T3  OpenSees modal analysis"}
traps = {"t1-aci-beam": "trap: omit phi -> adequate flips to True",
         "t2-aisc-column": "trap: elastic branch misuse -> Fcr 2.1x high",
         "t3-opensees-modal": "trap: kN/m with kg -> periods 31.6x off"}
fig, ax = plt.subplots(figsize=(7.4, 4.6), dpi=150)
ax.axis("off")
y = 0.94
for name, fields, score in rows:
    ax.text(0.02, y, titles[name], fontsize=12, weight="bold", va="center")
    ax.text(0.98, y, f"{score}/100", fontsize=12, weight="bold",
            va="center", ha="right",
            color=TEAL if score == 100 else ORANGE)
    y -= 0.075
    x = 0.05
    for fname, verdict in fields:
        c = TEAL if verdict == "PASS" else ORANGE
        ax.add_patch(FancyBboxPatch((x, y - 0.030), 0.165, 0.058,
                     boxstyle="round,pad=0.008", fc=c, ec="none", alpha=0.22))
        ax.text(x + 0.0825, y, fname, ha="center", va="center",
                fontsize=9, color=c)
        x += 0.185
    y -= 0.075
    ax.text(0.05, y, traps[name], fontsize=8.8, style="italic", alpha=0.75)
    y -= 0.095
ax.text(0.02, y + 0.01,
        "every field graded by a checker on an independent solution path; "
        "tolerances 0.5-1%", fontsize=9, alpha=0.85)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_title("Task pack regression: reference solutions vs independent checkers",
             fontsize=12, pad=12)
fig.tight_layout()
for p in (RES / "p6-scorecard.png", SITE / "p6-scorecard.png"):
    fig.savefig(p)
plt.close(fig)

# ---- anatomy diagram ---------------------------------------------------
fig, ax = plt.subplots(figsize=(7.4, 3.9), dpi=150)
ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 5)

def box(x, y, w, h, text, color, fs=9.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.09",
                                fc=color, ec="none", alpha=0.20))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.09",
                                fc="none", ec=color, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=FG)

def arrow(x1, y1, x2, y2, color, label=None, dy=0.16):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->",
                 mutation_scale=13, color=color, lw=1.5))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + dy, label, fontsize=8,
                ha="center", color=color)

box(0.2, 3.3, 2.5, 1.25, "task.md\nclosed inputs,\nJSON schema, units", TEAL)
box(3.75, 3.3, 2.5, 1.25, "reference_solution.py\nengineering path\n(code eqs / OpenSees)", TEAL)
box(3.75, 0.45, 2.5, 1.25, "checker.py\nindependent path\n(first principles / numpy)", ORANGE)
box(7.3, 1.9, 2.5, 1.25, "answer.json\ngraded fields,\npartial credit", FG)
arrow(2.7, 3.92, 3.75, 3.92, TEAL)
arrow(2.7, 3.6, 3.75, 1.35, ORANGE, "same statement,\nseparate solver", dy=0.42)
arrow(6.25, 3.6, 7.55, 3.05, TEAL, "writes")
arrow(7.55, 2.2, 6.25, 1.35, ORANGE, "grades")
ax.text(5.0, 0.06, "a golden value is golden only because two solution "
        "paths that share nothing agree on it", fontsize=9,
        ha="center", style="italic", alpha=0.85)
ax.set_title("Anatomy of a machine-gradable task", fontsize=12, pad=10)
fig.tight_layout()
for p in (RES / "p6-anatomy.png", SITE / "p6-anatomy.png"):
    fig.savefig(p)
plt.close(fig)
print("p6 figures written")
