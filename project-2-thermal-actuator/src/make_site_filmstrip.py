"""Dark-theme filmstrip of the thermal sag run for the site.

Re-runs the exact deterministic control loop from run_thermal_demo.py
(constants mirrored below) and draws the captured poses by forward
kinematics, so the strip needs no GL and matches the site theme. The
thermal-blind hold is ghosted in each frame for the A/B read.
"""
import os
import sys
import numpy as np
import mujoco
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermal_actuator import ThermalActuator, ThermalActuatorParams

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(HERE, "models", "arm_thermal.xml")
SITE = os.path.join(os.path.dirname(HERE), "site", "assets")

# mirrored from run_thermal_demo.py
DURATION, PHYS_DT, CTRL_EVERY = 300.0, 0.001, 5
CTRL_DT = PHYS_DT * CTRL_EVERY
N = int(DURATION / CTRL_DT)
Q_TARGET = np.array([0.0, 0.0, 0.0])
KP = np.array([60.0, 60.0, 40.0])
KD = np.array([6.0, 6.0, 4.0])
SHOULDER = 1
FRAME_TIMES = [0.0, 45.0, 75.0, 130.0, 300.0]

BG, FG, GRID = "#0e1626", "#dbe4f0", "#22304a"
TEAL, ORANGE, FAINT = "#4FD1C5", "#FF8A5B", "#57678A"


def simulate():
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)
    acts = [ThermalActuator(ThermalActuatorParams()) for _ in range(model.nu)]
    data.qpos[:] = Q_TARGET
    mujoco.mj_forward(model, data)
    snaps, fi = [], 0
    for k in range(N):
        t = k * CTRL_DT
        if fi < len(FRAME_TIMES) and t >= FRAME_TIMES[fi]:
            snaps.append((FRAME_TIMES[fi], data.qpos.copy(),
                          acts[SHOULDER].Tw, np.degrees(data.qpos[SHOULDER])))
            fi += 1
        grav = data.qfrc_bias.copy()
        tau_des = grav + KP * (Q_TARGET - data.qpos) - KD * data.qvel
        tau_avail = np.array([a.available_torque() for a in acts])
        data.ctrl[:] = np.clip(tau_des, -tau_avail, tau_avail)
        for _ in range(CTRL_EVERY):
            mujoco.mj_step(model, data)
        for j, a in enumerate(acts):
            a.step(abs(float(data.ctrl[j])), CTRL_DT)
    snaps.append((DURATION, data.qpos.copy(),
                  acts[SHOULDER].Tw, np.degrees(data.qpos[SHOULDER])))
    return model, snaps


def pose_points(model, q):
    d = mujoco.MjData(model)
    d.qpos[:] = q
    mujoco.mj_forward(model, d)
    j2 = model.joint("q2").id
    j3 = model.joint("q3").id
    tip = model.site("tip").id
    pts = np.array([d.xanchor[j2], d.xanchor[j3], d.site_xpos[tip]])
    return pts[:, [0, 2]]                      # side view: x-z plane


def main():
    model, snaps = simulate()
    seen, frames = set(), []
    for s in snaps:                            # dedupe frame times
        if s[0] not in seen:
            seen.add(s[0])
            frames.append(s)
    frames = frames[:5]
    print("captured:", [(f"{t:.0f}s", f"Tw {Tw:.0f}C", f"sag {-sag:.0f} deg")
                        for t, _, Tw, sag in frames])

    ghost = pose_points(model, Q_TARGET)
    fig, axes = plt.subplots(1, 5, figsize=(10.8, 2.55), dpi=150)
    fig.patch.set_facecolor(BG)
    for ax, (t, q, Tw, sag) in zip(axes, frames):
        ax.set_facecolor(BG)
        ax.plot(ghost[:, 0], ghost[:, 1], "-o", color=FAINT, lw=2.0,
                ms=3, alpha=0.5, zorder=1)
        pts = pose_points(model, q)
        ax.plot(pts[:, 0], pts[:, 1], "-o", color=TEAL, lw=2.6, ms=4, zorder=3)
        ax.plot(pts[-1, 0], pts[-1, 1], "o", color=ORANGE, ms=7, zorder=4)
        ax.plot([0, 0], [0, ghost[0, 1]], color=FAINT, lw=3.2,
                solid_capstyle="round", zorder=2)
        ax.axhline(ghost[0, 1], color=FG, lw=0.7, ls="--", alpha=0.28)
        ax.set_xlim(-0.12, 0.75)
        ax.set_ylim(-0.42, 0.48)
        ax.set_aspect("equal")
        ax.axis("off")
        sag_disp = max(0.0, -sag)
        ax.set_title(f"t = {t:.0f} s\nTw = {Tw:.0f} C   sag = {sag_disp:.0f}\u00b0",
                     fontsize=8.4, color=FG, pad=4)
    fig.suptitle("Thermal run over time; thermal-blind hold ghosted in slate",
                 fontsize=10.5, color=FG, y=1.05)
    fig.tight_layout()
    out = os.path.join(SITE, "p2-filmstrip.png")
    fig.savefig(out, bbox_inches="tight", facecolor=BG)
    print("wrote", out)
    from PIL import Image
    print("dimensions:", Image.open(out).size)


if __name__ == "__main__":
    main()
