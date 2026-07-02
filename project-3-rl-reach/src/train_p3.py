"""Project 3 trainer: the reward-shaping ablation.

Two PPO runs (Stable-Baselines3, identical budgets, seeds, and
hyperparameters). The only difference is the reward function: shaped
(distance + potential-based progress + hold bonus + torque penalty)
versus sparse (paid only inside the 2.5 cm tolerance). Evaluation is
zero-noise on 40 fixed targets every ~25k steps, so the curves measure
the policy, not the sampling.

Training is deliberately the boring part. A from-scratch PPO was
written, instrumented, and retired during development: on this task its
policy gradient sat below the trajectory-variance noise floor
(corr(advantage, action noise) ~ 0.02-0.07 with sign flips between
batches), and the honest comparison against a reference implementation
is what localized the remaining problems to the environment, where they
belonged. The interesting engineering lives in reach_env.py and the
write-up.

Outputs: results/p3_curves.npz, results/summary.txt,
results/policy_shaped.zip (reused by project 4 as the no-randomization
baseline).
"""

from __future__ import annotations
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reach_env import ReachEnv, EP_LEN

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
RES.mkdir(exist_ok=True)

TOTAL_STEPS = 600_000
CHUNK = 24_576            # eval cadence: 12 chunks of 8 envs x 256 x (?) -> ~24 evals
N_EVAL = 40


def make_eval_targets(n=N_EVAL, seed=7):
    env = ReachEnv(seed=seed)
    return [env._sample_target() for _ in range(n)]


def evaluate(model, targets, reward_mode="shaped", env_factory=None, seed=999):
    """Deterministic policy on fixed targets; returns (success, median mm)."""
    env = env_factory() if env_factory else ReachEnv(reward_mode, seed=seed)
    wins, dists = 0, []
    for k, tgt in enumerate(targets):
        obs, _ = env.reset(seed=seed + k, options={"target": tgt})
        for _ in range(EP_LEN):
            a, _ = model.predict(obs, deterministic=True)
            obs, _, _, trunc, info = env.step(a)
            if trunc:
                wins += int(info["success"])
                dists.append(info["final_dist"])
                break
    return wins / len(targets), float(np.median(dists) * 1000)


def train(reward_mode: str, seed: int = 0):
    venv = make_vec_env(lambda: ReachEnv(reward_mode), n_envs=8, seed=seed)
    model = PPO("MlpPolicy", venv, n_steps=256, batch_size=128, seed=seed,
                verbose=0, policy_kwargs=dict(net_arch=[64, 64]))
    targets = make_eval_targets()
    steps_ax, succ_ax, med_ax = [], [], []
    while model.num_timesteps < TOTAL_STEPS:
        model.learn(total_timesteps=CHUNK, reset_num_timesteps=False)
        sr, md = evaluate(model, targets, reward_mode)
        steps_ax.append(model.num_timesteps)
        succ_ax.append(sr)
        med_ax.append(md)
        print(f"[{reward_mode:6s}] {model.num_timesteps:7d} steps  "
              f"success {sr:5.1%}  median hold {md:7.1f} mm", flush=True)
    return model, np.array(steps_ax), np.array(succ_ax), np.array(med_ax)


if __name__ == "__main__":
    out = {}
    for mode in ("shaped", "sparse"):
        model, s, sr, md = train(mode)
        out[f"{mode}_steps"] = s
        out[f"{mode}_succ"] = sr
        out[f"{mode}_med_mm"] = md
        if mode == "shaped":
            model.save(RES / "policy_shaped")
    np.savez(RES / "p3_curves.npz", **out)

    with open(RES / "summary.txt", "w") as fh:
        fh.write("Project 3 summary: reward shaping ablation\n")
        fh.write(f"training budget per run: {TOTAL_STEPS} steps\n")
        fh.write(f"final eval success, shaped: {out['shaped_succ'][-1]:.1%}\n")
        fh.write(f"final median hold, shaped: {out['shaped_med_mm'][-1]:.1f} mm\n")
        fh.write(f"best eval success, shaped: {out['shaped_succ'].max():.1%}\n")
        fh.write(f"final eval success, sparse: {out['sparse_succ'][-1]:.1%}\n")
        fh.write(f"final median hold, sparse: {out['sparse_med_mm'][-1]:.1f} mm\n")
    print(open(RES / "summary.txt").read())
