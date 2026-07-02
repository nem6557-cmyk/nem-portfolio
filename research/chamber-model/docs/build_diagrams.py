#!/usr/bin/env python3
"""Render two color-coded flowcharts: (1) the gray-box physics model,
(2) the 3D VOF numerical study. Established physics vs fitted gray-box parts
are colour-separated so the model is legible at a glance."""
from graphviz import Digraph

IO   = "#d5e8d4"  # inputs / properties (green)
PHYS = "#dae8fc"  # established physics  (blue)
FIT  = "#ffe6cc"  # fitted gray-box      (amber)
RES  = "#e1d5e7"  # output / validation  (purple)
SOLV = "#fff2cc"  # solver setup         (yellow)
STAT = "#f8cecc"  # honest status        (red)

# ============================================================ DIAGRAM 1
g = Digraph("physics", format="png")
g.attr(rankdir="TB", bgcolor="white", fontname="Helvetica", splines="spline",
       nodesep="0.35", ranksep="0.5", labelloc="t", fontsize="20",
       label=("Physics map  -  gray-box reduced-order chamber model\n"
              "green = inputs    blue = established physics    "
              "amber = fitted (gray-box)    purple = output / validation\n"))
g.attr("node", shape="box", style="rounded,filled", fontname="Helvetica",
       fontsize="11", margin="0.16,0.10")
g.attr("edge", fontname="Helvetica", fontsize="9", color="#666666")

with g.subgraph(name="cluster_in") as c:
    c.attr(label="INPUTS", style="rounded,dashed", color="#82b366", fontsize="12")
    c.node("IN1", "Heat flux\nq'' [W/cm2]", fillcolor=IO)
    c.node("IN2", "Coolant inlet\nT_in [C]", fillcolor=IO)
    c.node("IN3", "Condenser geometry\n33 / 42 / 66-tube", fillcolor=IO)
    c.node("IN4", "Chip type\nplain / microchannel", fillcolor=IO)

g.node("PROP", "Fluid properties\nCoolProp (water) / literature (HFE-7000)\n"
               "rho  mu  k  cp  h_fg  sigma  Pr  beta", fillcolor=IO)

g.node("OP", "STEP 1   Operating-point map   (fitted)\n"
             "T_sat = a*T_in + b*Q + c\n"
             "subcooling = max(d*T_in + e*Q + f, 0)", fillcolor=FIT)

with g.subgraph(name="cluster_mech") as c:
    c.attr(label="STEP 2   two parallel heat-transfer mechanisms",
           style="rounded,dashed", color="#6c8ebf", fontsize="12")
    c.node("NC", "Natural convection  (Churchill-Chu / McAdams)\n"
                 "Ra = g*beta*dT*L^3 / (nu*alpha)\n"
                 "Nu = 0.15*Ra^(1/3)  or  0.54*Ra^(1/4)\n"
                 "q_nc = NC * (Nu*k/L) * dT", fillcolor=PHYS)
    c.node("NB", "Nucleate boiling  (Rohsenow)\n"
                 "q_nb = mu*h_fg*sqrt( g(rho_l-rho_v)/sigma )\n"
                 "        * ( cp*dT_sat / (C_sf*h_fg*Pr^s) )^3", fillcolor=PHYS)
    c.node("MC", "Microchannel area augmentation\n(Cooke-Kandlikar)   area x 2.17", fillcolor=PHYS)

g.node("BLEND", "Quadrature blend\nq'' = sqrt( q_nc^2 + q_nb^2 )", fillcolor=PHYS)
g.node("SOLVE", "Brent root-find\nsolve for T_surf", fillcolor=PHYS)
g.node("OUT",   "OUTPUT\nChip surface temperature  T_surf [C]", fillcolor=RES)

g.node("COND", "Condenser-side resistance  (Hausen, developing-laminar)\n"
               "Re, Pr  ->  Nu = 3.66 + ...  ->  h_i\n"
               "R = 1/(h_i*A_i) + R_wall\n"
               "finding:  COOLANT-SIDE LIMITED", fillcolor=PHYS)

g.node("CAL", "Calibrated constants   (GRAY-BOX, fitted to data)\n"
              "C_sf: plain 0.0131 / micro 0.0067  (transfer across chambers)\n"
              "NC:  33t = 9.0,  42t = 3.5  (per chamber)\n"
              "map a..f  (per chamber)", fillcolor=FIT)

g.node("VAL", "VALIDATION   vs 261 measured points\n"
              "RMSE 4.40 K,  R2 0.937\n"
              "leave-one-coolant-out:  33t 4.95 K / 42t 9.03 K", fillcolor=RES)

for a, b in [("IN1","OP"),("IN2","OP"),("IN3","OP"),("OP","NC"),("OP","NB"),
             ("PROP","NC"),("PROP","NB"),("IN4","MC"),("MC","NB"),
             ("NC","BLEND"),("NB","BLEND"),("BLEND","SOLVE"),("SOLVE","OUT"),
             ("IN3","COND"),("PROP","COND"),("OUT","VAL")]:
    g.edge(a, b)
g.edge("IN1","SOLVE", label="target q''", style="dotted")
g.edge("CAL","OP", label="a..f", style="dashed")
g.edge("CAL","NB", label="C_sf", style="dashed")
g.edge("CAL","NC", label="NC",   style="dashed")

g.attr(dpi="160")
g.render("/home/claude/diagrams/physics_model_map", cleanup=True)
g.format = "pdf"; g.render("/home/claude/diagrams/physics_model_map", cleanup=True)
print("diagram 1 done")

# ============================================================ DIAGRAM 2
n = Digraph("numerical", format="png")
n.attr(rankdir="TB", bgcolor="white", fontname="Helvetica", splines="spline",
       nodesep="0.35", ranksep="0.5", labelloc="t", fontsize="20",
       label=("Numerical study map  -  3D VOF + phase-change (OpenFOAM)\n"
              "green = geometry    blue = mesh pipeline    yellow = solver setup    "
              "amber = HPC step (not done)    red = honest status\n"))
n.attr("node", shape="box", style="rounded,filled", fontname="Helvetica",
       fontsize="11", margin="0.16,0.10")
n.attr("edge", fontname="Helvetica", fontsize="9", color="#666666")

n.node("GEO", "Geometry   (Python-generated STL, 3360 triangles)\n"
              "42-tube bundle, OD 3.175 mm\n"
              "80 x 80 x 42 mm chamber\n"
              "chip 34.5 x 32 mm on floor,  ~40% liquid fill", fillcolor=IO)

with n.subgraph(name="cluster_mesh") as c:
    c.attr(label="MESH PIPELINE", style="rounded,dashed", color="#6c8ebf", fontsize="12")
    c.node("BM",  "blockMesh\nbase ~2 mm  ->  33,600 cells", fillcolor=PHYS)
    c.node("SFE", "surfaceFeatureExtract\ntube edges", fillcolor=PHYS)
    c.node("SHM", "snappyHexMesh\ncastellate (+ snap + layers)\n"
                  "74k staircased  /  300k snapped (checkMesh OK)", fillcolor=PHYS)
    c.node("TS",  "topoSet + createPatch\ncarve chip patch from floor", fillcolor=PHYS)
    c.node("SF",  "setFields\n40% liquid fill", fillcolor=PHYS)

with n.subgraph(name="cluster_solver") as c:
    c.attr(label="SOLVER SETUP", style="rounded,dashed", color="#d6b656", fontsize="12")
    c.node("GOV", "Governing equations  (VOF, interface-capturing)\n"
                  "phase fraction alpha transport\n"
                  "momentum + surface tension (Navier-Stokes)\n"
                  "energy (T)\n"
                  "Lee-type phase-change source", fillcolor=SOLV)
    c.node("PROP2","Properties\nwater / vapour: rho, nu, cp, kappa, h_fg\n"
                   "sigma, T_sat\ncoeffC, coeffE   (UNCALIBRATED)", fillcolor=SOLV)
    c.node("BC",  "Boundary conditions\nchip 358 K,  tubes 305 K\n"
                  "walls no-slip,  gravity -z", fillcolor=SOLV)

n.node("RUN", "interCondensatingEvaporatingFoam\n"
              "PIMPLE,  adaptive dt (maxCo 0.4),  transient", fillcolor=SOLV)
n.node("POST","Post-process\nfoamToVTK  ->  PyVista\nT,  |U|,  alpha,  liquid/vapour interface", fillcolor=PHYS)

n.node("TARGET","Validation target  (your data)\nmeasured 42-plain boiling curve + CHF 65 W/cm2", fillcolor=RES)
n.node("CALIB", "Calibrate coeffC / coeffE  vs measured curve + CHF\n"
                "outer optimisation loop\n"
                "** HPC campaign -- NOT done **", fillcolor=FIT)

n.node("STATUS","STATUS:  unconverged DEMONSTRATION\n"
                "coarse, single-core, 0.8 ms, uncalibrated\n"
                "non-physical field spikes (T -> 610 K vs 358 K BC)\n"
                "NOT validated -- needs refined mesh + calibration + HPC convergence",
       fillcolor=STAT)

for a, b in [("GEO","BM"),("BM","SFE"),("SFE","SHM"),("SHM","TS"),("TS","SF"),
             ("SF","RUN"),("GOV","RUN"),("PROP2","RUN"),("BC","RUN"),
             ("RUN","POST"),("POST","STATUS")]:
    n.edge(a, b)
n.edge("POST","CALIB", style="dashed")
n.edge("TARGET","CALIB", style="dashed")
n.edge("CALIB","RUN", label="adjust coeffs, re-run", style="dashed", color="#d79b00")

n.attr(dpi="160")
n.render("/home/claude/diagrams/numerical_study_map", cleanup=True)
n.format = "pdf"; n.render("/home/claude/diagrams/numerical_study_map", cleanup=True)
print("diagram 2 done")
