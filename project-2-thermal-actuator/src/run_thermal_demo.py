"""
run_thermal_demo.py
==================
Couple the two-node thermal actuator model to the MuJoCo arm and show the
sim-to-real gap it captures.

Scenario: the arm is commanded to hold a fully extended horizontal pose with a
0.5 kg payload. The controller is a correct gravity-compensating PD law, the
same in both runs. The only difference is the actuator:

  * naive       : peak torque is always available (the usual simulator
                  assumption).
  * thermal     : available torque derates as the winding heats under the
                  sustained holding current.

The naive arm holds horizontal forever. The thermal arm holds, heats, and then
sags to a drooped equilibrium where the reduced gravity torque matches the
derated torque the hot motor can still deliver. Same controller, same commands,
different outcome, which is exactly what bites when a sim-tuned hold is deployed
to hardware.

Run: MUJOCO_GL=egl python src/run_thermal_demo.py
"""

from __future__ import annotations

import os
import numpy as np
import mujoco

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from thermal_actuator import ThermalActuator, ThermalActuatorParams

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(HERE, "models", "arm_thermal.xml")
RESULTS = os.path.join(HERE, "results")
os.makedirs(RESULTS, exist_ok=True)

DURATION = 300.0             # s
PHYS_DT = 0.001
CTRL_EVERY = 5
CTRL_DT = PHYS_DT * CTRL_EVERY
N = int(DURATION / CTRL_DT)

Q_TARGET = np.array([0.0, 0.0, 0.0])     # yaw, shoulder, elbow -> horizontal
KP = np.array([60.0, 60.0, 40.0])
KD = np.array([6.0, 6.0, 4.0])
SHOULDER = 1                              # joint index of interest
FRAME_TIMES = [0.0, 45.0, 75.0, 130.0, 300.0]   # s, for the filmstrip


def run(thermal: bool, capture_frames: bool = False):
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)
    nu = model.nu
    acts = [ThermalActuator(ThermalActuatorParams()) for _ in range(nu)]
    tau_peak = acts[0].p.tau_peak

    # Start exactly at the horizontal target.
    data.qpos[:] = Q_TARGET
    mujoco.mj_forward(model, data)

    log = {k: np.zeros(N) for k in
           ["t", "Tw", "Tc", "tau_des", "tau_avail", "tau_app", "q2", "grav"]}

    renderer = None
    frames = []
    frame_idx = 0
    if capture_frames:
        cam = mujoco.MjvCamera()
        cam.azimuth, cam.elevation, cam.distance = 90, -8, 1.6
        cam.lookat[:] = [0.35, 0, 0.15]
        try:
            renderer = mujoco.Renderer(model, height=300, width=440)
        except Exception as e:
            print(f"  (frame capture skipped: {type(e).__name__})")
            renderer = None

    for k in range(N):
        q = data.qpos.copy()
        qd = data.qvel.copy()
        grav = data.qfrc_bias.copy()                 # gravity + Coriolis load
        tau_des = grav + KP * (Q_TARGET - q) - KD * qd

        tau_avail = np.array([a.available_torque() if thermal else tau_peak
                              for a in acts])
        tau_app = np.clip(tau_des, -tau_avail, tau_avail)
        data.ctrl[:] = tau_app                       # gear = 1 -> applied = ctrl

        log["t"][k] = k * CTRL_DT
        log["Tw"][k] = acts[SHOULDER].Tw
        log["Tc"][k] = acts[SHOULDER].Tc
        log["tau_des"][k] = tau_des[SHOULDER]
        log["tau_avail"][k] = tau_avail[SHOULDER]
        log["tau_app"][k] = tau_app[SHOULDER]
        log["q2"][k] = np.degrees(q[SHOULDER])
        log["grav"][k] = grav[SHOULDER]

        for _ in range(CTRL_EVERY):
            mujoco.mj_step(model, data)
        if thermal:
            for j, a in enumerate(acts):
                a.step(abs(tau_app[j]), CTRL_DT)

        if (renderer is not None and frame_idx < len(FRAME_TIMES)
                and log["t"][k] >= FRAME_TIMES[frame_idx]):
            renderer.update_scene(data, camera=cam)
            frames.append((FRAME_TIMES[frame_idx], renderer.render().copy()))
            frame_idx += 1

    if renderer is not None:
        renderer.close()
    return log, frames


def plot_main(naive, thermal) -> str:
    p = ThermalActuator(ThermalActuatorParams()).p
    fig, ax = plt.subplots(3, 1, figsize=(8.5, 9), sharex=True)

    # (a) temperatures
    ax[0].plot(thermal["t"], thermal["Tw"], color="#c0392b", lw=1.8,
               label="winding $T_w$")
    ax[0].plot(thermal["t"], thermal["Tc"], color="#e67e22", lw=1.4,
               label="case $T_c$")
    ax[0].axhline(p.T_derate, color="gray", ls="--", lw=1,
                  label="derate onset")
    ax[0].axhline(p.T_max, color="k", ls=":", lw=1, label="full derate")
    ax[0].set_ylabel("temperature [degC]")
    ax[0].legend(loc="lower right", fontsize=8, ncol=2)
    ax[0].grid(alpha=0.3)
    ax[0].set_title("Shoulder motor thermal state")

    # (b) torque
    ax[1].plot(thermal["t"], thermal["grav"], color="#7f8c8d", lw=1.3,
               label="gravity load (required)")
    ax[1].plot(thermal["t"], thermal["tau_avail"], color="#2980b9", lw=1.6,
               label="available (derated)")
    ax[1].plot(thermal["t"], thermal["tau_app"], color="#27ae60", lw=1.2,
               ls="--", label="applied")
    ax[1].set_ylabel("shoulder torque [N m]")
    ax[1].legend(loc="upper right", fontsize=8)
    ax[1].grid(alpha=0.3)
    ax[1].set_title("Torque budget: demand outruns what the hot motor delivers")

    # (c) resulting joint angle, naive vs thermal
    ax[2].plot(naive["t"], naive["q2"], color="#2c3e50", lw=1.6,
               label="naive actuator (holds)")
    ax[2].plot(thermal["t"], thermal["q2"], color="#c0392b", lw=1.6,
               label="thermal actuator (sags)")
    ax[2].axhline(0, color="gray", ls="--", lw=0.8)
    ax[2].set_ylabel("shoulder angle [deg]\n(0 = horizontal)")
    ax[2].set_xlabel("time [s]")
    ax[2].legend(loc="lower left", fontsize=9)
    ax[2].grid(alpha=0.3)
    ax[2].set_title("Same controller, same commands, different outcome")

    fig.tight_layout()
    out = os.path.join(RESULTS, "01_thermal_derating.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def plot_rating() -> str:
    act = ThermalActuator(ThermalActuatorParams())
    taus = np.linspace(1.0, 5.5, 200)
    Tss = np.array([act.steady_state_winding_temp(t) for t in taus])
    cont = act.continuous_torque_limit()

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(taus, Tss, color="#2c3e50", lw=2)
    ax.axhline(act.p.T_derate, color="gray", ls="--", lw=1, label="derate onset")
    ax.axhline(act.p.T_max, color="k", ls=":", lw=1, label="insulation limit")
    ax.axvline(cont, color="#2980b9", ls="-.", lw=1.2,
               label=f"continuous rating {cont:.2f} N m")
    ax.axvline(4.0, color="#c0392b", ls="-", lw=1.2,
               label="horizontal hold demand ~4 N m")
    ax.fill_between(taus, act.p.T_max, Tss, where=Tss > act.p.T_max,
                    color="#c0392b", alpha=0.12)
    ax.set_xlabel("sustained torque [N m]")
    ax.set_ylabel("steady-state winding temp [degC]")
    ax.set_title("Continuous torque rating from the thermal network")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    ax.set_ylim(20, 200)
    fig.tight_layout()
    out = os.path.join(RESULTS, "02_torque_rating.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def plot_filmstrip(frames) -> str | None:
    if not frames:
        return None
    n = len(frames)
    fig, ax = plt.subplots(1, n, figsize=(2.6 * n, 2.6))
    if n == 1:
        ax = [ax]
    for a, (t, img) in zip(ax, frames):
        a.imshow(img)
        a.set_title(f"t = {t:.0f} s", fontsize=10)
        a.axis("off")
    fig.suptitle("Thermal-aware run: shoulder sags as the winding heats and "
                 "torque derates", fontsize=11)
    fig.tight_layout()
    out = os.path.join(RESULTS, "03_sag_filmstrip.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def main() -> None:
    act = ThermalActuator(ThermalActuatorParams())
    t_fast, t_slow = act.time_constants()
    print("Actuator: peak {:.1f} N m, continuous {:.2f} N m, "
          "tau_w {:.1f}s, tau_c {:.1f}s".format(
              act.p.tau_peak, act.continuous_torque_limit(), t_fast, t_slow))

    print("running naive actuator ...")
    naive, _ = run(thermal=False)
    print("running thermal actuator ...")
    thermal, frames = run(thermal=True, capture_frames=True)

    final_sag = thermal["q2"][-1]
    peak_Tw = thermal["Tw"].max()
    print(f"naive final shoulder angle  : {naive['q2'][-1]:6.2f} deg")
    print(f"thermal final shoulder angle: {final_sag:6.2f} deg  "
          f"(sag of {abs(final_sag):.1f} deg)")
    print(f"peak winding temperature    : {peak_Tw:6.1f} degC")

    p1 = plot_main(naive, thermal)
    p2 = plot_rating()
    p3 = plot_filmstrip(frames)

    print("\nfigures:")
    for p in [p1, p3, p2]:
        if p:
            print("  ", os.path.relpath(p, HERE))

    with open(os.path.join(RESULTS, "summary.txt"), "w") as fh:
        fh.write("Thermal actuator demo summary\n")
        fh.write(f"continuous torque rating: "
                 f"{act.continuous_torque_limit():.2f} N m\n")
        fh.write(f"horizontal hold demand: ~4 N m (exceeds rating)\n")
        fh.write(f"peak winding temp: {peak_Tw:.1f} degC\n")
        fh.write(f"naive final shoulder angle: {naive['q2'][-1]:.2f} deg\n")
        fh.write(f"thermal final shoulder angle: {final_sag:.2f} deg\n")


if __name__ == "__main__":
    main()
