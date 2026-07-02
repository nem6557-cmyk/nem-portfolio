"""Project 5: pushover and braced retrofit of a 3-story steel moment frame.

A fully specified nonlinear benchmark in OpenSeesPy. Every dimension and
material parameter is stated here, so nothing hangs on a section table
lookup, and every number the write-up quotes regenerates from this file.

Frame: single bay, L = 6.0 m; three stories at h = 3.5 m (H = 10.5 m).
Sections are plate-built I-shapes, chosen so the strong-column
weak-beam ratio at a joint is about 3, which puts the plastic mechanism
in the beams where a capacity-designed frame wants it:

  columns: d 400, bf 300, tf 20, tw 12  (mm)   Zx ~ 2.67e-3 m^3
  beams:   d 450, bf 200, tf 14, tw  9  (mm)   Zx ~ 1.62e-3 m^3

Material: Steel02, Fy = 345 MPa, E = 200 GPa, b = 0.01 (Giuffre-
Menegotto-Pinto). Elements: forceBeamColumn with 5 Gauss-Lobatto points
and fiber sections; columns carry P-Delta through their geometric
transformation. Seismic mass: 30 t per beam-column node, 180 t total
(W = 1766 kN), applied as gravity point loads before the push.

Pushover: displacement control at the roof, lateral pattern
proportional to mass times height, pushed to 4 percent roof drift with
adaptive substepping on non-convergence.

Retrofit: X-braces in every story, corotational truss, A = 20 cm^2,
same steel. Braces are tension-compression symmetric here; no buckling
model. That is stated scope, not an oversight: the comparison isolates
what added stiffness and strength do to period, capacity, and the
drift profile.

Outputs: results/p5_curves.npz, results/summary.txt, and three figures.
"""

from __future__ import annotations
import numpy as np
import openseespy.opensees as ops
from pathlib import Path

RES = Path(__file__).resolve().parent.parent / "results"
RES.mkdir(exist_ok=True)

# ---------------------------------------------------------------- geometry
L, H_STORY, N_STORY = 6.0, 3.5, 3
FY, E0, B_HARD = 345e6, 200e9, 0.01
MASS_NODE = 30_000.0                      # kg per beam-column node
G = 9.81
W_TOTAL = 2 * N_STORY * MASS_NODE * G     # N
COL = dict(d=0.40, bf=0.30, tf=0.020, tw=0.012)
BEAM = dict(d=0.45, bf=0.20, tf=0.014, tw=0.009)
A_BRACE = 20e-4                           # m^2
ROOF_TARGET = 0.04 * N_STORY * H_STORY    # 4% roof drift
DINC = 0.001                              # 1 mm displacement steps


def i_section(tag: int, s: dict, mat: int, nf: int = 8):
    """Fiber I-section from plate dimensions, strong-axis bending.

    In a 2D model OpenSees bends fiber sections about the section
    y-axis, so the depth d runs along y and the flange width along z.
    patch('rect', mat, nDivY, nDivZ, yI, zI, yJ, zJ).
    """
    d, bf, tf, tw = s["d"], s["bf"], s["tf"], s["tw"]
    hw = d / 2 - tf
    ops.section("Fiber", tag)
    ops.patch("rect", mat, 2, nf,  hw, -bf / 2, d / 2, bf / 2)   # top flange
    ops.patch("rect", mat, 2, nf, -d / 2, -bf / 2, -hw, bf / 2)  # bottom flange
    ops.patch("rect", mat, nf, 2, -hw, -tw / 2,  hw, tw / 2)     # web


def build(braced: bool):
    ops.wipe()
    ops.model("basic", "-ndm", 2, "-ndf", 3)

    # nodes: tag = 10*story + column (story 0 = base; column 1 left, 2 right)
    for s in range(N_STORY + 1):
        for c, x in ((1, 0.0), (2, L)):
            ops.node(10 * s + c, x, s * H_STORY)
            if s > 0:
                ops.mass(10 * s + c, MASS_NODE, 1e-6, 1e-6)
    ops.fix(1, 1, 1, 1)
    ops.fix(2, 1, 1, 1)

    ops.uniaxialMaterial("Steel02", 1, FY, E0, B_HARD, 18.0, 0.925, 0.15)
    i_section(1, COL, 1)
    i_section(2, BEAM, 1)
    ops.beamIntegration("Lobatto", 1, 1, 5)
    ops.beamIntegration("Lobatto", 2, 2, 5)
    ops.geomTransf("PDelta", 1)           # columns
    ops.geomTransf("Linear", 2)           # beams

    eid = 0
    for s in range(N_STORY):              # columns
        for c in (1, 2):
            eid += 1
            ops.element("forceBeamColumn", eid,
                        10 * s + c, 10 * (s + 1) + c, 1, 1)
    for s in range(1, N_STORY + 1):       # beams
        eid += 1
        ops.element("forceBeamColumn", eid, 10 * s + 1, 10 * s + 2, 2, 2)
    if braced:
        for s in range(N_STORY):          # X-braces, both diagonals
            for a, b in ((10 * s + 1, 10 * (s + 1) + 2),
                         (10 * s + 2, 10 * (s + 1) + 1)):
                eid += 1
                ops.element("corotTruss", eid, a, b, A_BRACE, 1)

    # gravity
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for s in range(1, N_STORY + 1):
        for c in (1, 2):
            ops.load(10 * s + c, 0.0, -MASS_NODE * G, 0.0)
    ops.system("BandGeneral"); ops.numberer("RCM")
    ops.constraints("Plain"); ops.test("NormDispIncr", 1e-8, 25)
    ops.algorithm("Newton"); ops.integrator("LoadControl", 0.1)
    ops.analysis("Static")
    assert ops.analyze(10) == 0, "gravity analysis failed"
    ops.loadConst("-time", 0.0)


def first_period() -> float:
    lam = ops.eigen("-genBandArpack", 1)[0]
    return 2 * np.pi / np.sqrt(lam)


def pushover():
    """Displacement-controlled push; returns roof drift, V/W, story drifts."""
    ops.timeSeries("Linear", 2)
    ops.pattern("Plain", 2, 2)
    zsum = sum(s * H_STORY for s in range(1, N_STORY + 1))
    for s in range(1, N_STORY + 1):
        f = (s * H_STORY) / zsum          # mass equal per floor -> m*z shape
        for c in (1, 2):
            ops.load(10 * s + c, f / 2, 0.0, 0.0)

    roof = 10 * N_STORY + 1
    ops.integrator("DisplacementControl", roof, 1, DINC)
    drift, vw, story = [0.0], [0.0], [np.zeros(N_STORY)]
    d = 0.0
    while d < ROOF_TARGET:
        ok = ops.analyze(1)
        if ok != 0:                        # adaptive fallback
            ops.algorithm("ModifiedNewton")
            ops.integrator("DisplacementControl", roof, 1, DINC / 10)
            ok = ops.analyze(10)
            ops.algorithm("Newton")
            ops.integrator("DisplacementControl", roof, 1, DINC)
            if ok != 0:
                print(f"  stopped at roof drift {d / (N_STORY*H_STORY):.3%}")
                break
        d = ops.nodeDisp(roof, 1)
        ops.reactions()
        v = -(ops.nodeReaction(1, 1) + ops.nodeReaction(2, 1))
        ux = [ops.nodeDisp(10 * s + 1, 1) for s in range(N_STORY + 1)]
        story.append(np.diff(ux) / H_STORY)
        drift.append(d / (N_STORY * H_STORY))
        vw.append(v / W_TOTAL)
    return np.array(drift), np.array(vw), np.stack(story)


def idealized(drift, vw):
    """Idealized bilinear: elastic stiffness from the first 10 mm of push,
    yield at the intersection with peak strength. Returns (ke, dy, mu)."""
    k = np.polyfit(drift[1:11], vw[1:11], 1)[0]     # (V/W) per unit drift
    vmax = vw.max()
    dy = vmax / k
    mu = drift[-1] / dy
    return k, dy, mu


def run(braced: bool):
    build(braced)
    t1 = first_period()
    drift, vw, story = pushover()
    return dict(T1=t1, drift=drift, vw=vw, story=story)


if __name__ == "__main__":
    bare = run(False)
    retro = run(True)
    np.savez(RES / "p5_curves.npz",
             b_drift=bare["drift"], b_vw=bare["vw"], b_story=bare["story"],
             r_drift=retro["drift"], r_vw=retro["vw"], r_story=retro["story"],
             b_T1=bare["T1"], r_T1=retro["T1"])

    kb, dyb, mub = idealized(bare["drift"], bare["vw"])
    kr, dyr, mur = idealized(retro["drift"], retro["vw"])

    # story drift profiles at a common base-shear demand, V/W = 0.25.
    # Equal-demand is the retrofit-relevant comparison: at the same lateral
    # load the braced frame is still elastic while the bare frame is near
    # capacity. (At equal roof drift the comparison inverts, because the
    # stiff braced frame is far past yield there and concentrates drift in
    # story 1; that is a real behavior, noted in the write-up.)
    def drifts_at_vw(frame, level=0.25):
        i = int(np.argmax(frame["vw"] >= level))
        return frame["story"][i]

    sb, sr = drifts_at_vw(bare), drifts_at_vw(retro)
    with open(RES / "summary.txt", "w") as fh:
        fh.write("Project 5 summary: pushover and braced retrofit\n")
        fh.write(f"seismic weight W: {W_TOTAL/1e3:.0f} kN\n")
        fh.write(f"T1 bare: {bare['T1']:.3f} s | T1 braced: {retro['T1']:.3f} s\n")
        fh.write(f"peak V/W bare: {bare['vw'].max():.3f} | "
                 f"braced: {retro['vw'].max():.3f}\n")
        fh.write(f"idealized ductility mu bare: {mub:.1f} | braced: {mur:.1f}\n")
        fh.write(f"peak story drift at V/W=0.25, bare: {sb.max():.2%} "
                 f"(story {int(sb.argmax())+1})\n")
        fh.write(f"peak story drift at V/W=0.25, braced: {sr.max():.2%} "
                 f"(story {int(sr.argmax())+1})\n")
        fh.write(f"drift reduction at equal demand: "
                 f"{(1 - sr.max()/sb.max()):.0%}\n")
        fh.write(f"roof drift reached, bare: {bare['drift'][-1]:.2%} | "
                 f"braced: {retro['drift'][-1]:.2%}\n")
    print(open(RES / "summary.txt").read())
