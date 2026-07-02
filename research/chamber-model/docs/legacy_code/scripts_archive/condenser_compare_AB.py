"""
Condenser design comparison: A (33 x OD4.76/ID3.137) vs B (66 x OD2.0/ID1.6).
Same 95 mm length, same chip, same 4 L/min total coolant, water/12 kPa/40 C.
Runs both through the identical flow + condenser pipeline.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gmsh
import condenser_solver as cs
import evaporator_solver as ev
from condenser_solver import Geometry, Operating, Mesh

MU, RHO, CP, KW = 6.53e-4, 992.0, 4178.0, 385.0
QTOT = 4.0/1000/60        # m3/s
TIN_C, TSAT_C = 40.0, 49.4
g = 9.81
water = ev.WATER_12kPa

def extract(step, sigxy):
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal",0)
    gmsh.open(step); gmsh.model.occ.synchronize()
    tubes=[]; cav=(0.0,15.0)
    for (d,t) in gmsh.model.getEntities(3):
        bb=gmsh.model.getBoundingBox(d,t)
        s=(round(bb[3]-bb[0],1),round(bb[4]-bb[1],1),round(bb[5]-bb[2],1))
        if s==sigxy: tubes.append(((bb[0]+bb[3])/2,bb[1],bb[4],(bb[2]+bb[5])/2))
        if s[0]==95.0 and s[1]==95.0: cav=(bb[2],bb[5])   # cavity z-floor, z-ceiling
    gmsh.finalize()
    return np.array(tubes), cav

def wet_frac(zc,r,zf):
    d=zf-zc
    if d>=r: return 1.0
    if d<=-r: return 0.0
    return 1.0-(r*r*np.arccos(d/r)-d*np.sqrt(r*r-d*d))/(np.pi*r*r)

def churchill_chu_h(dT,OD):
    nu=water.mu_l/water.rho_l; al=water.k_l/(water.rho_l*water.cp_l); Pr=nu/al
    Ra=g*water.beta_exp*max(dT,0.5)*OD**3/(nu*al)
    return (0.6+0.387*Ra**(1/6)/(1+(0.559/Pr)**(9/16))**(8/27))**2*water.k_l/OD

designs = {
 "A: 33 × OD4.76": dict(step="/mnt/user-data/uploads/CFD_Next_Gen.step",
                        sig=(5.6,95.0,5.6), OD=4.76e-3, ID=3.137e-3, N=33),
 "B: 66 × OD2.0":  dict(step="/mnt/user-data/uploads/Full_Assembly_V1_2mm_OD_66_Tubes.step",
                        sig=(2.0,95.0,2.0), OD=2.0e-3, ID=1.6e-3, N=66),
}

R = {}
for name, p in designs.items():
    OD,ID,N,L = p["OD"],p["ID"],p["N"],0.095
    tubes,cav = extract(p["step"], p["sig"])
    # hydraulics
    A_flow = N*np.pi/4*ID**2
    q_tube = QTOT/N
    v = q_tube/(np.pi/4*ID**2)
    Re = RHO*v*ID/MU
    dP = 128*MU*L*q_tube/(np.pi*ID**4)          # Hagen-Poiseuille per tube
    Ppump = dP*QTOT
    A_int = N*np.pi*ID*L; A_ext = N*np.pi*OD*L
    # condenser thermal (condensing mode)
    geo=Geometry(r_i=ID/2,r_o=OD/2,L=L,k_wall=KW,n_tubes=1)
    op=Operating(Q_per_tube_Lmin=q_tube*1000*60,T_in=TIN_C+273.15,P_kPa=12.0,
                 T_sat=TSAT_C+273.15,cond_model="nusselt_tube")
    rc=cs.solve_with_nusselt(geo,op,Mesh(14,6,100))
    h_cond=np.mean(rc["h_ext_field"])
    # submerged fraction at 40% fill (referenced to cavity floor)
    zf = cav[0] + 0.40*(cav[1]-cav[0])
    fr = np.array([wet_frac(zc, OD/2*1e3, zf) for zc in tubes[:,3]])
    f_sub = fr.mean()
    # coupled capacity
    mc = rc["mdot"]*rc["cp"]
    eps_sub = cs.solve_field(geo, Operating(Q_per_tube_Lmin=q_tube*1000*60,
              T_in=TIN_C+273.15,T_sat=TSAT_C+273.15,cond_model="constant_h",
              h_ext_const=churchill_chu_h(5.0,OD)), Mesh(14,6,100))["eps"]
    dTmax=TSAT_C-TIN_C
    Q_lat=N*(1-f_sub)*rc["Q_ext"]
    Q_sens=N*f_sub*mc*eps_sub*dTmax
    R[name]=dict(OD=OD,ID=ID,N=N,wall=(OD-ID)/2,A_flow=A_flow,v=v,Re=Re,dP=dP,
        Ppump=Ppump,A_int=A_int,A_ext=A_ext,eps=rc["eps"],NTU=rc["NTU"],UA=rc["UA"],
        Qtube=rc["Q_ext"],h_cond=h_cond,Qbank=rc["Q_ext"]*N,f_sub=f_sub,
        Qcap=Q_lat+Q_sens,tubes=tubes,zf=zf)

# ---------------- comparison table ----------------
A,B = R["A: 33 × OD4.76"], R["B: 66 × OD2.0"]

print("="*74)
print(f"{'CONDENSER DESIGN COMPARISON':^74}")
print(f"{'(water, 12 kPa, 40 C inlet, 4 L/min, 95 mm tubes)':^74}")
print("="*74)
print(f"  {'metric':30s} {'A 33×4.76':>12s} {'B 66×2.0':>12s}   B/A")
print("-"*74)
print(f"  {'tube count':30s} {A['N']:>12.0f} {B['N']:>12.0f}   {B['N']/A['N']:.2f}x")
print(f"  {'OD / ID / wall [mm]':30s} {A['OD']*1e3:>4.2f}/{A['ID']*1e3:.2f}/{A['wall']*1e3:.2f}      "
      f"{B['OD']*1e3:.2f}/{B['ID']*1e3:.2f}/{B['wall']*1e3:.2f}")
print(f"  {'internal area [cm^2]':30s} {A['A_int']*1e4:>12.0f} {B['A_int']*1e4:>12.0f}   {B['A_int']/A['A_int']:.2f}x")
print(f"  {'external area [cm^2]':30s} {A['A_ext']*1e4:>12.0f} {B['A_ext']*1e4:>12.0f}   {B['A_ext']/A['A_ext']:.2f}x")
print(f"  {'total flow area [mm^2]':30s} {A['A_flow']*1e6:>12.1f} {B['A_flow']*1e6:>12.1f}   {B['A_flow']/A['A_flow']:.2f}x")
print("-"*74)
print(f"  {'tube velocity [m/s]':30s} {A['v']:>12.3f} {B['v']:>12.3f}   {B['v']/A['v']:.2f}x")
print(f"  {'Reynolds':30s} {A['Re']:>12.0f} {B['Re']:>12.0f}   {B['Re']/A['Re']:.2f}x")
print(f"  {'pressure drop / tube [Pa]':30s} {A['dP']:>12.1f} {B['dP']:>12.1f}   {B['dP']/A['dP']:.2f}x")
print(f"  {'pumping power [mW]':30s} {A['Ppump']*1e3:>12.2f} {B['Ppump']*1e3:>12.2f}   {B['Ppump']/A['Ppump']:.2f}x")
print("-"*74)
print(f"  {'condensation HTC [W/m2K]':30s} {A['h_cond']:>12.0f} {B['h_cond']:>12.0f}   {B['h_cond']/A['h_cond']:.2f}x")
print(f"  {'effectiveness e':30s} {A['eps']:>12.3f} {B['eps']:>12.3f}   {B['eps']/A['eps']:.2f}x")
print(f"  {'NTU':30s} {A['NTU']:>12.3f} {B['NTU']:>12.3f}   {B['NTU']/A['NTU']:.2f}x")
print(f"  {'duty / tube [W]':30s} {A['Qtube']:>12.2f} {B['Qtube']:>12.2f}   {B['Qtube']/A['Qtube']:.2f}x")
print(f"  {'bank duty (all cond) [W]':30s} {A['Qbank']:>12.0f} {B['Qbank']:>12.0f}   {B['Qbank']/A['Qbank']:.2f}x")
print(f"  {'submerged frac @40% fill':30s} {A['f_sub']:>12.2f} {B['f_sub']:>12.2f}")
print(f"  {'coupled capacity [W]':30s} {A['Qcap']:>12.0f} {B['Qcap']:>12.0f}   {B['Qcap']/A['Qcap']:.2f}x")
print("="*74)

# ---------------- comparison figure ----------------
fig, ax = plt.subplots(2, 3, figsize=(14, 8))
labels=["A\n33×4.76","B\n66×2.0"]; cols=["#3b7dd8","#d8633b"]
def bars(a, va, vb, title, unit):
    a.bar(labels,[va,vb],color=cols); a.set_title(title,fontsize=10); a.set_ylabel(unit)
    for i,v in enumerate([va,vb]): a.text(i,v,f"{v:.1f}" if v>=1 else f"{v:.3f}",ha="center",va="bottom",fontsize=9)
bars(ax[0,0], A['A_ext']*1e4, B['A_ext']*1e4, "External (condensing) area", "cm²")
bars(ax[0,1], A['A_flow']*1e6, B['A_flow']*1e6, "Coolant flow area", "mm²")
bars(ax[0,2], A['v'], B['v'], "Tube velocity", "m/s")
bars(ax[1,0], A['dP'], B['dP'], "Pressure drop / tube", "Pa")
bars(ax[1,1], A['h_cond'], B['h_cond'], "Condensation HTC", "W/m²K")
bars(ax[1,2], A['Qcap'], B['Qcap'], "Coupled chamber capacity", "W")
fig.suptitle("Condenser design comparison — fewer large tubes (A) vs many small tubes (B), 4 L/min",fontsize=13)
fig.tight_layout(rect=[0,0,1,0.96]); fig.savefig("/home/claude/compare_AB.png",dpi=140); plt.close(fig)

# ---------------- 3D view of design B ----------------
tubes=B["tubes"]; OD=B["OD"]
fig=plt.figure(figsize=(9,7)); axx=fig.add_subplot(111,projection="3d")
th=np.linspace(0,2*np.pi,16); r=OD/2*1e3
for (xx,y0,y1,zz) in tubes:
    Y,TH=np.meshgrid([y0,y1],th); X=xx+r*np.cos(TH); Z=zz+r*np.sin(TH)
    sub = zz < B["zf"]
    axx.plot_surface(X,Y,Z,color="#1f77b4" if sub else "#9aa0a6",linewidth=0,antialiased=False,shade=True)
axx.set_box_aspect((np.ptp(tubes[:,0])+6,95,np.ptp(tubes[:,3])+6))
axx.view_init(elev=20,azim=-60); axx.set_xlabel("X"); axx.set_ylabel("Y"); axx.set_zlabel("Z")
axx.set_title(f"Design B — 66 × OD2.0 mm staggered bank (blue submerged @40% fill)")
fig.tight_layout(); fig.savefig("/home/claude/designB_3d.png",dpi=140); plt.close(fig)
print("figures: compare_AB.png, designB_3d.png")
