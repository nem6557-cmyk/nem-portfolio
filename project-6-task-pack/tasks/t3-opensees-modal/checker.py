"""Checker for T3. Deliberately does NOT use OpenSees.

The golden values come from the closed-form generalized eigenproblem
K phi = lambda M phi solved with numpy on the 2x2 story-stiffness
matrix. A submission graded by the same engine that produced it proves
nothing; an independent solution path is the whole point.
"""
import json
import sys
from pathlib import Path

import numpy as np

K1, K2, M = 25_000e3, 18_000e3, 20_000.0
K = np.array([[K1 + K2, -K2], [-K2, K2]])
Mm = np.diag([M, M])
lam, vec = np.linalg.eig(np.linalg.solve(Mm, K))
order = np.argsort(lam)                    # ascending: mode 1 first
lam, vec = lam[order], vec[:, order]
GOLD = {
    "T1_s": 2.0 * np.pi / np.sqrt(lam[0]),
    "T2_s": 2.0 * np.pi / np.sqrt(lam[1]),
    "phi_ratio": abs(vec[1, 0] / vec[0, 0]),
}
POINTS = {"T1_s": 40, "T2_s": 30, "phi_ratio": 30}
RTOL = 0.005


def close(x, gold):
    try:
        return abs(float(x) - gold) <= RTOL * abs(gold)
    except (TypeError, ValueError):
        return False


def grade(path: Path) -> int:
    try:
        ans = json.loads(path.read_text())
    except Exception as e:                                  # noqa: BLE001
        print(f"T3: could not read answer.json ({e}); score 0/100")
        return 0
    score = 0
    for k, pts in POINTS.items():
        ok = k in ans and close(ans[k], GOLD[k])
        score += pts * ok
        print(f"  {k:10s} {'PASS' if ok else 'FAIL'}"
              f"  (got {ans.get(k)!r}, want {GOLD[k]:.6g} +/-0.5%)")
    print(f"T3 score: {score}/100")
    return score


if __name__ == "__main__":
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "answer.json"
    sys.exit(0 if grade(p) == 100 else 1)
