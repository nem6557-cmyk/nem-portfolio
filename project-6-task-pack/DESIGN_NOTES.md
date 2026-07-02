# Designing machine-gradable engineering tasks

Notes from building this pack. The goal of a task in an AI training or
evaluation pipeline is different from a homework problem: it must be
solvable without judgment calls, gradable without a human, and hard to
pass by accident. Every choice below serves one of those three.

## 1. Closed inputs

Every number the solver needs is in the statement: geometry, material
properties, loads, code edition. Nothing requires a table lookup,
a database, or an assumption. If a real workflow would need a lookup
(beta_1, buckling branch limits), the governing rule is named in the
statement so the task tests application, not access.

## 2. Deterministic, machine-checkable deliverables

The answer is a JSON file with fixed field names and units stated in
the statement. No prose, no PDFs, no "show your work". Booleans where
the engineering question is a decision (`adequate`), floats where it is
a quantity. A checker script grades the file with one command and a
meaningful exit code, so the pack drops into CI or an RL reward loop
unchanged.

## 3. An independent verification path

The checker must not share a solution path with the reference:

- T1 and T2 recompute the code equations from first principles inside
  the checker, with their own constants.
- T3's reference runs OpenSees; its checker solves the 2x2 generalized
  eigenproblem in closed form with numpy and never imports OpenSees.

If the checker calls the same engine that produced the answer, a shared
bug grades itself correct. The independent path is what makes a golden
value golden.

## 4. Tolerances with a rationale

- 1% relative on code-equation quantities: loose enough to admit
  rounding-step differences between correct solutions, tight enough
  that a wrong method cannot land inside it.
- 0.5% on modal results: eigensolvers agree far tighter than hand
  methods, so the band narrows.
- Booleans exact. A capacity check is a decision; there is no
  "almost adequate".

The test applied to every tolerance: does at least one known-wrong
method fall outside it, and do all defensible correct methods fall
inside it?

## 5. Traps that diagnose, not decorate

Each task embeds one plausible wrong path whose output the checker
will see and fail:

- T1: the section is deliberately inadequate. Forgetting phi gives
  Mn = 492.8 kN-m > Mu = 460 and flips `adequate` to True. The trap
  converts a common omission into a wrong boolean instead of a small
  numeric error.
- T2: lambda_c = 53.8 puts the column in the inelastic branch.
  Applying the elastic Euler expression (E3-3) anyway gives
  Fcr = 597.1 MPa versus the correct 279.1: a 2.1x error, unmissable.
- T3: mixing kN/m with kg moves both periods by a factor of 31.6, and
  grabbing the eigenvalues in solver order instead of ascending order
  swaps T1 and T2. Both land far outside 0.5%.

A failed field should localize the misconception, which is what makes
these usable as RL reward signals rather than pass/fail walls.

## 6. Partial credit mirrors the dependency graph

Points sit on intermediate quantities in solution order (a, eps_t, phi,
phiMn; lambda, Fe, Fcr, phiPn), so a solver that is right up to step k
scores proportionally. The graded fields are exactly the quantities a
reviewing engineer would check on paper.

## 7. Anti-patterns this pack avoids

- Units left implicit anywhere in statement or schema.
- Tolerances wide enough that the trap path passes.
- Checker importing the reference (or its engine) for goldens.
- Fields a grader cannot verify without judgment ("justify briefly").
- Statements that depend on a specific software version's defaults.

## Pack regression test

`python3 grade_all.py` runs every reference through its checker and
exits nonzero unless the whole pack scores 100/100. A task ships only
when its reference passes its own independent checker.
