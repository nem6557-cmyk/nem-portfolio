"""Reference solution for T2 (AISC 360-22 E3 flexural buckling)."""
import json
import math
from pathlib import Path

E, FY = 200_000.0, 345.0        # MPa
A, RY = 13_000.0, 78.0          # mm^2, mm
LC, PU = 4200.0, 3000.0         # mm, kN


def solve() -> dict:
    lam = LC / RY
    fe = math.pi ** 2 * E / lam ** 2
    if FY / fe <= 2.25:                      # E3-2, inelastic
        fcr = (0.658 ** (FY / fe)) * FY
    else:                                    # E3-3, elastic
        fcr = 0.877 * fe
    phipn = 0.90 * fcr * A / 1e3             # kN
    return dict(lam=lam, Fe_MPa=fe, Fcr_MPa=fcr,
                phiPn_kN=phipn, adequate=bool(phipn >= PU))


if __name__ == "__main__":
    ans = solve()
    (Path(__file__).parent / "answer.json").write_text(json.dumps(ans, indent=2))
    print(json.dumps(ans, indent=2))
