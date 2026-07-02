"""A Gymnasium reach environment on the portfolio's 3-DOF arm.

Design notes, in the order a reviewer would ask about them.

Observation (12,): joint positions (3), joint velocities scaled by 0.1
(3), target position (3), fingertip-to-target vector (3). The delta is
technically redundant with the other two blocks but flattens the
credit-assignment problem for a small MLP; that is a deliberate
observation-design choice, not an accident.

Action (3,): joint torques in [-6, 6] N m, the same peak torque as the
thermal actuator in project 2. The environment clips; the policy does
not need to know the limits.

Reward, two modes:
  shaped: r = -d + 8 (d_prev - d) - 1e-3 |a|^2 + [d < tol]
          distance potential, a potential-based progress term that gives
          one-step credit for approach (policy-invariant shaping), a small
          torque penalty so the policy does not learn to buzz the
          actuators, and a hold bonus.
  sparse: r = [d < tol]
          nothing until the tip is already at the target. This is the
          exploration problem the ablation in train_p3.py measures.

Success: mean fingertip distance over the final 20 control steps below
tol (2.5 cm). Holding, not grazing.

Targets are sampled by drawing a random joint configuration inside the
limits and running forward kinematics, so every target is reachable by
construction. A scratch MjData does the FK; the live one is untouched.

Domain randomization (used by project 4): each env owns its own MjModel,
and `randomize(rng, w)` rescales joint damping, dry friction, actuator
gear, and payload mass by multiplicative factors of half-width w around
the nominal values. w = 0 restores nominal exactly.
"""

from __future__ import annotations
import numpy as np
import mujoco
import gymnasium as gym
from gymnasium import spaces
from pathlib import Path

XML = Path(__file__).resolve().parent.parent / "models" / "reach_arm.xml"

EP_LEN = 150          # control steps per episode
FRAME_SKIP = 4        # physics steps per control step -> 20 ms control dt
TOL = 0.025           # success tolerance [m]
HOLD_WINDOW = 20      # steps at episode end that must average < TOL


class ReachEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, reward_mode: str = "shaped", seed: int | None = None):
        assert reward_mode in ("shaped", "sparse")
        self.reward_mode = reward_mode
        self.model = mujoco.MjModel.from_xml_path(str(XML))
        self.data = mujoco.MjData(self.model)
        self._fk = mujoco.MjData(self.model)          # scratch for target FK
        self.rng = np.random.default_rng(seed)

        self._tip = self.model.site("fingertip").id
        self._target_body = self.model.body("target").id
        self._payload_body = self.model.body("payload").id

        # nominal parameter vectors, kept so randomize() is exact and repeatable
        self._nom = dict(
            damping=self.model.dof_damping.copy(),
            friction=self.model.dof_frictionloss.copy(),
            gear=self.model.actuator_gear.copy(),
            mass=float(self.model.body_mass[self._payload_body]),
        )

        self.observation_space = spaces.Box(-np.inf, np.inf, (12,), np.float64)
        self.action_space = spaces.Box(-6.0, 6.0, (3,), np.float64)
        self.target = np.zeros(3)
        self._t = 0
        self._dist_tail: list[float] = []

    # ---------------------------------------------------------------- helpers
    def _sample_target(self) -> np.ndarray:
        """Random reachable target via FK on a random joint configuration.

        Constraints make every target holdable, not merely touchable:
        shoulder is biased upward (extended-and-level poses near the
        torque budget are excluded), and targets below z = 0.10 m are
        rejected so nothing asks the arm to hold against the floor.
        """
        for _ in range(100):
            q = np.array([
                self.rng.uniform(-1.8, 1.8),      # yaw
                self.rng.uniform(-0.25, 0.95),    # shoulder, biased up
                self.rng.uniform(-1.9, 1.9),      # elbow
            ])
            self._fk.qpos[:] = q
            self._fk.qvel[:] = 0
            mujoco.mj_forward(self.model, self._fk)
            p = self._fk.site_xpos[self._tip].copy()
            if p[2] >= 0.10:
                self._last_target_q = q      # kept for scripted baselines
                return p
        self._last_target_q = q
        return p  # pragma: no cover - sampler is far from this in practice

    def _dist(self) -> float:
        return float(np.linalg.norm(self.data.site_xpos[self._tip] - self.target))

    def _obs(self) -> np.ndarray:
        tip = self.data.site_xpos[self._tip]
        return np.concatenate([
            self.data.qpos, 0.1 * self.data.qvel, self.target, self.target - tip,
        ])

    # ------------------------------------------------------- domain random.
    def randomize(self, rng: np.random.Generator, w: float) -> dict:
        """Rescale dynamics parameters by U(1-w, 1+w); gear by half that
        width (drives are usually better characterized than joints).
        Returns the factors used, for logging."""
        f = dict(
            damping=rng.uniform(1 - w, 1 + w, self._nom["damping"].shape),
            friction=rng.uniform(1 - w, 1 + w, self._nom["friction"].shape),
            gear=rng.uniform(1 - 0.5 * w, 1 + 0.5 * w),
            mass=rng.uniform(1 - w, 1 + w),
        )
        self.model.dof_damping[:] = self._nom["damping"] * f["damping"]
        self.model.dof_frictionloss[:] = self._nom["friction"] * f["friction"]
        self.model.actuator_gear[:] = self._nom["gear"] * f["gear"]
        self.model.body_mass[self._payload_body] = self._nom["mass"] * f["mass"]
        return f

    # ------------------------------------------------------------ gym API
    def reset(self, *, seed=None, options=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[:] = np.array([0.0, 0.4, -0.6]) + self.rng.uniform(-0.15, 0.15, 3)
        self.target = (options or {}).get("target", self._sample_target())
        self.model.body_pos[self._target_body] = self.target   # visual only
        mujoco.mj_forward(self.model, self.data)
        self._t = 0
        self._dist_tail = []
        self._d_prev = self._dist()
        return self._obs(), {}

    def step(self, action):
        a = np.clip(action, -6.0, 6.0)
        self.data.ctrl[:] = a
        for _ in range(FRAME_SKIP):
            mujoco.mj_step(self.model, self.data)
        self._t += 1
        d = self._dist()
        self._dist_tail.append(d)

        if self.reward_mode == "shaped":
            # Distance potential plus a progress term. The progress term is
            # potential-based shaping (Ng et al. 1999) with Phi = -8 d, so it
            # cannot change the optimal policy, but it converts "get closer"
            # from a 15-step GAE inference into one-step credit. Without it,
            # both this implementation and reference SB3 PPO sit at 0%
            # success for a quarter-million steps on this task.
            r = (-d + 8.0 * (self._d_prev - d)
                 - 1e-3 * float(a @ a) + (1.0 if d < TOL else 0.0))
        else:
            r = 1.0 if d < TOL else 0.0
        self._d_prev = d

        terminated = False
        truncated = self._t >= EP_LEN
        info = {}
        if truncated:
            tail = np.mean(self._dist_tail[-HOLD_WINDOW:])
            info["success"] = bool(tail < TOL)
            info["final_dist"] = float(tail)
        return self._obs(), r, terminated, truncated, info
