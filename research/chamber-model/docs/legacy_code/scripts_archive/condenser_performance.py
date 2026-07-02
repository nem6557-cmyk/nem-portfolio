"""
Condenser performance + 3D flow-distribution views on the REAL geometry.
Coolant water ~40 C at 4 L/min total, condensation at 12 kPa (T_sat 49.4 C).
Uses the centered-inlet per-column flow split from flow_manifold.py.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gmsh
import condenser_solver as cs
from condenser_solver import Geometry, Operating, Mesh

OD, ID, LT = 4.76e-3, 3.137e-3, 0.095
QTOT_LPM = 4.0
col_flow = np.load("/home/claude/col_flow.npy")      # m3/s per column (centered inlet)
COL_X = np.load("/home/claude/col_x.npy")            # mm

# ---- tube positions from STEP ----
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.open("/mnt/user-data/uploads/CFD_Next_Gen.step"); gmsh.model.occ.synchronize()
tubes = []
for (dim, tag) in gmsh.model.getEntities(3):
    bb = gmsh.model.getBoundingBox(dim, tag)
    sig = (round(bb[3]-bb[0],1), round(bb[4]-bb[1],1), round(bb[5]-bb[2],1))
    if sig == (5.6, 95.0, 5.6):
        tubes.append(((bb[0]+bb[3])/2, bb[1], bb[4], (bb[2]+bb[5])/2))  # cx,y0,y1,cz (mm)
gmsh.finalize()
tubes = np.array(tubes)
cx, cz = tubes[:,0], tubes[:,3]

# ---- map per-column flow to per-tube flow ----
col_assign = np.array([np.argmin(np.abs(COL_X - x)) for x in cx])
counts = np.array([np.sum(col_assign == k) for k in range(len(COL_X))])
tube_flow = np.array([col_flow[k]/counts[k] for k in col_assign])      # m3/s per tube
tube_flow_Lmin = tube_flow*1000*60

# ---- surface areas ----
A_int = np.pi*ID*LT*len(tubes); A_ext = np.pi*OD*LT*len(tubes)

# ---- condenser performance via verified solver (mean + min + max flow tube) ----
def run(qLmin):
    geo = Geometry(r_i=ID/2, r_o=OD/2, L=LT, k_wall=385.0, n_tubes=len(tubes))
    op = Operating(Q_per_tube_Lmin=qLmin, T_in=40+273.15, P_kPa=12.0,
                   T_sat=49.4+273.15, cond_model="nusselt_tube")
    return cs.solve_with_nusselt(geo, op, Mesh(n_rf=16, n_rw=8, n_z=120))

q_mean = QTOT_LPM/len(tubes)
r_mean = run(q_mean); r_lo = run(tube_flow_Lmin.min()); r_hi = run(tube_flow_Lmin.max())
bk = cs.bank_duty(r_mean, Geometry(r_i=ID/2, r_o=OD/2, L=LT, n_tubes=len(tubes)))

# tube-side pressure drop (Hagen-Poiseuille at mean flow) + manifold total from flow model
MU, RHO = 6.53e-4, 992.0
dP_tube = 128*MU*LT*(q_mean/1000/60)/(np.pi*ID**4)

print("="*66)
print(f"CONDENSER PERFORMANCE — real geometry, {QTOT_LPM} L/min, water/40C, 12 kPa")
print("="*66)
print(f"Tubes: {len(tubes)}  OD {OD*1e3:.2f} / ID {ID*1e3:.3f} mm, L {LT*1e3:.0f} mm, copper")
print(f"Surface area  : internal {A_int*1e4:.1f} cm^2,  external {A_ext*1e4:.1f} cm^2")
print(f"Flow/tube     : mean {q_mean:.4f} L/min ({tube_flow_Lmin.min():.4f}-{tube_flow_Lmin.max():.4f} across bank)")
print(f"Pressure drop : tube-side {dP_tube:.1f} Pa; manifold+tubes inlet->outlet ~53.7 Pa")
print(f"Reynolds      : {r_mean['Re']:.0f} (laminar)")
print(f"\nEffectiveness-NTU (condensing mode, Nusselt film):")
print(f"   effectiveness e : {r_mean['eps']:.4f}   (range {r_lo['eps']:.4f}-{r_hi['eps']:.4f} across tubes)")
print(f"   NTU             : {r_mean['NTU']:.4f}   (range {r_hi['NTU']:.4f}-{r_lo['NTU']:.4f})")
print(f"   UA              : {r_mean['UA']*1e3:.2f} mW/K per tube")
print(f"\nDuty & resistance:")
print(f"   duty per tube   : {r_mean['Q_ext']:.2f} W   (bank w/ inundation {bk['Q_bank']:.0f} W)")
print(f"   condensation HTC: {np.mean(r_mean['h_ext_field']):.0f} W/m^2K")
print(f"   condensate rate : {bk['mdot_cond_bank']*1e3:.3f} g/s (bank)")
print(f"   coolant outlet  : {r_mean['T_out']-273.15:.2f} C  (rise {r_mean['T_out']-(40+273.15):.2f} K)")
print(f"   system R        : {(49.4+273.15-(40+273.15))/bk['Q_bank']:.4f} K/W")
print("="*66)
print("Note: ε-NTU above is condensing-mode (all tubes see vapor). At 40% fill ~13 of")
print("33 tubes are submerged and run pool-side natural convection instead; the coupled")
print("chamber run applies the per-tube regime split.")

# ====================== 3D views colored by manifold flow distribution ======================
col_flow_mlmin = col_flow[col_assign] * 6e7          # column flow per tube [mL/min]
norm = plt.Normalize(col_flow_mlmin.min(), col_flow_mlmin.max())
cmap = plt.cm.turbo
th = np.linspace(0, 2*np.pi, 18); r = OD/2*1e3

def draw(ax):
    for (xx, y0, y1, zz), q in zip(tubes, col_flow_mlmin):
        Y, TH = np.meshgrid([y0, y1], th)
        X = xx + r*np.cos(TH); Z = zz + r*np.sin(TH)
        ax.plot_surface(X, Y, Z, color=cmap(norm(q)), linewidth=0, antialiased=False, shade=False)
    ax.set_box_aspect((np.ptp(tubes[:,0])+10, 95, np.ptp(tubes[:,3])+10))

fig = plt.figure(figsize=(15, 11))
views = [("isometric", 22, -60), ("top (X-Y)", 89, -90),
         ("front (X-Z)", 2, -90), ("side (Y-Z)", 2, 0)]
for k, (name, el, az) in enumerate(views, 1):
    ax = fig.add_subplot(2, 2, k, projection="3d")
    draw(ax); ax.view_init(elev=el, azim=az)
    ax.set_title(f"{name}", fontsize=11)
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
cb = fig.colorbar(sm, ax=fig.axes, shrink=0.6, pad=0.02)
cb.set_label("column (manifold) flow per tube [mL/min]")
fig.suptitle(f"Tube-bank flow distribution (centered inlet, {QTOT_LPM} L/min) — "
             f"columns {col_flow_mlmin.min():.0f}–{col_flow_mlmin.max():.0f} mL/min, center-fed", fontsize=13)
fig.savefig("/home/claude/bank_flow_3d.png", dpi=140, bbox_inches="tight"); plt.close(fig)

# ε-NTU curve with operating point
fig, ax = plt.subplots(figsize=(7, 5))
ntu = np.linspace(0, max(2.0, r_mean['NTU']*1.6), 200)
ax.plot(ntu, 1-np.exp(-ntu), lw=2, label="ε = 1 − e^(−NTU)")
ax.plot(r_mean['NTU'], r_mean['eps'], "ro", ms=10, label="operating point (4 L/min)")
ax.set_xlabel("NTU = UA / (ṁ cp)"); ax.set_ylabel("effectiveness ε")
ax.set_title("Condenser effectiveness — real geometry"); ax.legend(); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig("/home/claude/condenser_eps_ntu.png", dpi=140); plt.close(fig)
print("\nfigures: bank_flow_3d.png, condenser_eps_ntu.png")
