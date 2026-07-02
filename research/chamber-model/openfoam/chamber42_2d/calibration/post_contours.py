#!/usr/bin/env python3
"""
Render T, alpha.water, |U| and p_rgh contours for a chamber42_2d solve.
Reads the OpenFOAM case with PyVista (creates a <case>.foam stub if needed),
takes the last write time, and draws the four fields on the x-z plane. Because
the mesh is one cell thick in y, cell-centre values are contoured directly with
matplotlib (robust to the thin slab).

USAGE:  python post_contours.py [path/to/case] [--time last]
"""
import os, sys, argparse
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri


def read_case(case, which="last"):
    import pyvista as pv
    foam = os.path.join(case, "case.foam")
    if not os.path.isfile(foam):
        open(foam, "w").close()
    rd = pv.OpenFOAMReader(foam)
    times = list(rd.time_values)
    t = times[-1] if which == "last" else float(which)
    rd.set_active_time_value(min(times, key=lambda v: abs(v - t)))
    mesh = rd.read()
    internal = mesh["internalMesh"] if "internalMesh" in mesh.keys() else mesh.combine()
    cc = internal.cell_centers().points
    cd = internal.cell_data
    def f(name):
        return np.asarray(cd[name]) if name in cd else None
    U = f("U")
    fields = {
        "T (C)": (f("T") - 273.15) if f("T") is not None else None,
        "alpha.water": f("alpha.water"),
        "|U| (m/s)": np.linalg.norm(U, axis=1) if U is not None else None,
        "p_rgh (Pa)": f("p_rgh"),
    }
    return cc[:, 0], cc[:, 2], fields, t


def render(x, z, fields, t, out):
    items = [(k, v) for k, v in fields.items() if v is not None]
    n = len(items); ncol = 2; nrow = int(np.ceil(n / ncol))
    tri = mtri.Triangulation(x * 1e3, z * 1e3)
    fig, axes = plt.subplots(nrow, ncol, figsize=(11, 3.6 * nrow), squeeze=False)
    cmaps = {"T (C)": "inferno", "alpha.water": "Blues", "|U| (m/s)": "viridis",
             "p_rgh (Pa)": "coolwarm"}
    for ax, (name, val) in zip(axes.flat, items):
        lv = np.linspace(np.nanmin(val), np.nanmax(val), 24) if np.nanmin(val) != np.nanmax(val) else 24
        c = ax.tricontourf(tri, val, levels=lv, cmap=cmaps.get(name, "viridis"))
        plt.colorbar(c, ax=ax, shrink=0.9)
        ax.set_title(name); ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm)")
        ax.set_aspect("equal")
    for ax in axes.flat[n:]:
        ax.axis("off")
    fig.suptitle(f"chamber42_2d fields at t = {t*1e3:.1f} ms", y=1.0)
    fig.tight_layout(); fig.savefig(out, dpi=160)
    print(f"wrote {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case", nargs="?", default="..")
    ap.add_argument("--time", default="last")
    ap.add_argument("--out", default="fields_2d.png")
    a = ap.parse_args()
    x, z, fields, t = read_case(a.case, a.time)
    render(x, z, fields, t, a.out)


if __name__ == "__main__":
    main()
