# Physics Simulation Portfolio

Six projects on two tracks, built around one idea: simulation work you
can trust because it was verified, not asserted. Everything runs
headless, produces quantitative results against a known reference, and
is written to be read, run, and extended.

**Live portfolio site:** https://effervescent-lamington-fd7140.netlify.app The
site source lives in [`site/`](site) and is a dependency-free static
build.

## Track 1: robotics, sim-to-real in MuJoCo

| | project | what it shows |
|---|---|---|
| 1 | [Arm model + sim-to-real parameter identification](project-1-sysid) | Analytic mass properties injected into MJCF, then friction, damping, and true motor gain recovered from data and validated out of sample (1.1% mean parameter error). |
| 2 | [Thermally coupled actuator model](project-2-thermal-actuator) | The motor as a thermal device: a two-node network coupled into the physics so sustained-load torque derating, a commonly ignored sim-to-real failure mode, appears in simulation. |
| 3 | [RL reach environment, built and debugged](project-3-rl-reach) | A gymnasium environment, a reward shaping ablation (70% vs 0% at equal budget), and the debugging record: an MJCF unit bug and a gravity exploration trap, both found with scripted baselines, constraint-force inspection, and a reference-implementation comparison. |
| 4 | [Domain randomization, measured](project-4-domain-randomization) | A controlled zero-shot transfer benchmark over identified-parameter uncertainty, and an honest negative result with its mechanism: randomize what the controller cannot already reject. |

## Track 2: structural analysis and AI task design in OpenSees

| | project | what it shows |
|---|---|---|
| 5 | [Nonlinear pushover, bare vs braced steel frame](project-5-opensees-pushover) | Fiber sections, distributed plasticity, P-Delta, adaptive displacement control, and a comparison framed at equal demand: 85% story-drift reduction at V/W = 0.25. |
| 6 | [Machine-gradable task pack](project-6-task-pack) | Three structural tasks with closed statements, reference solutions, and checkers on independent solution paths, each with a diagnostic trap its tolerances are tuned to catch. 3/3 verified 100/100. |

## The angle these projects take

My background is thermal-fluid systems and high-heat-flux electronics
cooling, with heavy day-to-day use of CAD, finite-element and CFD
tooling, rigid-body mechanics, and Python or MATLAB for modelling and
parameter estimation. That work is peer reviewed, including thermal
resistance network analysis of a two-phase cooling module at IEEE
ITherm 2026, the same class of model project 2 couples into MuJoCo.

The through-line is verification discipline. Project 1 validates its
identified parameters out of sample. Project 3's environment is proven
learnable with scripted controllers before any policy is blamed.
Project 4's transfer numbers come from seeded, matched-condition
evaluation. Project 5 checks its elastic period against a hand
calculation before running anything nonlinear. Project 6 makes the
principle explicit: a golden value is golden only because two solution
paths that share nothing agree on it.

## Mapping to a robotics simulation / RL role

| requirement | where it shows up |
|---|---|
| High-fidelity robot models (URDF/MJCF) with accurate kinematics, dynamics, contact | Project 1: analytic inertials injected into MJCF; project 3: annotated MJCF including the unit-parsing failure mode |
| MuJoCo simulation environments | All of track 1, headless MuJoCo 3.x |
| Design and implement RL environments | Project 3: gymnasium API, feasibility-guaranteed target sampling, hold-based success criterion |
| Implement and tune RL training (PPO), reward design | Project 3: potential-based shaping with the theory cited and an ablation quantifying it |
| Domain randomization and sim-to-real transfer | Project 4: per-episode randomization hook, extrapolation-region transfer benchmark, mechanism-level analysis |
| Debug contact dynamics and simulation behavior | Project 3: qfrc_constraint diagnosis, floor-contact reasoning, exploration-trap measurement |
| Evaluate trained policies | Projects 3 and 4: deterministic fixed-target evaluation, scripted-controller floors, matched-condition comparisons |
| Tune physics parameters for sim-to-real | Projects 1, 2, and 4 (what happens when they drift) |
| ROS2 integration | Project 1: `ros2_bridge.py`, an rclpy sim server publishing `/joint_states` and taking torque commands |
| Clean, performant Python | Vectorised NumPy, live model-parameter mutation, SciPy least squares, SB3 integration |

## Mapping to a structural engineering AI task creation role

| requirement | where it shows up |
|---|---|
| OpenSees / OpenSeesPy modeling | Project 5: fiber sections, forceBeamColumn, Steel02, P-Delta, corotational truss; project 6 T3 |
| Nonlinear analysis (pushover) | Project 5: displacement control with adaptive substepping, bilinear idealization, ductility |
| Code-based checks (ACI 318, AISC 360) | Project 6 T1 and T2, reduced to exact machine-checkable quantities with the branch logic that trips solvers |
| Author tasks with verified golden solutions | Project 6: statement + reference + independent checker per task, pack regression at 100/100 |
| Evaluation design | Project 6: tolerance rationale, diagnostic traps, partial credit mirroring the solution dependency graph; DESIGN_NOTES.md |

I am a mechanical engineer (BS/MS, PhD candidate) working the
structural projects as computational mechanics against published code
equations, and the write-ups say so plainly.

## Honest scope

These are portfolio pieces, written to be defensible line by line, not
claims of production experience:

- The ROS2 bridge is written to correct rclpy patterns but is not
  exercised in this repo's sandbox, which has no ROS2 install.
- Project 3's training backend is Stable-Baselines3. A from-scratch PPO
  was written, instrumented, and retired when reference comparison
  showed its gradient sat below the trajectory-variance noise floor at
  this batch size; the environment, reward design, baselines, and
  evaluation harness are the work product.
- RL results are single-seed per condition; comparisons are
  matched-condition and sample sizes are stated.
- Project 5's braces are symmetric tension-compression (no buckling
  model); the frame is planar; no design code sign-off is claimed.
- Everything is validated in simulation against a known reference,
  which is the right way to prove the method.

## Quick start

```bash
pip install -r requirements.txt

# Track 1
cd project-1-sysid && python src/system_id.py
cd ../project-3-rl-reach && python src/train_p3.py      # ~35 min CPU
cd ../project-4-domain-randomization && python src/train_p4.py

# Track 2
cd ../project-5-opensees-pushover && python src/run_pushover.py
cd ../project-6-task-pack && python grade_all.py
```

Headless rendering uses EGL (`MUJOCO_GL=egl`) where figures need GL;
all numerical results regenerate without a display.

## The labs

Fifteen compact builds in `labs/`, three each across five benches: `ngspice/` (circuit simulation, including the project 2 thermal network solved as a SPICE circuit and agreeing to 4.5 mK), `paraview/` (headless VTK renders of the real dissertation CFD fields, with pvpython twins), `ml/` (a GP surrogate at 1.46 K cross-validated RMSE on 261 real data points, a PINN benchmarked honestly against Crank-Nicolson, a CV-pitfall study), `ai-eval/` (mutation testing the project 6 checkers to 79/79 sensitivity, tolerance sweeps, item-response analysis), and `fun/` (prayer times from solar geometry, measured chaos, plume art). Every lab ships `run_lab.py`, `RESULTS.txt`, and its figure; every number on the site's labs pages comes from those logs.
