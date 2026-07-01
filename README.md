# Robotics Simulation Portfolio

Two focused projects built around one idea: closing the sim-to-real gap in
physics simulation. Both run headless in MuJoCo, both produce quantitative
results, and both are written to be read, run, and extended.

**Live portfolio site:** _add your Netlify URL here once deployed._ The site
source lives in [`site/`](site) and is a dependency-free static build.

| | project | what it shows |
|---|---|---|
| 1 | [High-fidelity arm model + sim-to-real parameter identification](project-1-sysid) | Building an accurate MJCF from first-principles mass properties, then recovering the friction, damping, and true motor torque constant from data and validating out of sample. |
| 2 | [Thermally coupled actuator model](project-2-thermal-actuator) | Modelling the motor as a thermal device so that sustained-torque derating, a real and commonly ignored sim-to-real failure mode, appears in simulation. |

## The angle these projects take

My background is thermal-fluid systems and high-heat-flux electronics cooling,
with heavy day-to-day use of CAD, finite-element and CFD tooling, rigid-body
mechanics, and Python or MATLAB for modelling and parameter estimation. That
maps onto robotics simulation more directly than it first appears, and these
two projects lead with that overlap rather than hiding it.

Project 1 is the core competency the role asks for, done carefully: an MJCF
whose link inertias are derived analytically from geometry and material (the
mass-properties discipline of a mechanical designer, carried into the simulator
where dynamics actually depend on it), plus a full identification-and-validation
loop for the parameters that are never on a drawing.

Project 2 is the part I can bring that most candidates cannot. Modelling an
actuator's winding and case as a two-node lumped thermal network, deriving its
continuous torque rating and time constants, and coupling that into the physics
so a hot joint sags, is the same electronics-cooling modelling I do in research,
pointed at a sim-to-real problem. It is a small model with an outsized effect on
what a controller or policy can actually rely on.

## Mapping to the role

| requirement | where it shows up |
|---|---|
| High-fidelity robot models (URDF/MJCF) with accurate kinematics, dynamics, contact | Project 1: analytic inertials injected into MJCF; realistic actuator gain |
| MuJoCo simulation environments | Both projects, headless MuJoCo 3.x |
| End-to-end simulation pipelines for training, testing, validation | Project 1: excitation, logging, identification, out-of-sample validation |
| Tune physics parameters (friction, damping, inertia, actuator models) for sim-to-real | Project 1 (mechanical + gain) and Project 2 (thermal actuator) |
| ROS2 integration | Project 1: `ros2_bridge.py`, an rclpy sim server publishing `/joint_states` and taking torque commands |
| Rigid-body dynamics, contact mechanics, control theory | Gravity-compensated PD control, multiple-shooting identification, lumped thermal dynamics |
| Creating and validating robot models | Project 1's validation is the whole point of the second half |
| Clean, performant Python | Vectorised NumPy, live model-parameter mutation without recompiling, SciPy least squares, RK4 integration |
| Drive to close the sim-to-real gap | The organising theme of the whole repo |

## Honest scope

These are portfolio pieces, written to be defensible line by line, not claims of
production robotics experience. A few things are deliberately out of scope and
are the natural next steps:

- The ROS2 bridge is written to correct rclpy patterns but is not exercised in
  this repo's sandbox, which has no ROS2 install. It is meant to be run on a
  machine with ROS2 Humble (recipe in its docstring).
- No NVIDIA Isaac Sim or Gazebo here; MuJoCo was chosen for a headless,
  reproducible, dependency-light build. The modelling and identification ideas
  carry over directly.
- Everything is validated in simulation against a known ground truth, which is
  the right way to prove the method. Real-hardware validation is the obvious
  follow-on.

## Quick start

```bash
pip install mujoco numpy scipy matplotlib

# Project 1
cd project-1-sysid
python src/inertia.py
python src/build_arm.py
MUJOCO_GL=egl python src/system_id.py

# Project 2
cd ../project-2-thermal-actuator
python src/thermal_actuator.py
MUJOCO_GL=egl python src/run_thermal_demo.py
```

Headless rendering uses EGL (`MUJOCO_GL=egl`). The numerical results and figures
regenerate without a display; only the rendered arm images need a GL backend.
