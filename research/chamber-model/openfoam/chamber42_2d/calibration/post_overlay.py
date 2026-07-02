#!/usr/bin/env python3
"""
Overlay the SIMULATED 2D boiling curve on the MEASURED 42-tube/plain curve.
Reads each completed probe case under cal_runs/ (chip wall temperature from the
folder name, quasi-steady q'' from chipHeatFlux.dat) and the measured target
(targets_42plain.json). Produces the CFD-vs-experiment figure.

USAGE:  python post_overlay.py --runs ../cal_runs --targets targets_42plain.json
"""
import os, re, json, argparse, glob
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

AVG_WINDOW = 0.3


def steady_q(case):
    f = os.path.join(case, "chipHeatFlux.dat")
    if not os.path.isfile(f):
        return None
    a = np.array([l.split() for l in open(f) if l.strip() and not l.startswith("#")], float)
    n0 = int(len(a) * (1.0 - AVG_WINDOW))
    return float(a[n0:, 2].mean())


def collect(runs):
    pts = []
    for case in sorted(glob.glob(os.path.join(runs, "*Tw*"))):
        m = re.search(r"Tw(\d+(?:\.\d+)?)", os.path.basename(case))
        if not m:
            continue
        q = steady_q(case)
        if q is not None:
            pts.append((float(m.group(1)), q))
    return np.array(sorted(pts)) if pts else np.empty((0, 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="../cal_runs")
    ap.add_argument("--targets", default="targets_42plain.json")
    ap.add_argument("--coeffs", default="../calibrated_coeffs.json")
    ap.add_argument("--out", default="cfd_vs_experiment_42plain.png")
    a = ap.parse_args()
    t = json.load(open(a.targets))
    Tm = np.array([p["Tsurf_C"] for p in t["points"]])
    qm = np.array([p["q_Wcm2"] for p in t["points"]])
    o = np.argsort(Tm); Tm, qm = Tm[o], qm[o]
    sim = collect(a.runs)
    label = "2D VOF (Lee, calibrated)"
    if os.path.isfile(a.coeffs):
        c = json.load(open(a.coeffs))
        label = f"2D VOF: coeffE={c['coeffE']:.3g}, coeffC={c['coeffC']:.3g}"
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(Tm, qm, "o-", color="#2c3e50", label="measured 42-tube / plain")
    if "CHF_Wcm2" in t:
        ax.axhline(t["CHF_Wcm2"], ls=":", color="#c0392b",
                   label=f"measured CHF = {t['CHF_Wcm2']:.0f} W/cm$^2$")
    if len(sim):
        ax.plot(sim[:, 0], sim[:, 1], "s--", color="#2980b9", label=label)
    ax.set_xlabel("chip surface temperature (C)")
    ax.set_ylabel("heat flux q'' (W/cm$^2$)")
    ax.set_title("2D demonstration: simulated vs measured boiling curve")
    ax.grid(alpha=0.3); ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(a.out, dpi=160)
    print(f"measured points: {len(Tm)}, simulated points: {len(sim)}; wrote {a.out}")


if __name__ == "__main__":
    main()
