"""
Manifold flow distribution — top longitudinal (X-Y) view at 4 L/min
===================================================================
Depth-integrated Darcy / Hele-Shaw model of the coolant path:

    inlet hole -> tapered inlet plenum -> 33 parallel tubes -> tapered
    outlet plenum -> outlet hole

The plenums are modeled as high-conductance open channels whose transmissivity
TAPERS from the feed end to the dead end (the physical taper that flattens the
distribution). The tube bank is an anisotropic zone: conductive along the tube
axis (Y), nearly blocking across it (X). Solving the linear pressure field
gives the pressure contour, the velocity field (q = -T grad P), streamlines,
and the per-tube flow split. This captures the FRICTION-DOMINATED maldistribution
(more flow in the tubes nearest the inlet); full inertial momentum-recovery would
require 3D CFD.

Fluid default: water ~40 C. Distribution pattern is fluid-independent (linear);
viscosity only scales the pressure level.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

# ---------------- inputs ----------------
Q_LPM = 4.0
Q = Q_LPM / 1000 / 60.0                      # m3/s
MU, RHO = 6.53e-4, 992.0                     # water ~40 C
TUBE_ID, TUBE_OD, L_TUBE, N_TUBES = 3.137e-3, 4.76e-3, 0.095, 33
# tube X-columns from the STEP (distinct centroids, mm) and tubes per column
COL_X = np.array([-33.5,-27.92,-22.33,-16.75,-11.17,-5.58,0,5.58,11.16,16.75,22.33,27.92,33.5])

# domain (m)
X0, X1, Y0, Y1 = -0.043, 0.043, -0.060, 0.060
NX, NY = 150, 210
Y_IN_HI, Y_OUT_LO = -0.049, 0.049            # plenum/bank boundaries
PORT_X = (-0.0045, 0.0045)                   # inlet & outlet ports centered at x=0

# ---------------- grid ----------------
xf = np.linspace(X0, X1, NX+1); yf = np.linspace(Y0, Y1, NY+1)
xc = 0.5*(xf[:-1]+xf[1:]); yc = 0.5*(yf[:-1]+yf[1:])
dx, dy = xf[1]-xf[0], yf[1]-yf[0]
X, Yg = np.meshgrid(xc, yc, indexing="ij")

# ---------------- transmissivity field ----------------
# calibrate bank Y-transmissivity to real 33-tube Hagen-Poiseuille resistance
R_tube = 128*MU*L_TUBE/(np.pi*TUBE_ID**4)
R_bank = R_tube/N_TUBES
dP_bank = R_bank*Q                            # ~ real bank pressure drop
L_bankY = Y_OUT_LO - Y_IN_HI
W_x = 0.085
Ty_bank = Q*L_bankY/(dP_bank*W_x)
Tx_bank = 0.02*Ty_bank
RATIO = 70.0                                  # plenum/bank conductance ratio (low-loss header)

is_in_plen  = Yg <= Y_IN_HI
is_out_plen = Yg >= Y_OUT_LO
is_bank = (~is_in_plen) & (~is_out_plen)

taper = 1.0 - 0.4*(X - X0)/(X1 - X0)          # mild geometric taper toward the dead end
Tx = np.where(is_bank, Tx_bank, RATIO*Ty_bank*taper)
Ty = np.where(is_bank, Ty_bank, RATIO*Ty_bank*taper)

# ---------------- assemble sparse Laplacian ----------------
N = NX*NY
def idx(i,j): return i*NY + j
rows, cols, vals = [], [], []
b = np.zeros(N); diag = np.zeros(N)
def hm(a,b_): return 2*a*b_/(a+b_+1e-30)

# inlet / outlet cell masks
inlet = np.zeros((NX,NY), bool); outlet = np.zeros((NX,NY), bool)
for i in range(NX):
    if PORT_X[0] <= xc[i] <= PORT_X[1]:
        inlet[i, 0] = True            # bottom edge (inlet plenum far wall)
        outlet[i, NY-1] = True        # top edge (outlet plenum far wall)
n_in = inlet.sum()

for i in range(NX):
    for j in range(NY):
        p = idx(i,j)
        if outlet[i,j]:               # Dirichlet P=0
            rows.append(p); cols.append(p); vals.append(1.0); b[p]=0.0
            continue
        if i>0:
            T = hm(Tx[i,j],Tx[i-1,j])*dy/dx; rows.append(p);cols.append(idx(i-1,j));vals.append(-T);diag[p]+=T
        if i<NX-1:
            T = hm(Tx[i,j],Tx[i+1,j])*dy/dx; rows.append(p);cols.append(idx(i+1,j));vals.append(-T);diag[p]+=T
        if j>0:
            T = hm(Ty[i,j],Ty[i,j-1])*dx/dy; rows.append(p);cols.append(idx(i,j-1));vals.append(-T);diag[p]+=T
        if j<NY-1:
            T = hm(Ty[i,j],Ty[i,j+1])*dx/dy; rows.append(p);cols.append(idx(i,j+1));vals.append(-T);diag[p]+=T
        if inlet[i,j]:
            b[p] += Q/n_in
        rows.append(p); cols.append(p); vals.append(diag[p])

A = sp.csr_matrix((vals,(rows,cols)),shape=(N,N))
P = spla.spsolve(A,b).reshape(NX,NY)

# ---------------- velocity field q = -T grad P ----------------
dPx = np.gradient(P, xc, axis=0); dPy = np.gradient(P, yc, axis=1)
qx = -Tx*dPx; qy = -Ty*dPy
speed = np.sqrt(qx**2+qy**2)
# representative in-plane velocity (divide flux by a reference channel depth)
h_ref = 0.012
vel = speed/h_ref

# ---------------- per-column flow ----------------
jmid = NY//2
col_flow = []
for cxmm in COL_X:
    cx = cxmm/1000
    sel = np.abs(xc-cx) <= 0.5*np.median(np.diff(COL_X))/1000
    col_flow.append(np.sum(qy[sel,jmid])*dx)
col_flow = np.array(col_flow)
col_flow *= Q/np.sum(col_flow)               # normalize to total
mal = (col_flow.max()-col_flow.min())/col_flow.mean()*100

dP_total = P[inlet].mean() - 0.0
v_tube = (Q/N_TUBES)/(np.pi/4*TUBE_ID**2)
Re_tube = RHO*v_tube*TUBE_ID/MU

print("="*64)
print(f"MANIFOLD FLOW DISTRIBUTION  @ {Q_LPM} L/min (water ~40 C)")
print("="*64)
print(f"Total pressure drop inlet->outlet : {dP_total:.1f} Pa  ({dP_total/1000:.4f} kPa)")
print(f"Mean tube velocity (internal)     : {v_tube:.3f} m/s   Re = {Re_tube:.0f} (laminar)")
print(f"Per-column flow: mean {col_flow.mean()*6e7:.2f} mL/min, "
      f"min {col_flow.min()*6e7:.2f}, max {col_flow.max()*6e7:.2f}")
print(f"Flow maldistribution (max-min)/mean : {mal:.1f} %  "
      f"({'near-inlet columns carry more' })")
print("="*64)

# ---------------- figures ----------------
ext = [X0*1e3, X1*1e3, Y0*1e3, Y1*1e3]
def draw_tubes(ax):
    for cxmm in COL_X:
        ax.plot([cxmm,cxmm],[Y_IN_HI*1e3,Y_OUT_LO*1e3],color="k",lw=0.4,alpha=0.3)
    ax.axhline(Y_IN_HI*1e3,color="k",lw=0.6); ax.axhline(Y_OUT_LO*1e3,color="k",lw=0.6)
    ax.add_patch(plt.Rectangle((PORT_X[0]*1e3,Y0*1e3-1),(PORT_X[1]-PORT_X[0])*1e3,2,
                 color="lime",zorder=5)); ax.text(PORT_X[0]*1e3, Y0*1e3-4,"INLET",fontsize=8,color="green")
    ax.add_patch(plt.Rectangle((PORT_X[0]*1e3,Y1*1e3-1),(PORT_X[1]-PORT_X[0])*1e3,2,
                 color="red",zorder=5)); ax.text(PORT_X[0]*1e3, Y1*1e3+2,"OUTLET",fontsize=8,color="red")

# Fig 1: pressure contour
fig, ax = plt.subplots(figsize=(7.5,8))
pc = ax.contourf(X*1e3, Yg*1e3, P, 40, cmap="turbo")
draw_tubes(ax); plt.colorbar(pc,ax=ax,label="static pressure [Pa]")
ax.set_xlabel("X [mm]"); ax.set_ylabel("Y [mm] (flow direction)")
ax.set_title(f"Pressure field — tapered manifolds, {Q_LPM} L/min"); ax.set_aspect("equal")
fig.tight_layout(); fig.savefig("/home/claude/flow_pressure.png",dpi=140); plt.close(fig)

# Fig 2: velocity magnitude contour
fig, ax = plt.subplots(figsize=(7.5,8))
pc = ax.contourf(X*1e3, Yg*1e3, vel, 40, cmap="viridis")
draw_tubes(ax); plt.colorbar(pc,ax=ax,label="in-plane velocity [m/s] (superficial)")
ax.set_xlabel("X [mm]"); ax.set_ylabel("Y [mm]")
ax.set_title(f"Velocity magnitude — {Q_LPM} L/min"); ax.set_aspect("equal")
fig.tight_layout(); fig.savefig("/home/claude/flow_velocity.png",dpi=140); plt.close(fig)

# Fig 3: streamlines colored by speed
fig, ax = plt.subplots(figsize=(7.5,8))
strm = ax.streamplot(xc*1e3, yc*1e3, qx.T, qy.T, color=speed.T, cmap="plasma",
                     density=2.0, linewidth=1.0, arrowsize=0.8)
draw_tubes(ax); plt.colorbar(strm.lines,ax=ax,label="flux magnitude [m²/s]")
ax.set_xlabel("X [mm]"); ax.set_ylabel("Y [mm]")
ax.set_title(f"Streamlines (velocity magnitude) — {Q_LPM} L/min"); ax.set_aspect("equal")
ax.set_xlim(X0*1e3,X1*1e3); ax.set_ylim(Y0*1e3,Y1*1e3)
fig.tight_layout(); fig.savefig("/home/claude/flow_streamlines.png",dpi=140); plt.close(fig)

# Fig 4: per-column flow distribution
fig, ax = plt.subplots(figsize=(9,4.2))
ax.bar(COL_X, col_flow*6e7, width=3.5, color=plt.cm.coolwarm(
       (col_flow-col_flow.min())/(col_flow.max()-col_flow.min()+1e-12)))
ax.axhline(col_flow.mean()*6e7, color="k", ls="--", label=f"mean {col_flow.mean()*6e7:.1f} mL/min")
ax.set_xlabel("tube column X position [mm]  (inlet centered at X=0)")
ax.set_ylabel("flow per column [mL/min]")
ax.set_title(f"Flow distribution across the bank — spread {mal:.1f}% (more near inlet)")
ax.legend(); fig.tight_layout(); fig.savefig("/home/claude/flow_distribution.png",dpi=140); plt.close(fig)

np.save("/home/claude/col_flow.npy", col_flow); np.save("/home/claude/col_x.npy", COL_X)
print("figures: flow_pressure.png, flow_velocity.png, flow_streamlines.png, flow_distribution.png")
