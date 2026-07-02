"""Reference solution for T3: two-story shear building modal analysis.

Model: 1D chain (ndm=1, ndf=1). Each story is a Truss element with
E = k, A = 1, L = 1, so its axial stiffness EA/L equals the story
stiffness. Lumped masses at the floor nodes; eigen(2); periods from
the eigenvalues, mode shape from nodeEigenvector.
"""
import json
import math
from pathlib import Path

import openseespy.opensees as ops

K1 = 25_000e3          # N/m
K2 = 18_000e3          # N/m
M = 20_000.0           # kg


def solve() -> dict:
    ops.wipe()
    ops.model("basic", "-ndm", 1, "-ndf", 1)
    for tag, x in ((1, 0.0), (2, 1.0), (3, 2.0)):
        ops.node(tag, x)
    ops.fix(1, 1)
    ops.mass(2, M)
    ops.mass(3, M)
    ops.uniaxialMaterial("Elastic", 1, K1)
    ops.uniaxialMaterial("Elastic", 2, K2)
    ops.element("Truss", 1, 1, 2, 1.0, 1)
    ops.element("Truss", 2, 2, 3, 1.0, 2)
    lams = ops.eigen("-fullGenLapack", 2)
    periods = [2.0 * math.pi / math.sqrt(l) for l in lams]
    phi2 = ops.nodeEigenvector(2, 1, 1)
    phi3 = ops.nodeEigenvector(3, 1, 1)
    return {
        "T1_s": max(periods),
        "T2_s": min(periods),
        "phi_ratio": abs(phi3 / phi2),
    }


if __name__ == "__main__":
    out = solve()
    Path(__file__).parent.joinpath("answer.json").write_text(
        json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
