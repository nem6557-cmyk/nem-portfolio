# Project 3: RL reach environment, built and debugged from first principles

A gymnasium environment around the project 1/2 arm (3-DOF, gravity,
identified friction and damping, 6 Nm torque budget), a PPO reward
shaping ablation, and the debugging record that is the real product:

- **MJCF unit bug.** Joint ranges written as radians compiled under the
  default degree parser, clamping the arm to a 2.6 degree cone. Found
  with a scripted PD baseline and `qfrc_constraint` inspection, not
  learning curves. Fix: `<compiler angle="radian"/>`.
- **Gravity exploration trap.** Holding the arm up needs +2 to +4.3 Nm
  at the shoulder; zero-mean Gaussian exploration never samples it, so
  every rollout collapses to the fallen pose and returns carry no
  action information (measured corr(advantage, action noise) 0.02-0.07
  with sign flips, for a from-scratch PPO and reference SB3 alike).
  Fix: model-based gravity compensation (`gravcomp="1"`), what real
  impedance-controlled arms do; the policy learns residual torque.
- **Scripted baselines as instruments.** Plain PD: 71 mm gravity droop
  (tau/kp, as predicted). PD + gravity feedforward: 67%, 7.2 mm.
  Plain PD under gravcomp: 72%, 9.3 mm. The env is proven learnable
  before RL gets blamed.

The ablation: identical PPO budget (600k steps), seeds, and network;
only the reward differs. Shaped (distance + potential-based progress +
hold bonus) reaches **70% success, 19.2 mm median hold**; sparse never
finds the tolerance region once.

```
pip install mujoco gymnasium stable-baselines3 numpy matplotlib
python src/train_p3.py         # both ablation arms
python src/make_figures.py     # curves + rollout filmstrip
```

Files: `models/reach_arm.xml` (annotated with both bugs),
`src/reach_env.py` (env + randomization hook used by project 4),
`src/train_p3.py`, `src/finish_p3.py` (resume helper),
`src/make_figures.py`.
