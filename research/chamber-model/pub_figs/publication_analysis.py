#!/usr/bin/env python3
"""
Publication-quality boiling curves and numerical error analysis for the
validated gray-box thermal model of the subcooled pool-boiling chamber.

The model (chamber_model.py) is calibrated to the measured data; this script
quantifies its predictive accuracy and renders the figures for the manuscript:
    fig_boiling_curves   model vs experiment, q'' vs chip surface temperature
    fig_parity           predicted vs measured chip surface temperature
    fig_residuals        residual structure and distribution
plus a LaTeX results table and a per-point CSV.

All predictions use the FULL predictive chain chip_temp_from_geometry():
geometry + coolant inlet + heat flux -> chip surface temperature, with the
fitted, geometry-independent boiling coefficients. No per-point tuning.
"""
import os, csv, importlib.util
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ----------------------------------------------------------------------------
# load the validated model as a module
spec = importlib.util.spec_from_file_location("cm", "/home/claude/chamber_model.py")
cm = importlib.util.module_from_spec(spec); spec.loader.exec_module(cm)

OUT = "/home/claude/pub_analysis/figs"; os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------------
# publication style: STIX (Times-like) text + matched math, vector output
mpl.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix",
    "font.size": 9.5, "axes.labelsize": 10.5, "axes.titlesize": 10.5,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5, "legend.fontsize": 8,
    "axes.linewidth": 0.8, "lines.linewidth": 1.5, "lines.markersize": 4.2,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.minor.visible": True, "ytick.minor.visible": True,
    "xtick.top": True, "ytick.right": True,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.5,
    "savefig.dpi": 300, "savefig.bbox": "tight", "figure.dpi": 150,
})

CT = {"20": "#1f4e79", "30": "#2e7d32", "40": "#e07b00", "50": "#c0392b"}  # coolant inlet colour
CONFIGS = [("33", "plain"), ("33", "micro"), ("42", "plain"), ("42", "micro")]
LABELS = {("33", "plain"): "33-tube, plain copper", ("33", "micro"): "33-tube, microchannel",
          ("42", "plain"): "42-tube, plain copper", ("42", "micro"): "42-tube, microchannel"}
CHF = {("33", "plain"): 114.0, ("33", "micro"): 174.0, ("42", "plain"): 65.0, ("42", "micro"): 125.0}
MARK = {("33", "plain"): "o", ("33", "micro"): "s", ("42", "plain"): "^", ("42", "micro"): "D"}


def predict(p):
    return cm.chip_temp_from_geometry(p["q"], p["Tin"], f'{p["gk"]}-tube',
                                      cm.NC_FACTOR[p["gk"]], p["chip"])


# ============================================================================
# FIGURE 1 -- boiling curves, model vs experiment (2x2, one panel per config)
# ============================================================================
def fig_boiling():
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.4))
    for ax, cfg in zip(axes.ravel(), CONFIGS):
        gk, chip = cfg
        pts = cm.points(gk, chip)
        for t in ["20", "30", "40", "50"]:
            sub = sorted([p for p in pts if p["t"] == t], key=lambda r: r["Tsurf"])
            if not sub:
                continue
            Tm = [p["Tsurf"] for p in sub]; qm = [p["q"] for p in sub]
            ax.plot(Tm, qm, MARK[cfg], color=CT[t], mfc="white", mew=1.1, zorder=3)
            # model curve over the measured flux range
            qg = np.linspace(min(qm), max(qm), 60)
            Tp = [cm.chip_temp_from_geometry(q, float(t), f"{gk}-tube",
                                             cm.NC_FACTOR[gk], chip) for q in qg]
            ax.plot(Tp, qg, "-", color=CT[t], lw=1.6, zorder=2)
        ax.set_title(LABELS[cfg], pad=4)
        ax.set_xlabel(r"chip surface temperature $T_{\mathrm{surf}}\;[^{\circ}\mathrm{C}]$")
        ax.set_ylabel(r"heat flux $q''\;[\mathrm{W\,cm^{-2}}]$")
        # per-panel RMSE
        pr = [predict(p) for p in pts]; me = [p["Tsurf"] for p in pts]
        ax.text(0.04, 0.95, rf"$\mathrm{{RMSE}}={cm.rmse(pr, me):.2f}\ \mathrm{{K}}$"
                            f"\n$n={len(pts)}$",
                transform=ax.transAxes, va="top", ha="left", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", lw=0.6, alpha=0.9))
        ax.margins(x=0.04)
    # shared legend: coolant inlets + experiment/model proxies
    hc = [Line2D([], [], color=CT[t], lw=1.6, label=rf"$T_{{\mathrm{{in}}}}={t}\,^{{\circ}}\mathrm{{C}}$")
          for t in ["20", "30", "40", "50"]]
    hp = [Line2D([], [], color="0.3", marker="o", mfc="white", mew=1.1, ls="none", label="experiment"),
          Line2D([], [], color="0.3", lw=1.6, label="model")]
    fig.legend(handles=hc + hp, ncol=6, loc="lower center", frameon=False,
               bbox_to_anchor=(0.5, -0.005), columnspacing=1.3, handletextpad=0.5)
    fig.suptitle("Pool-boiling curves: validated gray-box model vs. experiment",
                 fontsize=11, y=0.995)
    fig.tight_layout(rect=(0, 0.035, 1, 0.985))
    fig.savefig(f"{OUT}/fig_boiling_curves.pdf"); fig.savefig(f"{OUT}/fig_boiling_curves.png")
    plt.close(fig)


# ============================================================================
# FIGURE 2 -- parity (predicted vs measured chip surface temperature)
# ============================================================================
def fig_parity(stats):
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    allm, allp = [], []
    for cfg in CONFIGS:
        gk, chip = cfg; pts = cm.points(gk, chip)
        me = [p["Tsurf"] for p in pts]; pr = [predict(p) for p in pts]
        allm += me; allp += pr
        ax.plot(me, pr, MARK[cfg], color=CT["30"] if False else None, mfc="none", mew=0.9,
                ms=4.2, label=LABELS[cfg], alpha=0.85)
    lo, hi = min(allm + allp) - 3, max(allm + allp) + 3
    ax.plot([lo, hi], [lo, hi], "k-", lw=1.0, zorder=1)
    for d, ls in [(5, "--"), (-5, "--")]:
        ax.plot([lo, hi], [lo + d, hi + d], color="0.5", ls=ls, lw=0.8, zorder=1)
    ax.text(0.96, 0.10, r"$\pm 5\ \mathrm{K}$", transform=ax.transAxes, ha="right",
            color="0.4", fontsize=8)
    o = stats["overall"]
    ax.text(0.04, 0.96,
            rf"$\mathrm{{RMSE}}={o['rmse']:.2f}\ \mathrm{{K}}$" "\n"
            rf"$\mathrm{{MAE}}={o['mae']:.2f}\ \mathrm{{K}}$" "\n"
            rf"$R^2={o['r2']:.3f}$" "\n"
            rf"$n={o['n']}$",
            transform=ax.transAxes, va="top", ha="left", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="0.7", lw=0.6))
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    ax.set_xlabel(r"measured $T_{\mathrm{surf}}\;[^{\circ}\mathrm{C}]$")
    ax.set_ylabel(r"predicted $T_{\mathrm{surf}}\;[^{\circ}\mathrm{C}]$")
    ax.set_title("Predictive parity (geometry + BC only)", pad=4)
    ax.legend(loc="lower right", frameon=False, fontsize=7.5, handletextpad=0.3)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig_parity.pdf"); fig.savefig(f"{OUT}/fig_parity.png")
    plt.close(fig)


# ============================================================================
# FIGURE 3 -- residual structure + distribution
# ============================================================================
def fig_residuals(stats):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.3),
                                 gridspec_kw=dict(width_ratios=[2, 1]))
    allr = []
    for cfg in CONFIGS:
        gk, chip = cfg; pts = cm.points(gk, chip)
        me = np.array([p["Tsurf"] for p in pts]); pr = np.array([predict(p) for p in pts])
        r = pr - me; allr += list(r)
        a1.plot(me, r, MARK[cfg], color=None, mfc="none", mew=0.9, ms=4.0,
                label=LABELS[cfg], alpha=0.8)
    allr = np.array(allr)
    a1.axhline(0, color="k", lw=0.9)
    a1.axhline(allr.mean(), color="#c0392b", ls="--", lw=0.9)
    a1.fill_between([min([p["Tsurf"] for p in cm.points()]) - 2,
                     max([p["Tsurf"] for p in cm.points()]) + 2],
                    allr.mean() - allr.std(), allr.mean() + allr.std(),
                    color="0.6", alpha=0.18, zorder=0)
    a1.set_xlabel(r"measured $T_{\mathrm{surf}}\;[^{\circ}\mathrm{C}]$")
    a1.set_ylabel(r"residual $T_{\mathrm{pred}}-T_{\mathrm{meas}}\;[\mathrm{K}]$")
    a1.set_title("Residual vs. surface temperature", pad=4)
    a1.legend(loc="upper right", frameon=False, fontsize=7, ncol=2, handletextpad=0.3,
              columnspacing=0.8)
    a1.text(0.03, 0.05, rf"bias $={allr.mean():+.2f}$ K,  $\sigma={allr.std():.2f}$ K",
            transform=a1.transAxes, fontsize=8, va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", lw=0.6, alpha=0.9))

    a2.hist(allr, bins=22, color="#4a6fa5", edgecolor="white", linewidth=0.4, density=True)
    x = np.linspace(allr.min(), allr.max(), 200)
    a2.plot(x, np.exp(-0.5 * ((x - allr.mean()) / allr.std()) ** 2) /
            (allr.std() * np.sqrt(2 * np.pi)), "k-", lw=1.2)
    a2.axvline(0, color="0.4", lw=0.8, ls=":")
    a2.set_xlabel(r"residual $[\mathrm{K}]$"); a2.set_ylabel("density")
    a2.set_title("Distribution", pad=4)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig_residuals.pdf"); fig.savefig(f"{OUT}/fig_residuals.png")
    plt.close(fig)


# ============================================================================
# numerical analysis: per-config + overall metrics, LOCO, table + CSV
# ============================================================================
def analyse():
    rows, allm, allp, csv_rows = [], [], [], []
    for cfg in CONFIGS:
        gk, chip = cfg; pts = cm.points(gk, chip)
        me = np.array([p["Tsurf"] for p in pts]); pr = np.array([predict(p) for p in pts])
        r = pr - me; allm += list(me); allp += list(pr)
        ss_res = float(np.sum(r ** 2)); ss_tot = float(np.sum((me - me.mean()) ** 2))
        rows.append(dict(cfg=LABELS[cfg], n=len(pts), rmse=cm.rmse(pr, me),
                         mae=float(np.mean(np.abs(r))), maxe=float(np.max(np.abs(r))),
                         bias=float(np.mean(r)), std=float(np.std(r)),
                         r2=1 - ss_res / ss_tot))
        for p, pp in zip(pts, pr):
            csv_rows.append([gk + "-tube", chip, p["t"], p["q"], p["Tin"],
                             p["Tsurf"], round(pp, 3), round(pp - p["Tsurf"], 3)])
    allm, allp = np.array(allm), np.array(allp); ar = allp - allm
    overall = dict(n=len(allm), rmse=cm.rmse(allp, allm), mae=float(np.mean(np.abs(ar))),
                   maxe=float(np.max(np.abs(ar))), bias=float(np.mean(ar)), std=float(np.std(ar)),
                   r2=1 - float(np.sum(ar ** 2)) / float(np.sum((allm - allm.mean()) ** 2)))
    loco = {gk: cm.leave_one_coolant_out(gk) for gk in ["33", "42"]}

    # CSV of every prediction
    with open(f"{OUT}/predictions.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["condenser", "chip", "coolant_C", "q_Wcm2", "Tin_C",
                    "Tsurf_meas_C", "Tsurf_pred_C", "residual_K"])
        w.writerows(csv_rows)

    # LaTeX table (booktabs)
    with open(f"{OUT}/results_table.tex", "w") as f:
        f.write(r"""\begin{table}[t]
\centering
\caption{Predictive accuracy of the gray-box model for the chip surface
temperature. Predictions use the full geometry-to-temperature chain with
fitted, geometry-independent boiling coefficients; no per-point tuning.
RMSE, MAE and maximum absolute error are in kelvin; bias is the signed mean
residual. The leave-one-coolant-out (LOCO) column is the held-out RMSE when an
entire coolant-inlet condition is withheld from the calibration.}
\label{tab:accuracy}
\begin{tabular}{lrrrrrrr}
\toprule
Configuration & $n$ & RMSE & MAE & $\max|e|$ & bias & $R^2$ & LOCO \\
\midrule
""")
        loco_by = {"33-tube, plain copper": loco["33"], "33-tube, microchannel": loco["33"],
                   "42-tube, plain copper": loco["42"], "42-tube, microchannel": loco["42"]}
        for r in rows:
            lc = loco_by[r["cfg"]]
            f.write(f"{r['cfg']} & {r['n']} & {r['rmse']:.2f} & {r['mae']:.2f} & "
                    f"{r['maxe']:.2f} & {r['bias']:+.2f} & {r['r2']:.3f} & {lc:.2f} \\\\\n")
        f.write(r"\midrule" "\n")
        f.write(f"\\textbf{{All data}} & {overall['n']} & {overall['rmse']:.2f} & "
                f"{overall['mae']:.2f} & {overall['maxe']:.2f} & {overall['bias']:+.2f} & "
                f"{overall['r2']:.3f} & -- \\\\\n")
        f.write(r"""\bottomrule
\end{tabular}
\end{table}
""")
    return dict(rows=rows, overall=overall, loco=loco)


def main():
    stats = analyse()
    fig_boiling()
    fig_parity(stats)
    fig_residuals(stats)
    o = stats["overall"]
    print("Per-configuration accuracy (chip surface temperature):")
    print(f"{'configuration':28s}{'n':>4}{'RMSE':>7}{'MAE':>7}{'max|e|':>8}{'bias':>7}{'R2':>7}")
    for r in stats["rows"]:
        print(f"{r['cfg']:28s}{r['n']:>4}{r['rmse']:>7.2f}{r['mae']:>7.2f}"
              f"{r['maxe']:>8.2f}{r['bias']:>+7.2f}{r['r2']:>7.3f}")
    print(f"{'ALL DATA':28s}{o['n']:>4}{o['rmse']:>7.2f}{o['mae']:>7.2f}"
          f"{o['maxe']:>8.2f}{o['bias']:>+7.2f}{o['r2']:>7.3f}")
    print(f"\nLeave-one-coolant-out held-out RMSE:  33-tube {stats['loco']['33']:.2f} K,"
          f"  42-tube {stats['loco']['42']:.2f} K")
    print(f"\nFigures + table + CSV in {OUT}/")


if __name__ == "__main__":
    main()
