#!/usr/bin/env python3
"""
Convergence / stationarity check for a chamber42_2d solve.
Reads chipHeatFlux.dat (time, q''[W/m2], q''[W/cm2], Q[W]) written by the
chipHeatFlux functionObject and plots q'' vs time with a running mean. Reports
whether the chip heat flux has levelled (quasi-steady), which is the signal that
the run is long enough to read a boiling-curve point.

USAGE:  python post_convergence.py [path/to/chipHeatFlux.dat] [--tail 0.3]
"""
import sys, argparse
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path):
    rows = [l.split() for l in open(path) if l.strip() and not l.startswith("#")]
    a = np.array(rows, float)
    return a[:, 0], a[:, 2]            # time [s], q'' [W/cm2]


def running_mean(t, q, tail):
    rm = np.array([q[: i + 1].mean() for i in range(len(q))])   # cumulative mean
    n0 = int(len(q) * (1.0 - tail))
    drift = (q[n0:].max() - q[n0:].min()) / max(abs(q[n0:].mean()), 1e-9)
    return rm, drift, q[n0:].mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dat", nargs="?", default="chipHeatFlux.dat")
    ap.add_argument("--tail", type=float, default=0.3)
    ap.add_argument("--out", default="convergence.png")
    a = ap.parse_args()
    t, q = load(a.dat)
    rm, drift, qbar = running_mean(t, q, a.tail)
    steady = drift < 0.05
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(t * 1e3, q, color="#7f8c8d", lw=0.8, label="instantaneous")
    ax.plot(t * 1e3, rm, color="#c0392b", lw=2, label="running mean")
    ax.axhline(qbar, ls="--", color="#2c3e50", lw=1,
               label=f"last {int(a.tail*100)}% mean = {qbar:.2f} W/cm$^2$")
    ax.set_xlabel("time (ms)"); ax.set_ylabel("chip heat flux q'' (W/cm$^2$)")
    ax.set_title(f"Convergence: drift over last {int(a.tail*100)}% = {drift*100:.1f}% "
                 f"({'STEADY' if steady else 'NOT yet steady'})")
    ax.grid(alpha=0.3); ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(a.out, dpi=160)
    print(f"q'' last-{int(a.tail*100)}% mean = {qbar:.3f} W/cm2, drift = {drift*100:.2f}%, "
          f"steady = {steady}")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
