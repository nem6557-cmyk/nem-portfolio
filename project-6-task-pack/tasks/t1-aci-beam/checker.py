"""Deterministic checker for T1.

Grades an answer.json against golden values computed independently at
authoring time and verified by hand (a = 2454*420/(0.85*28*350) =
123.731 mm; c = 145.566 mm; eps_t = 0.0081290; phi = 0.90 since
eps_t > eps_ty + 0.003 = 0.0051; Mn = 492.804 kN-m; phiMn = 443.524
kN-m < Mu = 460 -> NOT adequate).

The beam is deliberately inadequate: an answer produced by pattern-
matching "design checks usually pass" fails the boolean, and a phi
omission (Mn = 492.9 > 460 -> "adequate") flips it too. The boolean is
the gaming trap; the numerics catch everything else.

Scoring: each of the five fields is worth 20 points; numeric fields
must be within 1% relative tolerance. Exit code 0 iff score == 100.
"""
import json
import sys
from pathlib import Path

GOLD = dict(a_mm=123.7311, eps_t=0.0081290, phi=0.90,
            phiMn_kNm=443.524, adequate=False)
RTOL = 0.01


def close(x, ref):
    try:
        return abs(float(x) - ref) <= RTOL * abs(ref)
    except (TypeError, ValueError):
        return False


def grade(path: Path) -> int:
    try:
        ans = json.loads(path.read_text())
    except Exception as e:                                  # noqa: BLE001
        print(f"T1: could not read answer.json ({e}); score 0/100")
        return 0
    score = 0
    for k in ("a_mm", "eps_t", "phi", "phiMn_kNm"):
        ok = k in ans and close(ans[k], GOLD[k])
        score += 20 * ok
        print(f"  {k:10s} {'PASS' if ok else 'FAIL'}"
              f"  (got {ans.get(k)!r}, want {GOLD[k]:.6g} +/-1%)")
    ok = isinstance(ans.get("adequate"), bool) and ans["adequate"] == GOLD["adequate"]
    score += 20 * ok
    print(f"  {'adequate':10s} {'PASS' if ok else 'FAIL'}"
          f"  (got {ans.get('adequate')!r}, want {GOLD['adequate']})")
    print(f"T1 score: {score}/100")
    return score


if __name__ == "__main__":
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "answer.json"
    sys.exit(0 if grade(p) == 100 else 1)
