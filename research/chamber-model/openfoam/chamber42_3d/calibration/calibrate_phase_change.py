#!/usr/bin/env python3
"""
Calibrate the interCondensatingEvaporatingFoam phase-change coefficients
(coeffE evaporation, coeffC condensation) against the MEASURED 42-tube
plain-copper boiling curve and CHF.

WHAT THIS IS
------------
An ORCHESTRATOR, not a sandbox run. Every objective evaluation launches a set
of full 3D VOF solves (one per wall superheat) on the refined mesh. Each solve
is hours-to-days of HPC wall time, so this script is meant to be driven by a
cluster scheduler, not executed interactively. It is provided so the calibration
loop is fully specified and reproducible.

METHOD
------
The constant (Lee-type) phase-change model relieves interfacial super-heat /
sub-cooling at a rate set by coeffE / coeffC [1/(s.K)]. For a heated chip held
at wall temperature T_w, the resolved interfacial evaporation + conduction +
convection produce a chip heat flux q''(T_w). Sweeping T_w builds a SIMULATED
boiling curve. We adjust (coeffE, coeffC) so that curve matches the measured
Rohsenow curve and so that the simulated curve turns over (vapour blanketing,
wall-T runaway) at the measured CHF.

Note the mapping is indirect and MESH-DEPENDENT: the Lee coefficient interacts
with cell size at the interface. Re-calibrate if the mesh changes. coeffE is the
primary knob for the boiling branch; coeffC mainly affects the condensing tubes.

EXTRACTION
----------
Each case writes chipHeatFlux.dat (see system/chipHeatFlux):
    time   q''[W/m2]   q''[W/cm2]   Q[W]
We take the time-average over the last `avg_window` fraction of the run as the
quasi-steady value. Confirm the functionObject compiles against your build.

USAGE (on a cluster)
--------------------
    python calibrate_phase_change.py --targets targets_42plain.json \
        --template ../ --runner slurm --max-iter 25
"""
import os, re, json, shutil, subprocess, argparse
import numpy as np

# ----- wall temperatures to probe the boiling branch (deg C -> K) -----
# chosen to span the measured Tsurf range; CHF point included to test turn-over
PROBE_TWALL_C = [50, 60, 70, 78, 85, 90]
TSAT_K = 338.0
AVG_WINDOW = 0.3          # average q'' over the last 30% of each run (quasi-steady)
CHF_PENALTY_WEIGHT = 2.0  # weight on reproducing the CHF turn-over


def load_targets(path):
    t = json.load(open(path))
    pts = t["points"]
    Ts = np.array([p["Tsurf_C"] for p in pts])
    q = np.array([p["q_Wcm2"] for p in pts])
    # monotone reference curve q_meas(Tsurf) by sorting + interpolation
    o = np.argsort(Ts)
    return Ts[o], q[o], float(t["CHF_Wcm2"])


def write_coeffs(case, coeffE, coeffC):
    """Patch constant/phaseChangeProperties for this candidate."""
    p = os.path.join(case, "constant", "phaseChangeProperties")
    txt = open(p).read()
    txt = re.sub(r"coeffC coeffC \[[^]]*\] [0-9.eE+-]+",
                 f"coeffC coeffC [0 0 -1 -1 0 0 0] {coeffC:g}", txt)
    txt = re.sub(r"coeffE coeffE \[[^]]*\] [0-9.eE+-]+",
                 f"coeffE coeffE [0 0 -1 -1 0 0 0] {coeffE:g}", txt)
    open(p, "w").write(txt)


def set_chip_Twall(case, Twall_K):
    """Set the chip patch fixedValue temperature in 0/T."""
    p = os.path.join(case, "0", "T")
    txt = open(p).read()
    # assumes a chip { type fixedValue; value uniform <T>; } entry exists
    txt = re.sub(r"(chip\s*\{[^}]*?value\s+uniform\s+)[0-9.eE+-]+",
                 rf"\g<1>{Twall_K:g}", txt, flags=re.S)
    open(p, "w").write(txt)


def run_case(case, runner):
    """Launch one solve. Returns when it finishes (blocking)."""
    if runner == "slurm":
        subprocess.run(["sbatch", "--wait", "Allrun.cluster"], cwd=case, check=True)
    else:  # local (only for a tiny smoke test, NOT a converged run)
        subprocess.run(["./Allrun"], cwd=case, check=True)


def read_steady_q(case):
    """Time-average q''[W/cm2] over the last AVG_WINDOW of chipHeatFlux.dat."""
    f = os.path.join(case, "chipHeatFlux.dat")
    rows = [l.split() for l in open(f) if l.strip() and not l.startswith("#")]
    t = np.array([float(r[0]) for r in rows])
    qcm2 = np.array([float(r[2]) for r in rows])
    n0 = int(len(t) * (1.0 - AVG_WINDOW))
    return float(np.mean(qcm2[n0:]))


def simulate_curve(template, coeffE, coeffC, runner, workdir="cal_runs"):
    """Run the probe set for one (coeffE, coeffC); return (Twall_C, q_sim[W/cm2])."""
    os.makedirs(workdir, exist_ok=True)
    q_sim = []
    for Tc in PROBE_TWALL_C:
        case = os.path.join(workdir, f"E{coeffE:g}_C{coeffC:g}_Tw{Tc}")
        if not os.path.isdir(case):
            shutil.copytree(template, case, ignore=shutil.ignore_patterns(
                "cal_runs", "VTK", "post", "0.0*", "processor*", "*.png"))
        write_coeffs(case, coeffE, coeffC)
        set_chip_Twall(case, Tc + 273.15)
        run_case(case, runner)
        q_sim.append(read_steady_q(case))
    return np.array(PROBE_TWALL_C, float), np.array(q_sim, float)


def objective(params, template, targets, runner):
    coeffE, coeffC = params
    Ts_m, q_m, chf = targets
    Tw, q_s = simulate_curve(template, coeffE, coeffC, runner)
    # interpolate measured curve onto the simulated wall temperatures
    q_m_at = np.interp(Tw, Ts_m, q_m)
    resid = q_s - q_m_at
    # CHF turn-over penalty: simulated curve should not exceed measured CHF before turn-over
    chf_pen = CHF_PENALTY_WEIGHT * max(0.0, q_s.max() - chf)
    rms = float(np.sqrt(np.mean(resid**2)))
    print(f"  coeffE={coeffE:.4g} coeffC={coeffC:.4g} -> RMS={rms:.3f} W/cm2, "
          f"q_sim_max={q_s.max():.1f}, CHFpen={chf_pen:.2f}")
    return rms + chf_pen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="targets_42plain.json")
    ap.add_argument("--template", default="..")
    ap.add_argument("--runner", choices=["slurm", "local"], default="slurm")
    ap.add_argument("--max-iter", type=int, default=25)
    ap.add_argument("--E0", type=float, default=0.1)   # initial coeffE
    ap.add_argument("--C0", type=float, default=1.0)   # initial coeffC
    args = ap.parse_args()

    targets = load_targets(args.targets)
    from scipy.optimize import minimize
    res = minimize(objective, x0=[args.E0, args.C0],
                   args=(args.template, targets, args.runner),
                   method="Nelder-Mead",
                   options={"maxiter": args.max_iter, "xatol": 1e-3, "fatol": 1e-2})
    print("\ncalibrated:", res.x, "final objective:", res.fun)
    json.dump({"coeffE": float(res.x[0]), "coeffC": float(res.x[1]),
               "objective_Wcm2": float(res.fun)},
              open("calibrated_coeffs.json", "w"), indent=1)


if __name__ == "__main__":
    main()
