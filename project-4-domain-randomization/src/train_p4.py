"""Project 4: domain randomization over identified-parameter uncertainty.

Project 1 identified this arm's friction, damping, and motor gain to
about one percent against ground truth. Real hardware does not stay
put: lubrication state, temperature, payload, and supply voltage move
those parameters day to day. This project asks whether a policy trained
on the nominal model survives that drift, and whether randomizing the
training dynamics over the plausible parameter range buys robustness.

Two policies, identical PPO budget, hyperparameters, and architecture
(Stable-Baselines3):
  nominal : trained on the fixed nominal model
            (this is exactly project 3's shaped policy, reused)
  DR      : trained with per-episode randomization at half-width
            w = 0.30 on damping, friction, payload mass, and w/2 on
            actuator gear

Evaluation: zero-shot on unseen "real" systems drawn at shift levels
w_eval in {0, 0.15, 0.30, 0.45, 0.60}. Levels above 0.30 are outside
the DR training range, so the right-hand side of the curve measures
extrapolation, not memorized robustness. 24 frozen systems x 12 fixed
targets per level, identical (system, target, start pose) triples for
both policies, deterministic actions.

Outputs: results/p4_transfer.npz, results/p4_dr_curve.npz,
results/policy_dr.zip, results/summary.txt.
"""

from __future__ import annotations
import numpy as np
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
P3_SRC = HERE.parent.parent / "project-3-rl-reach" / "src"
P3_RES = HERE.parent.parent / "project-3-rl-reach" / "results"
sys.path.insert(0, str(P3_SRC))

from reach_env import ReachEnv, EP_LEN                       # noqa: E402
from train_p3 import make_eval_targets, evaluate             # noqa: E402

from stable_baselines3 import PPO                            # noqa: E402
from stable_baselines3.common.env_util import make_vec_env   # noqa: E402

RES = HERE.parent / "results"
RES.mkdir(exist_ok=True)

W_TRAIN = 0.30
W_EVAL = [0.0, 0.15, 0.30, 0.45, 0.60]
N_SYS = 24
N_TGT = 12
TOTAL_STEPS = 600_000
CHUNK = 24_576


class DREnv(ReachEnv):
    """Reach env that redraws its dynamics parameters every episode."""

    def __init__(self, w: float, seed: int | None = None):
        super().__init__("shaped", seed=seed)
        self.w = w
        self._dr_rng = np.random.default_rng(None if seed is None else seed + 5000)

    def reset(self, *, seed=None, options=None):
        self.randomize(self._dr_rng, self.w)
        return super().reset(seed=seed, options=options)


def transfer_eval(model, w: float, targets, seed0: int = 40_000) -> float:
    """Success rate on N_SYS frozen systems x N_TGT targets at shift w.

    The (system, target, start pose) triples are fully seeded, so the
    nominal and DR policies see byte-identical evaluation conditions.
    """
    wins = 0
    for s_i in range(N_SYS):
        env = ReachEnv("shaped", seed=1)
        env.randomize(np.random.default_rng(seed0 + s_i * 13), w)
        for t_i, tgt in enumerate(targets):
            obs, _ = env.reset(seed=seed0 + s_i * 977 + t_i,
                               options={"target": tgt})
            for _ in range(EP_LEN):
                a, _ = model.predict(obs, deterministic=True)
                obs, _, _, trunc, info = env.step(a)
                if trunc:
                    wins += int(info["success"])
                    break
    return wins / (N_SYS * N_TGT)


if __name__ == "__main__":
    targets12 = make_eval_targets(N_TGT, seed=31)
    targets40 = make_eval_targets()

    # ---- train the DR policy ------------------------------------------
    venv = make_vec_env(lambda: DREnv(W_TRAIN), n_envs=8, seed=0)
    model = PPO("MlpPolicy", venv, n_steps=256, batch_size=128, seed=0,
                verbose=0, policy_kwargs=dict(net_arch=[64, 64]))
    steps_ax, succ_ax, med_ax = [], [], []
    while model.num_timesteps < TOTAL_STEPS:
        model.learn(total_timesteps=CHUNK, reset_num_timesteps=False)
        sr, md = evaluate(model, targets40)     # nominal-dynamics eval
        steps_ax.append(model.num_timesteps)
        succ_ax.append(sr)
        med_ax.append(md)
        print(f"[DR w={W_TRAIN}] {model.num_timesteps:7d} steps  "
              f"success {sr:5.1%}  median hold {md:7.1f} mm", flush=True)
    model.save(RES / "policy_dr")
    np.savez(RES / "p4_dr_curve.npz", steps=np.array(steps_ax),
             succ=np.array(succ_ax), med_mm=np.array(med_ax))

    # ---- zero-shot transfer sweep -------------------------------------
    nominal = PPO.load(P3_RES / "policy_shaped")
    rows = {"w": np.array(W_EVAL), "nominal": [], "dr": []}
    for w in W_EVAL:
        sn = transfer_eval(nominal, w, targets12)
        sd = transfer_eval(model, w, targets12)
        rows["nominal"].append(sn)
        rows["dr"].append(sd)
        print(f"w={w:.2f}  nominal {sn:5.1%}   DR {sd:5.1%}", flush=True)
    rows["nominal"] = np.array(rows["nominal"])
    rows["dr"] = np.array(rows["dr"])
    np.savez(RES / "p4_transfer.npz", **rows)

    with open(RES / "summary.txt", "w") as fh:
        fh.write("Project 4 summary: domain randomization transfer\n")
        fh.write(f"DR training half-width: {W_TRAIN}\n")
        fh.write(f"eval grid: {N_SYS} systems x {N_TGT} targets per level\n")
        for i, w in enumerate(W_EVAL):
            tag = " (extrapolation)" if w > W_TRAIN else ""
            fh.write(f"w={w:.2f}{tag}: nominal {rows['nominal'][i]:.1%}, "
                     f"DR {rows['dr'][i]:.1%}\n")
        fh.write(f"nominal-dynamics eval of DR policy at end of training: "
                 f"{succ_ax[-1]:.1%}, median hold {med_ax[-1]:.1f} mm\n")
    print(open(RES / "summary.txt").read())
