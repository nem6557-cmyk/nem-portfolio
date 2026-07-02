"""
Three-way condenser comparison from REAL STEP geometry, with the measured
layout-factor trend.
=====================================================================
Designs (tube positions + sizes read directly from the uploaded STEP files):
    33-tube  OD4.76 / ID3.137 / L95     (open,     CFD_Next_Gen.step)
    42-tube  OD3.175/ ID1.39  / L62.6    (confined, Heat_Exchanger_Design_3.step) <- validated
    66-tube  OD2.0  / ID1.6   / L95      (open,     Full_Assembly_..._66_Tubes.step)

Single-phase coolant hydraulics (Hagen-Poiseuille per tube, equal split) plus the
verified condensing-mode condenser solver (Nusselt film). Then the GEOMETRIC
condenser-side resistance is compared with the MEASURED effective resistance via
the layout factor f = R_effective / R_geometric calibrated in the reduced-order model:
    33-tube  f = 0.78  (measured, open)
    42-tube  f = 1.63  (measured, confined)
    66-tube  f = 0.78  (ASSUMED open -- forecast, no validation data)
The trend (f vs a confinement metric) is the speculative contribution: tighter
packing departs further from the ideal developing-laminar estimate.

Reduced-physics (analytical) study -- NOT OpenFOAM CFD. Run from scripts_archive/.
"""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gmsh
import condenser_solver as cs
import evaporator_solver as ev
from condenser_solver import Geometry, Operating, Mesh

MU, RHO, CP, KW = 6.53e-4, 992.0, 4178.0, 385.0
QTOT = 4.0/1000/60        # m3/s total coolant
TIN_C, TSAT_C = 40.0, 49.4
g = 9.81
water = ev.WATER_12kPa
import os
_here=os.path.dirname(os.path.abspath(__file__))
UP=next((d for d in [os.path.join(_here,"..","geometry"),"/mnt/user-data/uploads"] if os.path.isdir(d)),"/mnt/user-data/uploads")

# design table: file, signature, tube axis, OD, ID, L, measured layout factor, factor source
DES = {
 "33-tube\nOD4.76 open": dict(step=f"{UP}/CFD_Next_Gen.step",        sig=(5.6,95.0,5.6),  ax="y",
                              OD=4.76e-3, ID=3.137e-3, N=33, L=0.095,  f=0.78, fsrc="measured"),
 "42-tube\nOD3.18 confined": dict(step=f"{UP}/Heat_Exchanger_Design_3.step", sig=(62.6,3.2,3.2), ax="x",
                              OD=3.175e-3,ID=1.39e-3,  N=42, L=0.0626, f=1.63, fsrc="measured"),
 "66-tube\nOD2.0 open": dict(step=f"{UP}/Full_Assembly_V1_2mm_OD_66_Tubes.step", sig=(2.0,95.0,2.0), ax="y",
                              OD=2.0e-3,  ID=1.6e-3,   N=66, L=0.095,  f=0.78, fsrc="assumed (forecast)"),
}

def extract(step, sig, ax):
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal",0)
    gmsh.open(step); gmsh.model.occ.synchronize()
    pos=[]
    for (d,t) in gmsh.model.getEntities(3):
        bb=gmsh.model.getBoundingBox(d,t)
        s=(round(bb[3]-bb[0],1),round(bb[4]-bb[1],1),round(bb[5]-bb[2],1))
        if s==sig:
            if ax=="y": pos.append(((bb[0]+bb[3])/2,(bb[2]+bb[5])/2))   # (x,z)
            else:       pos.append(((bb[1]+bb[4])/2,(bb[2]+bb[5])/2))   # (y,z)
    gmsh.finalize()
    return np.array(pos)

def nn_pitch(pos):
    """min nearest-neighbour centre distance [mm]."""
    d=np.inf
    for i in range(len(pos)):
        for j in range(i+1,len(pos)):
            d=min(d,np.hypot(*(pos[i]-pos[j])))
    return d

R={}
for name,p in DES.items():
    OD,ID,N,L = p["OD"],p["ID"],p["N"],p["L"]
    pos = extract(p["step"], p["sig"], p["ax"])
    pitch = nn_pitch(pos)                      # mm
    # hydraulics (equal split)
    A_flow=N*np.pi/4*ID**2; q=QTOT/N; v=q/(np.pi/4*ID**2); Re=RHO*v*ID/MU
    dP=128*MU*L*q/(np.pi*ID**4); Ppump=dP*QTOT
    A_int=N*np.pi*ID*L; A_ext=N*np.pi*OD*L
    # condensing-mode thermal (per tube) -> geometric condenser resistance
    geo=Geometry(r_i=ID/2,r_o=OD/2,L=L,k_wall=KW,n_tubes=1)
    op=Operating(Q_per_tube_Lmin=q*1000*60,T_in=TIN_C+273.15,P_kPa=12.0,
                 T_sat=TSAT_C+273.15,cond_model="nusselt_tube")
    rc=cs.solve_with_nusselt(geo,op,Mesh(14,6,100))
    UA_tube=rc["UA"]; R_geo=1.0/(UA_tube*N)          # K/W, N tubes in parallel
    R_eff=R_geo*p["f"]                                # measured effective resistance
    R[name]=dict(OD=OD,ID=ID,N=N,L=L,pitch=pitch,pitchOD=pitch/(OD*1e3),
        A_flow=A_flow,v=v,Re=Re,dP=dP,Ppump=Ppump,A_int=A_int,A_ext=A_ext,
        eps=rc["eps"],NTU=rc["NTU"],h_cond=np.mean(rc["h_ext_field"]),
        Qtube=rc["Q_ext"],Qbank=rc["Q_ext"]*N,R_geo=R_geo,R_eff=R_eff,
        f=p["f"],fsrc=p["fsrc"],pos=pos)

# ---------------- console table ----------------
names=list(R.keys()); cols=[R[n] for n in names]
def row(lbl, key, fmt="{:.3g}", scale=1.0):
    vals="".join(f"{fmt.format(c[key]*scale):>15s}" for c in cols)
    print(f"  {lbl:30s}{vals}")
print("="*76)
print(f"{'THREE-WAY CONDENSER COMPARISON (real STEP geometry, 4 L/min, water/40C/12kPa)':^76}")
print("="*76)
print(f"  {'design':30s}"+"".join(f"{n.split(chr(10))[0]:>15s}" for n in names))
print("-"*76)
row("tubes","N","{:.0f}"); row("OD [mm]","OD","{:.2f}",1e3); row("ID [mm]","ID","{:.3f}",1e3)
row("tube length [mm]","L","{:.1f}",1e3)
row("nearest pitch [mm]","pitch","{:.2f}"); row("pitch/OD (confinement)","pitchOD","{:.2f}")
print("-"*76)
row("coolant flow area [mm^2]","A_flow","{:.1f}",1e6)
row("tube velocity [m/s]","v","{:.3f}"); row("Reynolds","Re","{:.0f}")
row("pressure drop/tube [Pa]","dP","{:.1f}"); row("pumping power [mW]","Ppump","{:.2f}",1e3)
print("-"*76)
row("external area [cm^2]","A_ext","{:.0f}",1e4)
row("condensation HTC [W/m2K]","h_cond","{:.0f}")
row("effectiveness eps","eps","{:.3f}"); row("NTU","NTU","{:.3f}")
row("bank duty [W]","Qbank","{:.0f}")
print("-"*76)
row("geometric R_cond [K/W]","R_geo","{:.4f}")
row("layout factor f","f","{:.2f}")
row("effective R_cond [K/W]","R_eff","{:.4f}")
print("="*76)
print("  layout factor source: "+", ".join(f"{n.split(chr(10))[0]} {c['fsrc']}" for n,c in zip(names,cols)))
print("="*76)

# ---------------- figure 1: bar comparison ----------------
short=[n.replace("\n","\n") for n in names]; bcol=["#3b7dd8","#d8633b","#5caa55"]
fig,ax=plt.subplots(2,3,figsize=(14,8))
def bars(a,key,title,unit,scale=1.0,fmt="{:.1f}"):
    vals=[c[key]*scale for c in cols]
    a.bar(short,vals,color=bcol); a.set_title(title,fontsize=10); a.set_ylabel(unit)
    for i,v in enumerate(vals): a.text(i,v,fmt.format(v),ha="center",va="bottom",fontsize=8)
    a.tick_params(axis="x",labelsize=7)
bars(ax[0,0],"A_ext","External (condensing) area","cm²",1e4)
bars(ax[0,1],"A_flow","Coolant flow area","mm²",1e6)
bars(ax[0,2],"v","Tube velocity","m/s",1,"{:.3f}")
bars(ax[1,0],"dP","Pressure drop / tube","Pa")
bars(ax[1,1],"h_cond","Condensation HTC","W/m²K",1,"{:.0f}")
bars(ax[1,2],"Qbank","Bank condensing duty","W",1,"{:.0f}")
fig.suptitle("Condenser comparison from real geometry — 33 / 42 / 66 tube, 4 L/min",fontsize=13)
fig.tight_layout(rect=[0,0,1,0.96]); fig.savefig("/home/claude/condenser_compare_3way.png",dpi=140); plt.close(fig)

# ---------------- figure 2: geometric vs measured-effective resistance ----------------
# The honest result: per-tube geometry (pitch/OD, areas) does NOT explain the layout factor.
# The confined 42-tube's effective resistance sits well ABOVE its geometric value; the open
# 33/66 bundles sit BELOW theirs. That deviation is a chamber-level drainage/circulation effect,
# i.e. the gap that CFD (manifold maldistribution; pool-side drainage) would resolve.
fig,(ax1,ax2)=plt.subplots(1,2,figsize=(13,5.4))
x=np.arange(len(names)); w=0.36
Rg=[c["R_geo"]*1e3 for c in cols]; Re=[c["R_eff"]*1e3 for c in cols]
ax1.bar(x-w/2,Rg,w,label="geometric R (developing-laminar)",color="#9aa0a6")
ax1.bar(x+w/2,Re,w,label="effective R (measured layout factor)",color="#c0392b")
for i,c in enumerate(cols):
    ax1.text(i+w/2, c["R_eff"]*1e3, f"×{c['f']:.2f}", ha="center", va="bottom", fontsize=9,
             color=("#c0392b" if c["f"]>1 else "#1e7d34"))
ax1.set_xticks(x); ax1.set_xticklabels([n.split(chr(10))[0] for n in names])
ax1.set_ylabel("condenser-side resistance [mK/W]")
ax1.set_title("Geometry under-predicts the confined bundle\n(42-tube f>1 penalty; open bundles f<1)")
ax1.legend(fontsize=8); ax1.grid(alpha=0.3,axis="y")
# right: layout factor vs pitch/OD, shown precisely to make the NON-correlation explicit
for n,c in zip(names,cols):
    meas=c["fsrc"].startswith("measured")
    ax2.scatter(c["pitchOD"],c["f"],s=150,zorder=3,color="#c0392b" if meas else "#9aa0a6",
                edgecolor="k",marker="o" if meas else "s")
    ax2.annotate(n.split(chr(10))[0]+("" if meas else " (forecast)"),(c["pitchOD"],c["f"]),
                 textcoords="offset points",xytext=(8,6),fontsize=9)
ax2.axhline(1.0,ls="--",color="#2c3e50",lw=1); ax2.set_ylim(0,1.9)
ax2.set_xlabel("pitch / OD"); ax2.set_ylabel("measured layout factor f")
ax2.set_title("f is NOT explained by tube pitch/OD\n(confinement penalty is a chamber/drainage effect)")
ax2.grid(alpha=0.3)
fig.suptitle("Layout factor vs geometry: the confined-42 penalty needs CFD, not per-tube metrics",fontsize=12)
fig.tight_layout(rect=[0,0,1,0.95]); fig.savefig("/home/claude/condenser_layout_trend.png",dpi=150); plt.close(fig)
print("\nfigures: condenser_compare_3way.png, condenser_layout_trend.png")
