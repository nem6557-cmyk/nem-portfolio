# Project 4: domain randomization, measured honestly

Does the project 3 policy need domain randomization over the parameter
uncertainty project 1 identified? A controlled experiment answers it:

- Two policies, identical PPO budget/seeds/network. Nominal = project
  3's shaped policy. DR = trained with damping, friction, payload mass
  ~ U(0.7, 1.3) x nominal and gear ~ U(0.85, 1.15), redrawn per episode.
- Zero-shot transfer at shift levels w in {0, .15, .30, .45, .60}
  (above .30 is extrapolation past the DR range): 24 frozen unseen
  systems x 12 targets per level, identical seeded conditions for both
  policies, 1440 episodes per policy.

**Result: DR bought nothing here.** Nominal degrades 66.7% -> 61.1%
across the full sweep; DR pays an 8.4 point tax on nominal dynamics and
never overtakes. Mechanism: engine gravity compensation tracks the true
randomized mass, so the dominant sensitivity never reaches the policy,
and 50 Hz feedback absorbs damping/friction transients. The lesson:
randomize what the controller cannot already reject, and run the
sensitivity analysis before paying the DR tax.

```
pip install mujoco gymnasium stable-baselines3 numpy matplotlib
python src/train_p4.py         # DR training + full transfer sweep
python src/make_figures.py
```
