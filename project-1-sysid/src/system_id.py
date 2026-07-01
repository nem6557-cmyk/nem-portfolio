"""
system_id.py
============
Sim-to-real parameter identification for the 3-DOF arm.

The problem this solves
-----------------------
You can model a robot's geometry and mass perfectly and still miss on
dynamics, because the friction, damping, and true motor torque constant are not
on any drawing. They have to be measured on the physical machine. This pipeline
demonstrates the standard closed loop:

    1. Treat one MJCF as the "real robot" with unknown-to-us friction, damping,
       and a motor that delivers only 85% of nominal torque.
    2. Excite it with a rich multi-sine motion and log the commanded joint
       torques and the (noisy) measured joint angles. This is the stand-in for
       a bench data-collection run on real hardware.
    3. Start from a deliberately wrong "nominal" model (no thermal/friction
       knowledge, full nominal torque) and identify the seven physical
       parameters by minimising a multiple-shooting prediction error.
    4. Validate the identified model on a *different* trajectory it never saw
       during fitting, which is the real test of whether the gap actually
       closed.

Everything below runs headless and writes figures into ../results.

Identified parameters (theta):
    [ d1, d2, d3,  f1, f2, f3,  gear ]
    damping [N m s/rad] x3, dry friction [N m] x3, motor gain [-].
"""

from __future__ import annotations

import os
import numpy as np
import mujoco
from scipy.optimize import least_squares

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(HERE, "models", "arm3.xml")
RESULTS = os.path.join(HERE, "results")
os.makedirs(RESULTS, exist_ok=True)

rng = np.random.default_rng(7)

# Truth, read straight from the generated model so there is a single source.
_m0 = mujoco.MjModel.from_xml_path(MODEL_PATH)
THETA_TRUE = np.concatenate([
    np.array(_m0.dof_damping, dtype=float),
    np.array(_m0.dof_frictionloss, dtype=float),
    [float(_m0.actuator_gear[0, 0])],
])
NJ = _m0.nq  # 3

# A naive first guess: friction/damping underestimated, motor assumed nominal.
THETA_INIT = np.array([0.10, 0.10, 0.10, 0.05, 0.05, 0.05, 1.00])

# Control / logging cadence.
PHYS_DT = float(_m0.opt.timestep)     # 0.001 s
CTRL_EVERY = 2                        # apply control every 2 physics steps
CTRL_DT = PHYS_DT * CTRL_EVERY        # 0.002 s
DURATION = 4.0                        # seconds per trajectory
N = int(DURATION / CTRL_DT)

# Measurement noise (position encoders + velocity estimate).
POS_NOISE = 0.002    # rad, ~0.11 deg
VEL_NOISE = 0.02     # rad/s

# PD gains used only to generate exciting, bounded motion.
KP = np.array([25.0, 30.0, 15.0])
KD = np.array([2.0, 2.5, 1.2])


def set_theta(model: mujoco.MjModel, theta: np.ndarray) -> None:
    """Write a parameter vector into a MuJoCo model in place."""
    model.dof_damping[:] = theta[0:NJ]
    model.dof_frictionloss[:] = theta[NJ:2 * NJ]
    model.actuator_gear[:, 0] = theta[2 * NJ]


def multisine(t: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Per-joint reference angle and rate, a sum of sines with random phase.

    Frequencies are chosen to force velocity reversals (excites dry friction)
    across a spread of speeds (excites viscous damping).
    """
    r = np.random.default_rng(seed)
    freqs = np.array([0.3, 0.7, 1.3])          # Hz
    weights = np.array([1.0, 0.5, 0.25])
    amp = np.array([0.6, 0.5, 0.7])            # rad, per joint
    q = np.zeros((t.size, NJ))
    qd = np.zeros((t.size, NJ))
    for j in range(NJ):
        ph = r.uniform(0, 2 * np.pi, size=freqs.size)
        for f, w, p in zip(freqs, weights, ph):
            q[:, j] += amp[j] * w * np.sin(2 * np.pi * f * t + p)
            qd[:, j] += amp[j] * w * 2 * np.pi * f * np.cos(2 * np.pi * f * t + p)
    return q, qd


def collect_dataset(theta: np.ndarray, seed: int):
    """Run the 'real' arm under PD tracking; log commands and noisy states.

    Returns dict with time, commanded torque u, true and measured (q, qd).
    """
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    set_theta(model, theta)
    data = mujoco.MjData(model)

    t = np.arange(N) * CTRL_DT
    q_ref, qd_ref = multisine(t, seed)

    u_log = np.zeros((N, NJ))
    q_true = np.zeros((N, NJ))
    qd_true = np.zeros((N, NJ))

    # Start at the reference so there is no startup transient.
    data.qpos[:] = q_ref[0]
    data.qvel[:] = qd_ref[0]
    mujoco.mj_forward(model, data)

    for k in range(N):
        q = data.qpos.copy()
        qd = data.qvel.copy()
        # PD command in controller units (motor delivers gear*ctrl).
        u = KP * (q_ref[k] - q) + KD * (qd_ref[k] - qd)
        u = np.clip(u, -40, 40)
        data.ctrl[:] = u
        u_log[k] = u
        q_true[k] = q
        qd_true[k] = qd
        for _ in range(CTRL_EVERY):
            mujoco.mj_step(model, data)

    q_meas = q_true + rng.normal(0, POS_NOISE, q_true.shape)
    qd_meas = qd_true + rng.normal(0, VEL_NOISE, qd_true.shape)
    return dict(t=t, u=u_log, q_true=q_true, qd_true=qd_true,
                q_meas=q_meas, qd_meas=qd_meas, q_ref=q_ref)


def simulate_openloop(theta: np.ndarray, ds: dict, window: int) -> np.ndarray:
    """Replay recorded commands through a candidate model with multiple
    shooting: reset to the measured state every `window` control steps, then
    integrate forward. Returns predicted joint angles, shape (N, NJ).

    Multiple shooting keeps the identification well-posed: it stops small early
    errors from compounding over the whole record while still forcing the model
    dynamics (not just a one-step fit) to explain the data inside each window.
    """
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    set_theta(model, theta)
    data = mujoco.MjData(model)

    q_pred = np.zeros((N, NJ))
    u = ds["u"]
    for k in range(N):
        if k % window == 0:                     # re-anchor on measured state
            data.qpos[:] = ds["q_meas"][k]
            data.qvel[:] = ds["qd_meas"][k]
            mujoco.mj_forward(model, data)
        q_pred[k] = data.qpos
        data.ctrl[:] = u[k]
        for _ in range(CTRL_EVERY):
            mujoco.mj_step(model, data)
    return q_pred


def identify(ds: dict, window: int = 60):
    """Fit theta by nonlinear least squares on the shooting residual."""
    cost_history: list[float] = []

    def residual(theta_free: np.ndarray) -> np.ndarray:
        q_pred = simulate_openloop(theta_free, ds, window)
        r = (q_pred - ds["q_meas"]).ravel()
        cost_history.append(0.5 * float(r @ r))
        return r

    lb = np.array([0, 0, 0, 0, 0, 0, 0.3])
    ub = np.array([5, 5, 5, 5, 5, 5, 1.5])
    sol = least_squares(residual, THETA_INIT, bounds=(lb, ub),
                        method="trf", xtol=1e-10, ftol=1e-10, verbose=0)
    return sol.x, np.array(cost_history)


# --------------------------------------------------------------------------
# Plots
# --------------------------------------------------------------------------
def plot_excitation(ds: dict) -> str:
    fig, ax = plt.subplots(NJ, 1, figsize=(8, 6), sharex=True)
    labels = ["q1 yaw", "q2 shoulder", "q3 elbow"]
    for j in range(NJ):
        ax[j].plot(ds["t"], np.degrees(ds["q_ref"][:, j]), "k--", lw=1,
                   label="reference")
        ax[j].plot(ds["t"], np.degrees(ds["q_meas"][:, j]), color="#c0392b",
                   lw=0.8, alpha=0.8, label="measured (noisy)")
        ax[j].set_ylabel(f"{labels[j]}\n[deg]")
        ax[j].grid(alpha=0.3)
    ax[0].legend(loc="upper right", fontsize=8)
    ax[-1].set_xlabel("time [s]")
    fig.suptitle("Identification dataset: rich multi-sine excitation")
    fig.tight_layout()
    p = os.path.join(RESULTS, "01_excitation.png")
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def plot_convergence(cost: np.ndarray) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.semilogy(cost, color="#2c3e50", lw=1.5)
    ax.set_xlabel("residual evaluation")
    ax.set_ylabel("least-squares cost (log)")
    ax.set_title("Identification convergence")
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    p = os.path.join(RESULTS, "02_convergence.png")
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def plot_recovery(theta_id: np.ndarray) -> str:
    names = ["d1", "d2", "d3", "f1", "f2", "f3", "gear"]
    x = np.arange(len(names))
    w = 0.27
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(x - w, THETA_INIT, w, label="initial guess", color="#bdc3c7")
    ax.bar(x, THETA_TRUE, w, label="true", color="#27ae60")
    ax.bar(x + w, theta_id, w, label="identified", color="#2980b9")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("value  (N m s/rad, N m, or -)")
    ax.set_title("Parameter recovery")
    ax.legend()
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    p = os.path.join(RESULTS, "03_parameter_recovery.png")
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def _rmse_deg(pred, truth):
    return np.degrees(np.sqrt(np.mean((pred - truth) ** 2, axis=0)))


def plot_validation(theta_id: np.ndarray, val: dict) -> tuple[list[str], dict]:
    """Validate on held-out data with two complementary, honest views.

    Figure 04 : the identified model predicting the full 4 s open loop from a
                single initial state. Overlap with the real arm is the headline
                qualitative result. The naive model is not drawn here because
                mismatched parameters make open-loop integration diverge, which
                only compresses the axis; that case is quantified fairly below.

    Figure 05 : a bounded-horizon prediction test. Both models are re-anchored
                to the true state every 0.5 s and asked to predict the next
                0.5 s. This is a fair, finite comparison that isolates model
                error from open-loop divergence, and it is the metric reported
                as the headline number.
    """
    HORIZON = int(0.5 / CTRL_DT)                       # 0.5 s window

    q_id_full = simulate_openloop(theta_id, val, window=N)       # full open loop
    q_id_win = simulate_openloop(theta_id, val, window=HORIZON)
    q_naive_win = simulate_openloop(THETA_INIT, val, window=HORIZON)

    rmse_id = _rmse_deg(q_id_win, val["q_true"])
    rmse_naive = _rmse_deg(q_naive_win, val["q_true"])

    # ---- Figure 04: identified vs real, full open-loop prediction ----------
    fig, ax = plt.subplots(NJ, 1, figsize=(8, 6.5), sharex=True)
    labels = ["q1 yaw", "q2 shoulder", "q3 elbow"]
    for j in range(NJ):
        ax[j].plot(val["t"], np.degrees(val["q_true"][:, j]), "k", lw=1.6,
                   label="real (held-out)")
        ax[j].plot(val["t"], np.degrees(q_id_full[:, j]), color="#2980b9",
                   lw=1.2, ls="--", label="identified model")
        ax[j].set_ylabel(f"{labels[j]}\n[deg]")
        ax[j].grid(alpha=0.3)
    ax[0].legend(loc="upper right", fontsize=9)
    ax[-1].set_xlabel("time [s]")
    fig.suptitle("Held-out validation: identified model predicts 4 s open loop")
    fig.tight_layout()
    p4 = os.path.join(RESULTS, "04_validation_openloop.png")
    fig.savefig(p4, dpi=130)
    plt.close(fig)

    # ---- Figure 05: bounded-horizon RMSE, naive vs identified --------------
    x = np.arange(NJ)
    w = 0.35
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    b1 = ax.bar(x - w / 2, rmse_naive, w, label="naive model", color="#e67e22")
    b2 = ax.bar(x + w / 2, rmse_id, w, label="identified model", color="#2980b9")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("prediction RMSE over 0.5 s [deg]")
    ax.set_title("Bounded-horizon prediction error on unseen trajectory")
    ax.legend()
    ax.grid(alpha=0.3, axis="y")
    ax.bar_label(b1, fmt="%.1f", fontsize=8)
    ax.bar_label(b2, fmt="%.2f", fontsize=8)
    fig.tight_layout()
    p5 = os.path.join(RESULTS, "05_prediction_rmse.png")
    fig.savefig(p5, dpi=130)
    plt.close(fig)

    return [p4, p5], dict(rmse_id=rmse_id, rmse_naive=rmse_naive)


def render_pose(path: str) -> str | None:
    """Render one frame of the arm for the README. Returns None if headless
    GL is unavailable in the environment."""
    try:
        model = mujoco.MjModel.from_xml_path(MODEL_PATH)
        data = mujoco.MjData(model)
        data.qpos[:] = [0.5, -0.7, 1.0]
        mujoco.mj_forward(model, data)
        cam = mujoco.MjvCamera()
        cam.azimuth, cam.elevation, cam.distance = 130, -20, 1.3
        cam.lookat[:] = [0.15, 0, 0.35]
        with mujoco.Renderer(model, height=480, width=640) as r:
            r.update_scene(data, camera=cam)
            img = r.render()
        plt.imsave(path, img)
        return path
    except Exception as e:
        print(f"  (render skipped: {type(e).__name__})")
        return None


def main() -> None:
    print("Truth      theta*:", np.round(THETA_TRUE, 3))
    print("Init guess theta0:", np.round(THETA_INIT, 3))

    print("\n[1/4] collecting 'real robot' dataset ...")
    ds = collect_dataset(THETA_TRUE, seed=1)

    print("[2/4] identifying parameters (multiple shooting) ...")
    theta_id, cost = identify(ds, window=60)
    print("Identified theta :", np.round(theta_id, 3))

    err = 100 * np.abs(theta_id - THETA_TRUE) / np.abs(THETA_TRUE)
    names = ["d1", "d2", "d3", "f1", "f2", "f3", "gear"]
    print("\nparam    true    init     id      |err|%")
    for n, tt, ti, tid, e in zip(names, THETA_TRUE, THETA_INIT, theta_id, err):
        print(f"{n:5s}  {tt:6.3f}  {ti:6.3f}  {tid:6.3f}   {e:6.2f}")
    print(f"\nmean identified-parameter error: {err.mean():.2f}%")

    print("\n[3/4] validating on held-out trajectory ...")
    val = collect_dataset(THETA_TRUE, seed=99)   # different phases -> unseen

    print("[4/4] writing figures ...")
    p1 = plot_excitation(ds)
    p2 = plot_convergence(cost)
    p3 = plot_recovery(theta_id)
    val_paths, val_stats = plot_validation(theta_id, val)
    pose = render_pose(os.path.join(RESULTS, "00_arm_pose.png"))

    print("\nHeld-out prediction RMSE over 0.5 s horizon [deg]:")
    print(f"  naive model     : {np.round(val_stats['rmse_naive'], 2)}")
    print(f"  identified model: {np.round(val_stats['rmse_id'], 2)}")
    improve = (1 - val_stats['rmse_id'] / val_stats['rmse_naive']) * 100
    print(f"  RMSE reduction  : {np.round(improve, 1)} %")

    print("\nfigures:")
    for p in [pose, p1, p2, p3] + val_paths:
        if p:
            print("  ", os.path.relpath(p, HERE))

    # Persist a small summary for the README/repo.
    with open(os.path.join(RESULTS, "summary.txt"), "w") as fh:
        fh.write("System identification summary\n")
        fh.write(f"mean parameter error: {err.mean():.2f}%\n")
        fh.write(f"held-out RMSE naive [deg]: "
                 f"{np.round(val_stats['rmse_naive'],2).tolist()}\n")
        fh.write(f"held-out RMSE identified [deg]: "
                 f"{np.round(val_stats['rmse_id'],2).tolist()}\n")
        fh.write(f"RMSE reduction: {np.round(improve,1).tolist()} %\n")


if __name__ == "__main__":
    main()
