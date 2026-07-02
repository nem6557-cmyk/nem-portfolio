# Project 5: nonlinear pushover of a steel MRF, bare vs X-braced

A 3-story, 1-bay steel moment frame in OpenSeesPy: fiber sections
(Steel02, Fy = 345 MPa, 1% hardening), forceBeamColumn distributed
plasticity with 5 Lobatto points, P-Delta columns, displacement-
controlled pushover to 4% roof drift with adaptive substepping. One
model change adds corotational-truss X-braces (20 cm^2/diagonal).

Headline numbers (from `results/summary.txt`):
T1 0.934 s -> 0.367 s; peak V/W 0.364 -> 1.218; idealized ductility
3.5 -> 7.1; and at equal demand V/W = 0.25, peak story drift falls
0.98% -> 0.14%, an **85% reduction** in the damage-driving quantity.

Two engineering notes worth reading in the source: the 2D fiber-axis
orientation check (a silent order-of-magnitude stiffness bug caught by
validating the elastic period against a hand calculation before any
pushover runs), and the equal-demand comparison rationale (equal roof
drift pushes the stiffer structure far deeper into response and flatters
nobody honestly).

Scope stated plainly: symmetric tension-compression braces (no
compression buckling model), planar frame, fixed load pattern,
computational mechanics on a structural benchmark rather than design
sign-off.

```
pip install openseespy numpy matplotlib
python src/run_pushover.py     # both frames, ~1 min
python src/make_figures.py
```
