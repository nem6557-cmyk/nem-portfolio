"""Reference solution for T1 (ACI 318-19 singly reinforced beam).

Whitney stress block: a = As*fy / (0.85*f'c*b); beta_1 per Table 22.2.2.4.3;
strain compatibility from c = a/beta_1; phi per Table 21.2.2 with the
linear transition between eps_ty and eps_ty + 0.003.
"""
import json
from pathlib import Path

B, D = 350.0, 540.0            # mm
FC, FY, ES = 28.0, 420.0, 200_000.0   # MPa
AS = 2454.0                    # mm^2
MU = 460.0                     # kN-m
EPS_CU = 0.003


def beta1(fc: float) -> float:
    if fc <= 28.0:
        return 0.85
    return max(0.65, 0.85 - 0.05 * (fc - 28.0) / 7.0)


def solve() -> dict:
    a = AS * FY / (0.85 * FC * B)                    # mm
    c = a / beta1(FC)
    eps_t = EPS_CU * (D - c) / c
    eps_ty = FY / ES
    if eps_t >= eps_ty + 0.003:
        phi = 0.90
    elif eps_t <= eps_ty:
        phi = 0.65
    else:
        phi = 0.65 + 0.25 * (eps_t - eps_ty) / 0.003
    mn = AS * FY * (D - a / 2.0) / 1e6               # kN-m
    phimn = phi * mn
    return dict(a_mm=a, eps_t=eps_t, phi=phi,
                phiMn_kNm=phimn, adequate=bool(phimn >= MU))


if __name__ == "__main__":
    ans = solve()
    out = Path(__file__).parent / "answer.json"
    out.write_text(json.dumps(ans, indent=2))
    print(json.dumps(ans, indent=2))
