#!/usr/bin/env python3
"""
Calibrate the interCondensatingEvaporatingFoam phase-change coefficients
(coeffE evaporation, coeffC condensation) for the 2D chamber42_2d case against
the MEASURED 42-tube / plain-copper boiling curve and CHF.

WHAT THIS IS
------------
A workstation-scale orchestrator. Each objective evaluation launches a small set
of full 2D VOF solves (one per chip wall temperature) to quasi-stationarity. In
2D each solve is minutes-to-hours on a desktop, so this can run locally; it does
NOT need a cluster (unlike the 3D version). The two coefficients are fit by
Nelder-Mead so the simulated boiling curve q''(T_wall) matches the measured curve
and turns over near the measured CHF.

The mapping is MESH-DEPENDENT (the Lee coefficient interacts with interface cell
size); re-calibrate if the mesh changes. coeffE is the primary knob for the
boiling branch; coeffC mainly affects the condensing (cold-surface) side.

The 2D condenser is the idealised cold top surface (see ../README.md), so 2D
coefficients DEMONSTRATE the pipeline and do not transfer quantitatively to 3D.

EXTRACTION
----------
Each case appends chipHeatFlux.dat:   time   q''[W/m2]   q''[W/cm2]   Q[W]
We take the mean over the last AVG_WINDOW fraction (quasi-steady value).

USAGE
-----
    python calibrate_lee_2d.py --targets targets_42plain.json --template .. \
        --runner local --max-iter 15
"""
import os, re, json, shutil, subprocess, argparse
import numpy as np

PROBE_TWALL_C = [48, 52, 58, 65, 75, 85]   # spans onset (Tsat~49 C) through boiling
TSAT_K = 322.0                              # matches constant/thermophysicalProperties
AVG_WINDOW = 0.3
CHF_PENALTY_WEIGHT = 2.0


def load_targets(path):
    t = json.load(open(path)); pts = t["points"]
    Ts = np.array([p["Tsurf_C"] for p in pts]); q = np.array([p["q_Wcm2"] for p in pts])
    o = np.argsort(Ts); return Ts[o], q[o], float(t["CHF_Wcm2"])


def write_coeffs(case, coeffE, coeffC):
    p = os.path.join(case, "constant", "phaseChangeProperties")
    if not os.path.isfile(p):                       # create if absent
        open(p, "w").write(
            "FoamFile { version 2.0; format ascii; class dictionary; "
            "object phaseChangeProperties; }\nphaseChangeTwoPhaseModel constant;\n"
            "constantCoeffs { coeffC coeffC [0 0 -1 -1 0 0 0] %g; "
            "coeffE coeffE [0 0 -1 -1 0 0 0] %g; }\n" % (coeffC, coeffE))
        return
    txt = open(p).read()
    txt = re.sub(r"coeffC coeffC \[[^]]*\] [0-9.eE+-]+",
                 f"coeffC coeffC [0 0 -1 -1 0 0 0] {coeffC:g}", txt)
    txt = re.sub(r"coeffE coeffE \[[^]]*\] [0-9.eE+-]+",
                 f"coeffE coeffE [0 0 -1 -1 0 0 0] {coeffE:g}", txt)
    open(p, "w").write(txt)


def set_chip_Twall(case, Twall_K):
    p = os.path.join(case, "0.orig", "T")
    txt = open(p).read()
    txt = re.sub(r"(chip\s*\{[^}]*?value\s+uniform\s+)[0-9.eE+-]+",
                 rf"\g<1>{Twall_K:g}", txt, flags=re.S)
    open(p, "w").write(txt)


def run_case(case, runner):
    if runner == "slurm":
        subprocess.run(["sbatch", "--wait", "Allrun.cluster"], cwd=case, check=True)
    else:
        subprocess.run(["./Allrun"], cwd=case, check=True)


def read_steady_q(case):
    f = os.path.join(case, "chipHeatFlux.dat")
    rows = [l.split() for l in open(f) if l.strip() and not l.startswith("#")]
    t = np.array([float(r[0]) for r in rows]); qcm2 = np.array([float(r[2]) for r in rows])
    n0 = int(len(t) * (1.0 - AVG_WINDOW)); return float(np.mean(qcm2[n0:]))


def simulate_curve(template, coeffE, coeffC, runner, workdir="cal_runs"):
    os.makedirs(workdir, exist_ok=True); q_sim = []
    for Tc in PROBE_TWALL_C:
        case = os.path.join(workdir, f"E{coeffE:g}_C{coeffC:g}_Tw{Tc}")
        if not os.path.isdir(case):
            shutil.copytree(template, case, ignore=shutil.ignore_patterns(
                "cal_runs", "VTK", "postProcessing", "0", "0.0*", "0.[0-9]*",
                "processor*", "*.png", "chipHeatFlux.dat"))
        write_coeffs(case, coeffE, coeffC); set_chip_Twall(case, Tc + 273.15)
        run_case(case, runner); q_sim.append(read_steady_q(case))
    return np.array(PROBE_TWALL_C, float), np.array(q_sim, float)


def objective(params, template, targets, runner):
    coeffE, coeffC = params; Ts_m, q_m, chf = targets
    Tw, q_s = simulate_curve(template, coeffE, coeffC, runner)
    q_m_at = np.interp(Tw, Ts_m, q_m); resid = q_s - q_m_at
    chf_pen = CHF_PENALTY_WEIGHT * max(0.0, q_s.max() - chf)
    rms = float(np.sqrt(np.mean(resid**2)))
    print(f"  coeffE={coeffE:.4g} coeffC={coeffC:.4g} -> RMS={rms:.3f} W/cm2, "
          f"q_sim_max={q_s.max():.1f}, CHFpen={chf_pen:.2f}", flush=True)
    return rms + chf_pen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="targets_42plain.json")
    ap.add_argument("--template", default="..")
    ap.add_argument("--runner", choices=["slurm", "local"], default="local")
    ap.add_argument("--max-iter", type=int, default=15)
    ap.add_argument("--E0", type=float, default=0.1)
    ap.add_argument("--C0", type=float, default=1.0)
    args = ap.parse_args()
    targets = load_targets(args.targets)
    from scipy.optimize import minimize
    res = minimize(objective, x0=[args.E0, args.C0],
                   args=(args.template, targets, args.runner), method="Nelder-Mead",
                   options={"maxiter": args.max_iter, "xatol": 1e-3, "fatol": 1e-2})
    print("\ncalibrated:", res.x, "final objective:", res.fun)
    json.dump({"coeffE": float(res.x[0]), "coeffC": float(res.x[1]),
               "objective_Wcm2": float(res.fun), "probe_Twall_C": PROBE_TWALL_C},
              open("calibrated_coeffs.json", "w"), indent=1)
    print("wrote calibrated_coeffs.json")


if __name__ == "__main__":
    main()
