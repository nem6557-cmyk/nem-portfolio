#!/usr/bin/env python3
"""
Overlay the chamber42_2d fixed-time demonstration sweep on the measured 42-plain
boiling curve. The simulated points are chip flux at a FIXED simulation time (not
converged steady values); the plot and its caption state this explicitly.
USAGE:  python plot_sweep_demo.py sweep_demo_E<..>.csv [--targets calibration/targets_42plain.json]
"""
import sys, json, argparse
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--targets", default="calibration/targets_42plain.json")
ap.add_argument("--out", default="cfd_vs_experiment_42plain.png")
a = ap.parse_args()

# simulated sweep
rows = [l.split(",") for l in open(a.csv) if l.strip() and not l.startswith("#")]
Tw = np.array([float(r[0]) for r in rows]); qs = np.array([float(r[1]) for r in rows])

# measured curve: 20 C coolant branch (low Tsat, matches sim TSat=322 K=49 C)
tg = json.load(open(a.targets))
pts = [p for p in tg["points"] if abs(p["coolant_C"] - 20.0) < 1e-6]
Tm = np.array([p["Tsurf_C"] for p in pts]); qm = np.array([p["q_Wcm2"] for p in pts])
o = np.argsort(Tm); Tm, qm = Tm[o], qm[o]
chf = tg.get("CHF_Wcm2")

fig, ax = plt.subplots(figsize=(7.2, 5))
ax.plot(Tm, qm, "o-", color="#2c3e50", ms=5, lw=1.6, label="measured 42-plain (20 C coolant)")
if chf: ax.axhline(chf, ls=":", color="#c0392b", lw=1.3, label=f"measured CHF = {chf:g} W/cm$^2$")
ax.plot(Tw, qs, "s--", color="#2980b9", ms=7, lw=1.8,
        label="2D sim, chip flux at fixed sim time\n(NOT converged; demonstration only)")
ax.set_xlabel("chip wall temperature (C)"); ax.set_ylabel("chip heat flux q'' (W/cm$^2$)")
ax.set_title("2D demonstration sweep vs measured boiling curve")
ax.grid(alpha=0.3); ax.legend(fontsize=8.5, loc="upper left")
fig.tight_layout(); fig.savefig(a.out, dpi=160)
print(f"wrote {a.out}  ({len(Tw)} sim points vs {len(Tm)} measured points)")
