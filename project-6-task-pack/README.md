# Project 6: machine-gradable structural engineering task pack

Three tasks packaged the way an AI training/eval pipeline needs them:
closed problem statement (`task.md`), reference solution, and a checker
that grades a JSON deliverable on an **independent solution path**.

| task | graded fields | embedded trap |
|---|---|---|
| T1 ACI 318-19 beam flexure | a, eps_t, phi, phiMn, adequate | section is deliberately inadequate; omitting phi flips the boolean |
| T2 AISC 360-22 column buckling | lambda, Fe, Fcr, phiPn, adequate | slenderness is inelastic; elastic-branch misuse gives Fcr 2.1x high |
| T3 OpenSees modal analysis | T1_s, T2_s, phi_ratio | kN/m with kg moves periods 31.6x; solver-order eigenvalues swap modes |

T3's checker never imports OpenSees: it solves the 2x2 generalized
eigenproblem in closed form with numpy. A golden value is golden only
because two solution paths that share nothing agree on it.

```
pip install openseespy numpy
python grade_all.py     # exit 0 iff the whole pack scores 100/100
```

Design rationale, tolerance logic, and the anti-pattern list are in
[`DESIGN_NOTES.md`](DESIGN_NOTES.md).
