"""
Coupled boiling curve: plain chip + each condenser as the heat sink.
Fixed: 4 L/min, coolant inlet 20 C, water at 12 kPa (T_sat 49.4 C), 40% fill.
Sweeps q'' in 5 W/cm^2 steps to CHF for condenser A (33x4.76) and B (66x2.0).
"""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gmsh
import condenser_solver as cs
import evaporator_solver as ev
from condenser_solver import Geometry, Operating, Mesh

# ---- fixed conditions ----
A_CHIP = 34.5e-3*32.0e-3                 # 11.04 cm^2
TIN_C, TSAT_C = 20.0, 49.4
QTOT = 4.0/1000/60                       # m3/s
RHO, CP = 998.0, 4182.0                  # water ~20 C coolant
C_cool = QTOT*RHO*CP                     # coolant capacity rate [W/K]
g = 9.81
water = ev.WATER_12kPa

def churchill_chu_h(dT, OD):
    nu=water.mu_l/water.rho_l; al=water.k_l/(water.rho_l*water.cp_l); Pr=nu/al
    Ra=g*water.beta_exp*max(dT,0.5)*OD**3/(nu*al)
    return (0.6+0.387*Ra**(1/6)/(1+(0.559/Pr)**(9/16))**(8/27))**2*water.k_l/OD

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

# ---- condenser resistance + HTC per design ----
def condenser_props(OD, ID, N, step, sig):
    geo=Geometry(r_i=ID/2, r_o=OD/2, L=0.095, k_wall=385.0, n_tubes=1)
    mesh=Mesh(14,6,100)
    rc=cs.solve_with_nusselt(geo, Operating(Q_per_tube_Lmin=QTOT*1000*60/N,
        T_in=TIN_C+273.15, P_kPa=12.0, T_sat=TSAT_C+273.15, cond_model="nusselt_tube"), mesh)
    eps_cond=rc["eps"]; h_cond=float(np.mean(rc["h_ext_field"]))
    eps_sub=cs.solve_field(geo, Operating(Q_per_tube_Lmin=QTOT*1000*60/N,
        T_in=TIN_C+273.15, T_sat=TSAT_C+273.15, cond_model="constant_h",
        h_ext_const=churchill_chu_h(5.0,OD)), mesh)["eps"]
    f_sub=extract_fsub(step, sig, OD)
    eps_eff=(1-f_sub)*eps_cond + f_sub*eps_sub
    R_cond=1.0/(C_cool*eps_eff)             # pool->coolant resistance [K/W]
    return dict(R_cond=R_cond, h_cond=h_cond, eps_eff=eps_eff, f_sub=f_sub,
                eps_cond=eps_cond, eps_sub=eps_sub)

designs={
 "A: 33 x 4.76mm": dict(OD=4.76e-3, ID=3.137e-3, N=33,
    step="/mnt/user-data/uploads/CFD_Next_Gen.step", sig=(5.6,95.0,5.6)),
 "B: 66 x 2.0mm":  dict(OD=2.0e-3, ID=1.6e-3, N=66,
    step="/mnt/user-data/uploads/Full_Assembly_V1_2mm_OD_66_Tubes.step", sig=(2.0,95.0,2.0)),
}
for nm,p in designs.items():
    p.update(condenser_props(p["OD"],p["ID"],p["N"],p["step"],p["sig"]))
    print(f"{nm}: R_cond={p['R_cond']*1e3:.2f} mK/W, h_cond={p['h_cond']:.0f} W/m2K, "
          f"eps_eff={p['eps_eff']:.3f}, f_sub={p['f_sub']:.2f}")

# ---- boiling model ----
surf=ev.Surface(A_chip=A_CHIP, tc_depth=3.0e-3, k_solid=385.0)
bm=ev.BoilingModel(C_sf=0.013, beta_deg=45.0, C_sub_perK=0.0535)

def sweep(R_cond, h_cond):
    rows=[]
    q=5.0
    while q < 300:
        Q=q*1e4*A_CHIP                       # W
        T_pool=TIN_C + Q*R_cond
        dT_sub=max(TSAT_C - T_pool, 0.0)
        op=ev.Operating(fluid=water, dT_sub=dT_sub, phi_deg=0.0)
        cur=ev.boiling_curve(op, surf, bm)
        chf=cur["q_chf"]/1e4                 # W/cm2 at this subcooling
        if q >= chf:                         # past CHF -> record CHF point and stop
            # interpolate the self-consistent CHF crossing
            break
        dT_sat=np.interp(q*1e4, cur["q_comb"], cur["dT"])
        T_surf=TSAT_C + dT_sat
        h_boil=q*1e4/dT_sat
        R_surf=(T_surf - T_pool)/Q
        R_tot=(T_surf - TIN_C)/Q
        rows.append(dict(q=q, T_surf=T_surf, dT_sub=dT_sub, dT_sat=dT_sat,
                         h_boil=h_boil, h_cond=h_cond, R_surf=R_surf,
                         R_cond=R_cond, R_tot=R_tot, chf=chf))
        q+=5.0
    # find self-consistent CHF: q == chf(dT_sub(q))
    def gap(qq):
        Q=qq*1e4*A_CHIP; dts=max(TSAT_C-(TIN_C+Q*R_cond),0.0)
        return qq - ev.boiling_curve(ev.Operating(fluid=water,dT_sub=dts,phi_deg=0.0),surf,bm)["q_chf"]/1e4
    lo,hi=q-5 if rows else 5, q+40
    for _ in range(60):
        mid=(lo+hi)/2
        if gap(mid)<0: lo=mid
        else: hi=mid
    q_chf=(lo+hi)/2
    Q=q_chf*1e4*A_CHIP; T_pool=TIN_C+Q*R_cond; dT_sub=max(TSAT_C-T_pool,0)
    cur=ev.boiling_curve(ev.Operating(fluid=water,dT_sub=dT_sub,phi_deg=0.0),surf,bm)
    dT_sat=np.interp(q_chf*1e4,cur["q_comb"],cur["dT"]); T_surf=TSAT_C+dT_sat
    rows.append(dict(q=q_chf,T_surf=T_surf,dT_sub=dT_sub,dT_sat=dT_sat,
                     h_boil=q_chf*1e4/dT_sat,h_cond=h_cond,R_surf=(T_surf-T_pool)/Q,
                     R_cond=R_cond,R_tot=(T_surf-TIN_C)/Q,chf=q_chf,is_chf=True))
    return rows, q_chf

results={}
for nm,p in designs.items():
    rows,qchf=sweep(p["R_cond"],p["h_cond"]); results[nm]=rows
    print(f"\n{nm}: CHF = {qchf:.1f} W/cm^2  ({qchf*A_CHIP*1e4:.0f} W)")

# ---- tables ----
for nm,rows in results.items():
    print("\n"+"="*108)
    print(f"  {nm}   (water/12 kPa, T_in 20 C, 4 L/min, 40% fill)")
    print("="*108)
    print(f"  {'q[W/cm2]':>8} {'Tsurf[C]':>8} {'dTsub[K]':>8} {'dTsat[K]':>8} "
          f"{'h_boil':>9} {'h_cond':>8} {'Rsurf':>9} {'Rcond':>9} {'Rtot':>9} {'CHF[W/cm2]':>10}")
    print(f"  {'':>8} {'':>8} {'':>8} {'':>8} {'[W/m2K]':>9} {'[W/m2K]':>8} "
          f"{'[K/W]':>9} {'[K/W]':>9} {'[K/W]':>9} {'':>10}")
    print("  "+"-"*106)
    for r in rows:
        tag=" <-CHF" if r.get("is_chf") else ""
        print(f"  {r['q']:>8.1f} {r['T_surf']:>8.1f} {r['dT_sub']:>8.1f} {r['dT_sat']:>8.2f} "
              f"{r['h_boil']:>9.0f} {r['h_cond']:>8.0f} {r['R_surf']:>9.4f} {r['R_cond']:>9.4f} "
              f"{r['R_tot']:>9.4f} {r['chf']:>10.1f}{tag}")

# ---- save CSVs ----
import csv
for nm,rows in results.items():
    fn="/home/claude/sweep_%s.csv"%("A" if nm.startswith("A") else "B")
    with open(fn,"w",newline="") as f:
        w=csv.writer(f); w.writerow(["q_Wcm2","Tsurf_C","dTsub_K","dTsat_K","h_boil_Wm2K",
            "h_cond_Wm2K","Rsurf_KW","Rcond_KW","Rtot_KW","CHF_Wcm2"])
        for r in rows:
            w.writerow([f"{r['q']:.2f}",f"{r['T_surf']:.2f}",f"{r['dT_sub']:.2f}",f"{r['dT_sat']:.3f}",
                f"{r['h_boil']:.0f}",f"{r['h_cond']:.0f}",f"{r['R_surf']:.5f}",f"{r['R_cond']:.5f}",
                f"{r['R_tot']:.5f}",f"{r['chf']:.2f}"])

# ---- plot: T_surf (x) vs q'' (y) ----
fig,ax=plt.subplots(figsize=(9,7))
cols={"A: 33 x 4.76mm":"#3b7dd8","B: 66 x 2.0mm":"#d8633b"}
for nm,rows in results.items():
    Ts=[r["T_surf"] for r in rows]; qs=[r["q"] for r in rows]
    ax.plot(Ts,qs,"-o",color=cols[nm],ms=4,label=nm)
    ax.plot(Ts[-1],qs[-1],"*",color=cols[nm],ms=18,markeredgecolor="k",zorder=5)
    ax.annotate(f"CHF {qs[-1]:.0f}",(Ts[-1],qs[-1]),textcoords="offset points",
                xytext=(8,-4),fontsize=9,color=cols[nm])
ax.axvline(TSAT_C,color="0.6",ls=":",lw=1); ax.text(TSAT_C+0.2,2,"T_sat 49.4°C",color="0.5",fontsize=8)
ax.set_xlabel("surface temperature  T_surf  [°C]"); ax.set_ylabel("heat flux  q''  [W/cm²]")
ax.set_title("Plain-chip boiling curve through each condenser\n(water/12 kPa, 20°C inlet, 4 L/min, 40% fill)")
ax.legend(loc="upper left"); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig("/home/claude/boiling_AB.png",dpi=140); plt.close(fig)
print("\nfigure: boiling_AB.png ; CSVs: sweep_A.csv, sweep_B.csv")
