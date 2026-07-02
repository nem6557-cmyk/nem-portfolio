"""
Floating-pressure coupled boiling curve: plain chip + each condenser.
Chamber saturation floats up from 12 kPa (anchored at q''=5 W/cm^2):
    T_sat(Q) = 49.4 C + (Q - Q5) * R_vapor          (condensation-side resistance)
Bulk pool warms toward saturation through the blended pool resistance:
    T_pool(Q) = 20 C + Q * R_pool   ->  subcooling = T_sat - T_pool
Surface temp tracks the floating saturation: T_surf = T_sat + dT_sat.
Boiling/CHF correlations use 12 kPa nominal water properties (the pressure
excursion over the credible range is modest; fully floating the properties
makes the empirical CHF correlation extrapolate unphysically). Floating
pressure is reported from CoolProp at the floating T_sat.
Better condenser -> lower R_vapor -> lower T_sat -> the T_surf curves separate.
"""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gmsh
from CoolProp.CoolProp import PropsSI
import condenser_solver as cs
import evaporator_solver as ev
from condenser_solver import Geometry, Operating, Mesh

A_CHIP = 34.5e-3*32.0e-3
TIN_C  = 20.0
TSAT0_C= 49.4
Q5     = 5.0*1e4*A_CHIP
QTOT   = 4.0/1000/60
RHO, CP= 998.0, 4182.0
C_cool = QTOT*RHO*CP
g = 9.81

def churchill_chu_h(dT, OD, fl):
    nu=fl.mu_l/fl.rho_l; al=fl.k_l/(fl.rho_l*fl.cp_l); Pr=nu/al
    Ra=g*fl.beta_exp*max(dT,0.5)*OD**3/(nu*al)
    return (0.6+0.387*Ra**(1/6)/(1+(0.559/Pr)**(9/16))**(8/27))**2*fl.k_l/OD

def extract_fsub(step, sig, OD):
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal",0)
    gmsh.open(step); gmsh.model.occ.synchronize()
    cz=[]; cav=(0.0,15.0)
    for (d,t) in gmsh.model.getEntities(3):
        bb=gmsh.model.getBoundingBox(d,t)
        s=(round(bb[3]-bb[0],1),round(bb[4]-bb[1],1),round(bb[5]-bb[2],1))
        if s==sig: cz.append((bb[2]+bb[5])/2)
        if s[0]==95.0 and s[1]==95.0: cav=(bb[2],bb[5])
    gmsh.finalize()
    zf=cav[0]+0.40*(cav[1]-cav[0]); r=OD/2*1e3
    def wf(zc):
        d=zf-zc
        if d>=r: return 1.0
        if d<=-r: return 0.0
        return 1.0-(r*r*np.arccos(d/r)-d*np.sqrt(r*r-d*d))/(np.pi*r*r)
    return float(np.mean([wf(z) for z in cz]))

def condenser_props(OD, ID, N, step, sig):
    fl0=ev.WATER_12kPa
    geo=Geometry(r_i=ID/2, r_o=OD/2, L=0.095, k_wall=385.0, n_tubes=1)
    mesh=Mesh(14,6,100)
    rc=cs.solve_with_nusselt(geo, Operating(Q_per_tube_Lmin=QTOT*1000*60/N,
        T_in=TIN_C+273.15, P_kPa=12.0, T_sat=TSAT0_C+273.15, cond_model="nusselt_tube"), mesh)
    eps_cond=rc["eps"]; h_cond=float(np.mean(rc["h_ext_field"]))
    eps_sub=cs.solve_field(geo, Operating(Q_per_tube_Lmin=QTOT*1000*60/N,
        T_in=TIN_C+273.15, T_sat=TSAT0_C+273.15, cond_model="constant_h",
        h_ext_const=churchill_chu_h(5.0,OD,fl0)), mesh)["eps"]
    f_sub=extract_fsub(step, sig, OD)
    eps_eff=(1-f_sub)*eps_cond + f_sub*eps_sub
    R_vapor=1.0/(C_cool*eps_cond)
    R_pool =1.0/(C_cool*eps_eff)
    return dict(R_vapor=R_vapor, R_pool=R_pool, h_cond=h_cond,
                eps_cond=eps_cond, eps_eff=eps_eff, f_sub=f_sub)

designs={
 "A: 33 x 4.76mm": dict(OD=4.76e-3, ID=3.137e-3, N=33,
    step="/mnt/user-data/uploads/CFD_Next_Gen.step", sig=(5.6,95.0,5.6)),
 "B: 66 x 2.0mm":  dict(OD=2.0e-3, ID=1.6e-3, N=66,
    step="/mnt/user-data/uploads/Full_Assembly_V1_2mm_OD_66_Tubes.step", sig=(2.0,95.0,2.0)),
}
for nm,p in designs.items():
    p.update(condenser_props(p["OD"],p["ID"],p["N"],p["step"],p["sig"]))
    print(f"{nm}: R_vapor={p['R_vapor']*1e3:.2f} mK/W (sets T_sat float), "
          f"R_pool={p['R_pool']*1e3:.2f} mK/W, h_cond={p['h_cond']:.0f}, f_sub={p['f_sub']:.2f}")

surf=ev.Surface(A_chip=A_CHIP, tc_depth=3.0e-3, k_solid=385.0)
bm=ev.BoilingModel(C_sf=0.013, beta_deg=45.0, C_sub_perK=0.0535)
_pc={}
def Psat(Tc):
    k=round(Tc,2)
    if k not in _pc: _pc[k]=PropsSI('P','T',Tc+273.15,'Q',1,'Water')/1e3
    return _pc[k]

def state(q, Rv, Rp):
    Q=q*1e4*A_CHIP
    T_sat=TSAT0_C + (Q-Q5)*Rv                       # floating saturation temperature
    fl=ev.WATER_12kPa                               # boiling/CHF props at 12 kPa nominal
    T_pool=TIN_C + Q*Rp
    dT_sub=max(T_sat - T_pool, 0.0)
    op=ev.Operating(fluid=fl, dT_sub=dT_sub, phi_deg=0.0)
    cur=ev.boiling_curve(op, surf, bm)
    return Q,T_sat,Psat(T_sat),T_pool,dT_sub,cur,cur["q_chf"]/1e4

def sweep(Rv, Rp, h_cond):
    rows=[]; q=5.0
    while q<400:
        Q,T_sat,P,T_pool,dT_sub,cur,chf=state(q,Rv,Rp)
        if q>=chf: break
        dT_sat=np.interp(q*1e4, cur["q_comb"], cur["dT"]); T_surf=T_sat+dT_sat
        rows.append(dict(q=q,P=P,T_sat=T_sat,T_surf=T_surf,dT_sub=dT_sub,dT_sat=dT_sat,
            h_boil=q*1e4/dT_sat,h_cond=h_cond,R_surf=(T_surf-T_pool)/Q,
            R_cond=(T_pool-TIN_C)/Q,R_tot=(T_surf-TIN_C)/Q,chf=chf))
        q+=5.0
    lo,hi=(q-5 if rows else 5.0), q+60
    for _ in range(60):
        mid=0.5*(lo+hi)
        if mid-state(mid,Rv,Rp)[6]<0: lo=mid
        else: hi=mid
    qc=0.5*(lo+hi)
    Q,T_sat,P,T_pool,dT_sub,cur,chf=state(qc,Rv,Rp)
    dT_sat=np.interp(qc*1e4,cur["q_comb"],cur["dT"]); T_surf=T_sat+dT_sat
    rows.append(dict(q=qc,P=P,T_sat=T_sat,T_surf=T_surf,dT_sub=dT_sub,dT_sat=dT_sat,
        h_boil=qc*1e4/dT_sat,h_cond=h_cond,R_surf=(T_surf-T_pool)/Q,
        R_cond=(T_pool-TIN_C)/Q,R_tot=(T_surf-TIN_C)/Q,chf=qc,is_chf=True))
    return rows,qc

results={}
for nm,p in designs.items():
    rows,qc=sweep(p["R_vapor"],p["R_pool"],p["h_cond"]); results[nm]=rows
    print(f"{nm}: CHF = {qc:.1f} W/cm^2  ({qc*A_CHIP*1e4:.0f} W),  "
          f"T_sat at CHF = {rows[-1]['T_sat']:.1f} C ({rows[-1]['P']:.0f} kPa)")

for nm,rows in results.items():
    print("\n"+"="*120)
    print(f"  {nm}   (water, T_in 20 C, 4 L/min, 40% fill, FLOATING pressure from 12 kPa)")
    print("="*120)
    print(f"  {'q':>6} {'P':>6} {'Tsat':>6} {'Tsurf':>6} {'dTsub':>6} {'dTsat':>6} "
          f"{'h_boil':>8} {'h_cond':>8} {'Rsurf':>8} {'Rcond':>8} {'Rtot':>8} {'CHF':>7}")
    print(f"  {'W/cm2':>6} {'kPa':>6} {'C':>6} {'C':>6} {'K':>6} {'K':>6} "
          f"{'W/m2K':>8} {'W/m2K':>8} {'K/W':>8} {'K/W':>8} {'K/W':>8} {'W/cm2':>7}")
    print("  "+"-"*118)
    for r in rows:
        tag=" <-CHF" if r.get("is_chf") else ""
        print(f"  {r['q']:>6.1f} {r['P']:>6.1f} {r['T_sat']:>6.1f} {r['T_surf']:>6.1f} "
              f"{r['dT_sub']:>6.1f} {r['dT_sat']:>6.2f} {r['h_boil']:>8.0f} {r['h_cond']:>8.0f} "
              f"{r['R_surf']:>8.4f} {r['R_cond']:>8.4f} {r['R_tot']:>8.4f} {r['chf']:>7.1f}{tag}")

import csv
for nm,rows in results.items():
    fn="/home/claude/sweep_float_%s.csv"%("A" if nm.startswith("A") else "B")
    with open(fn,"w",newline="") as f:
        w=csv.writer(f); w.writerow(["q_Wcm2","P_kPa","Tsat_C","Tsurf_C","dTsub_K","dTsat_K",
            "h_boil_Wm2K","h_cond_Wm2K","Rsurf_KW","Rcond_KW","Rtot_KW","CHF_Wcm2"])
        for r in rows:
            w.writerow([f"{r['q']:.2f}",f"{r['P']:.2f}",f"{r['T_sat']:.2f}",f"{r['T_surf']:.2f}",
                f"{r['dT_sub']:.2f}",f"{r['dT_sat']:.3f}",f"{r['h_boil']:.0f}",f"{r['h_cond']:.0f}",
                f"{r['R_surf']:.5f}",f"{r['R_cond']:.5f}",f"{r['R_tot']:.5f}",f"{r['chf']:.2f}"])

fig,ax=plt.subplots(figsize=(9,7))
cols={"A: 33 x 4.76mm":"#3b7dd8","B: 66 x 2.0mm":"#d8633b"}
for nm,rows in results.items():
    Ts=[r["T_surf"] for r in rows]; qs=[r["q"] for r in rows]
    ax.plot(Ts,qs,"-o",color=cols[nm],ms=4,label=nm)
    ax.plot(Ts[-1],qs[-1],"*",color=cols[nm],ms=18,markeredgecolor="k",zorder=5)
    ax.annotate(f"CHF {qs[-1]:.0f}",(Ts[-1],qs[-1]),textcoords="offset points",xytext=(8,-2),
                fontsize=9,color=cols[nm])
ax.axvline(TSAT0_C,color="0.6",ls=":",lw=1); ax.text(TSAT0_C+0.2,2,"T_sat0 49.4°C",color="0.5",fontsize=8)
ax.set_xlabel("surface temperature  T_surf  [°C]"); ax.set_ylabel("heat flux  q''  [W/cm²]")
ax.set_title("Plain-chip boiling curve, FLOATING pressure\n(water, 20°C inlet, 4 L/min, 40% fill, 12 kPa at 5 W/cm²)")
ax.legend(loc="upper left"); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig("/home/claude/boiling_AB_float.png",dpi=140); plt.close(fig)
print("\nfigure: boiling_AB_float.png ; CSVs: sweep_float_A.csv, sweep_float_B.csv")
