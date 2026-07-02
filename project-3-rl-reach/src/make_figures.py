"""Figures for project 3. Filmstrip renders the actual trained policy
via forward kinematics (no GL in this environment); the curves figure
reads results/p3_curves.npz written by the training scripts."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from reach_env import ReachEnv, EP_LEN

ROOT = HERE.parent
RES = ROOT / "results"
SITE = ROOT.parent / "site" / "assets"

BG, FG, GRID = "#0e1626", "#dbe4f0", "#22304a"
TEAL, ORANGE = "#4FD1C5", "#FF8A5B"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.5,
})


def filmstrip():
    from stable_baselines3 import PPO
    import mujoco
    model = PPO.load(RES / "policy_shaped")
    env = ReachEnv("shaped", seed=42)
    tgt = np.array([0.35, 0.30, 0.45])
    obs, _ = env.reset(seed=42, options={"target": tgt})
    jids = [env.model.joint(n).id for n in ("shoulder", "elbow")]
    frames, snaps = [0, 8, 18, 30, 60, 149], {}
    base = np.array([0.0, 0.0, 0.22])
    for t in range(EP_LEN):
        if t in frames:
            pts = [base] + [env.data.xanchor[j].copy() for j in jids] \
                  + [env.data.site_xpos[env._tip].copy()]
            snaps[t] = (np.array(pts), float(np.linalg.norm(
                env.data.site_xpos[env._tip] - tgt)))
        a, _ = model.predict(obs, deterministic=True)
        obs, _, _, trunc, info = env.step(a)
    fig = plt.figure(figsize=(10.8, 2.6), dpi=150)
    for i, t in enumerate(frames):
        ax = fig.add_subplot(1, 6, i + 1, projection="3d")
        pts, d = snaps[t]
        ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], "-o", color=TEAL,
                lw=2.5, ms=3.5)
        ax.scatter(*tgt, color=ORANGE, s=45, marker="*")
        ax.set_xlim(-0.55, 0.55); ax.set_ylim(-0.55, 0.55)
        ax.set_zlim(0, 0.8)
        ax.set_axis_off()
        ax.set_facecolor(BG)
        ax.view_init(elev=18, azim=-50)
        ax.set_title(f"t = {t * 0.02:.2f} s\nd = {d * 1000:.0f} mm",
                     fontsize=8.5, pad=-2)
    fig.suptitle("Trained policy, one rollout: reach and hold inside 25 mm",
                 fontsize=11, y=1.04)
    fig.tight_layout()
    for p in (RES / "p3-rollout.png", SITE / "p3-rollout.png"):
        fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print(f"filmstrip written (final hold {snaps[149][1]*1000:.1f} mm)")


def curves():
    f = RES / "p3_curves.npz"
    if not f.exists():
        print("p3_curves.npz not present yet; skipping curves")
        return
    d = np.load(f)
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.8), dpi=150)
    for mode, c in (("shaped", TEAL), ("sparse", ORANGE)):
        axes[0].plot(d[f"{mode}_steps"] / 1e3, d[f"{mode}_succ"] * 100,
                     color=c, lw=2.2, label=mode)
        axes[1].plot(d[f"{mode}_steps"] / 1e3, d[f"{mode}_med_mm"],
                     color=c, lw=2.2, label=mode)
    axes[0].set_xlabel("training steps (thousands)")
    axes[0].set_ylabel("eval success rate (%)")
    axes[0].set_ylim(-3, 100); axes[0].legend(framealpha=0.15)
    axes[0].set_title("Success on 40 fixed targets")
    axes[1].set_xlabel("training steps (thousands)")
    axes[1].set_ylabel("median hold distance (mm)")
    axes[1].set_yscale("log")
    axes[1].axhline(25, color=FG, lw=1, ls="--", alpha=0.5)
    axes[1].text(15, 28, "25 mm tolerance", fontsize=8.5, alpha=0.8)
    axes[1].legend(framealpha=0.15)
    axes[1].set_title("How close it holds")
    fig.suptitle("Same task, same budget, same PPO; only the reward differs",
                 y=1.02)
    fig.tight_layout()
    for p in (RES / "p3-curves.png", SITE / "p3-curves.png"):
        fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print("curves written")


if __name__ == "__main__":
    filmstrip()
    curves()
