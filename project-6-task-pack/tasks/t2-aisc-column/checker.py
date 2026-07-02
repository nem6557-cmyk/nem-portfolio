"""Deterministic checker for T2.

Golden values fixed at authoring time:
lam = 4200/78 = 53.8462; Fe = pi^2 E / lam^2 = 680.801 MPa;
Fy/Fe = 0.5068 <= 2.25 -> inelastic branch, Fcr = 0.658^(Fy/Fe) Fy
= 279.064 MPa; phiPn = 0.9 Fcr A = 3265.05 kN >= Pu = 3000 kN.

The branch point is the trap: applying E3-3 (0.877 Fe) here gives
597.1 MPa and fails Fcr while Fe still passes, which separates
"knows the Euler formula" from "knows the specification".
"""
import json
import sys
from pathlib import Path

GOLD = dict(lam=53.846154, Fe_MPa=680.8013, Fcr_MPa=279.0641,
            phiPn_kN=3265.050, adequate=True)
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
        print(f"T2: could not read answer.json ({e}); score 0/100")
        return 0
    score = 0
    for k in ("lam", "Fe_MPa", "Fcr_MPa", "phiPn_kN"):
        ok = k in ans and close(ans[k], GOLD[k])
        score += 20 * ok
        print(f"  {k:10s} {'PASS' if ok else 'FAIL'}"
              f"  (got {ans.get(k)!r}, want {GOLD[k]:.6g} +/-1%)")
    ok = isinstance(ans.get("adequate"), bool) and ans["adequate"] == GOLD["adequate"]
    score += 20 * ok
    print(f"  {'adequate':10s} {'PASS' if ok else 'FAIL'}"
          f"  (got {ans.get('adequate')!r}, want {GOLD['adequate']})")
    print(f"T2 score: {score}/100")
    return score


if __name__ == "__main__":
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "answer.json"
    sys.exit(0 if grade(p) == 100 else 1)
