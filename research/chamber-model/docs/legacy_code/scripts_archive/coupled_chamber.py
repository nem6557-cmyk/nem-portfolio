"""
Coupled closed chamber — steady state
=====================================
Evaporator (plain copper chip, subcooled pool boiling)  <->  condenser
(33-tube bank, partially submerged at 40% fill).

Heat path at steady state:
  chip  ->  vapor (boiling)        ->  condensing tubes  (latent path)
  chip  ->  pool  (convection)     ->  submerged tubes   (sensible path)
  all heat leaves through the 4 L/min coolant in the tubes.

At fixed chamber pressure (12 kPa, T_sat=49.4 C) the condenser pins the latent
duty and caps the total rejectable power. We solve the balance, sweep chip power
over the achievable window, and report the operating point + the limiting factor.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import condenser_solver as cs
import evaporator_solver as ev

# ---- geometry / operating ----
OD, ID, LT, NT = 4.76e-3, 3.137e-3, 0.095, 33
A_CHIP = 34.5e-3 * 32.0e-3
QTOT_LPM = 4.0
TIN_C, TSAT_C = 40.0, 49.4
F_SUB = 0.483                      # area-weighted submerged fraction at 40% fill
g = 9.81

water = ev.WATER_12kPa            # condensing/pool fluid props at 12 kPa
TIN = TIN_C + 273.15; TSAT = TSAT_C + 273.15; dTmax = TSAT - TIN

# ---- per-tube condenser solves (condensing vs submerged) ----
geo1 = cs.Geometry(r_i=ID/2, r_o=OD/2, L=LT, k_wall=385.0, n_tubes=1)
mesh = cs.Mesh(n_rf=16, n_rw=8, n_z=120)

op_cond = cs.Operating(Q_per_tube_Lmin=QTOT_LPM/NT, T_in=TIN, P_kPa=12.0,
                       T_sat=TSAT, cond_model="nusselt_tube")
res_cond = cs.solve_with_nusselt(geo1, op_cond, mesh)
Q_cond_tube = res_cond["Q_ext"]; eps_cond = res_cond["eps"]
mc = res_cond["mdot"] * res_cond["cp"]            # per-tube m_dot*cp [W/K]

# submerged tube: external natural convection (Churchill-Chu, horizontal cylinder)
def churchill_chu_h(dT):
    nu = water.mu_l/water.rho_l; al = water.k_l/(water.rho_l*water.cp_l); Pr = nu/al
    Ra = g*water.beta_exp*max(dT,0.5)*OD**3/(nu*al)
    Nu = (0.6 + 0.387*Ra**(1/6)/(1+(0.559/Pr)**(9/16))**(8/27))**2
    return Nu*water.k_l/OD
h_nc = churchill_chu_h(5.0)
op_sub = cs.Operating(Q_per_tube_Lmin=QTOT_LPM/NT, T_in=TIN, T_sat=TSAT,
                      cond_model="constant_h", h_ext_const=h_nc)
res_sub = cs.solve_field(geo1, op_sub, mesh)
eps_sub = res_sub["eps"]

# ---- condenser capacity at fixed 12 kPa ----
N_cond, N_sub = NT*(1-F_SUB), NT*F_SUB
Q_lat_cap = N_cond * Q_cond_tube                 # latent duty (pinned at 12 kPa)
Q_sens_cap = N_sub * mc * eps_sub * dTmax        # max sensible (pool -> T_sat)
Q_cap = Q_lat_cap + Q_sens_cap

# ---- chip boiling state ----
surf = ev.Surface(A_chip=A_CHIP, tc_depth=3.0e-3, k_solid=385.0)
bm = ev.BoilingModel(C_sf=0.013, beta_deg=45.0, C_sub_perK=0.0535)

def chip_state(Q, dT_sub):
    qpp = Q/A_CHIP/1e4                            # W/cm2
    st = ev.operating_point(qpp, ev.Operating(fluid=water, dT_sub=dT_sub), surf, bm)
    return qpp, st

print("="*70)
print("COUPLED CHAMBER — water, 12 kPa, T_in 40 C, 4 L/min")
print("="*70)
print(f"Condensing tube duty   : {Q_cond_tube:.2f} W  (eps {eps_cond:.3f})")
print(f"Submerged tube natconv : h = {h_nc:.0f} W/m2K, eps {eps_sub:.3f}")
print(f"Regime split (48% sub) : {N_cond:.0f} condensing-equiv, {N_sub:.0f} submerged-equiv")
print(f"\nCONDENSER CAPACITY at 12 kPa / 40 C / 4 L/min:")
print(f"   latent (pinned)     : {Q_lat_cap:.0f} W")
print(f"   sensible (max)      : {Q_sens_cap:.0f} W")
print(f"   TOTAL CAPACITY      : {Q_cap:.0f} W   ({Q_cap/(A_CHIP*1e4):.1f} W/cm2 on the chip)")

# chip CHF for reference
cur_sat = ev.boiling_curve(ev.Operating(fluid=water, dT_sub=0.0), surf, bm)
cur_sub = ev.boiling_curve(ev.Operating(fluid=water, dT_sub=dTmax), surf, bm)
print(f"\nChip CHF (plain Cu)    : {cur_sat['q_chf']/1e4:.0f} W/cm2 saturated "
      f"-> {cur_sat['q_chf']/1e4*A_CHIP*1e4:.0f} W ; "
      f"{cur_sub['q_chf']/1e4:.0f} W/cm2 at {dTmax:.1f} K subcool -> {cur_sub['q_chf']/1e4*A_CHIP*1e4:.0f} W")
print(f"LIMITING FACTOR        : "
      f"{'CONDENSER' if Q_cap < cur_sat['q_chf']/1e4*A_CHIP*1e4 else 'CHIP CHF'} "
      f"(chamber caps at {Q_cap:.0f} W, chip CHF >= {cur_sat['q_chf']/1e4*A_CHIP*1e4:.0f} W)")

# ---- operating window sweep (chip power from latent floor to capacity) ----
Qs = np.linspace(Q_lat_cap, Q_cap, 40)
Tpool, dTsub, Tchip, margin, qpp_arr = [], [], [], [], []
for Q in Qs:
    Qsens = Q - Q_lat_cap
    Tp = TIN + Qsens/(N_sub*mc*eps_sub); Tp = min(Tp, TSAT)
    ds = TSAT - Tp
    qpp, st = chip_state(Q, ds)
    Tpool.append(Tp-273.15); dTsub.append(ds); qpp_arr.append(qpp)
    Tchip.append(st["T_surf_C"] if not st.get("beyond_chf") else np.nan)
    margin.append(st["margin_to_chf"] if not st.get("beyond_chf") else np.nan)

print(f"\nOPERATING POINT at capacity ({Q_cap:.0f} W, {Q_cap/(A_CHIP*1e4):.1f} W/cm2):")
print(f"   pool subcooling     : {dTsub[-1]:.1f} K  (T_pool {Tpool[-1]:.1f} C)")
print(f"   chip surface temp   : {Tchip[-1]:.1f} C  (superheat {Tchip[-1]-TSAT_C:.1f} K)")
print(f"   CHF margin          : {margin[-1]:.2f}")
print(f"OPERATING POINT at latent floor ({Q_lat_cap:.0f} W, {Q_lat_cap/(A_CHIP*1e4):.1f} W/cm2):")
print(f"   pool subcooling     : {dTsub[0]:.1f} K (max), chip {Tchip[0]:.1f} C, CHF margin {margin[0]:.2f}")

# ---- capacity vs coolant inlet temperature (sensitivity) ----
Tin_sweep = np.array([20,25,30,35,40,45])
cap_sweep = []
for Tic in Tin_sweep:
    dT = TSAT - (Tic+273.15)
    op_c = cs.Operating(Q_per_tube_Lmin=QTOT_LPM/NT, T_in=Tic+273.15, P_kPa=12.0,
                        T_sat=TSAT, cond_model="nusselt_tube")
    rc = cs.solve_with_nusselt(geo1, op_c, mesh)
    cap = N_cond*rc["Q_ext"] + N_sub*mc*eps_sub*dT
    cap_sweep.append(cap)
cap_sweep = np.array(cap_sweep)

# ================= figures =================
fig, ax = plt.subplots(2, 2, figsize=(12, 8))
ax[0,0].plot(Qs, Tchip, "r-", lw=2, label="chip surface")
ax[0,0].plot(Qs, Tpool, "b-", lw=2, label="pool")
ax[0,0].axhline(TSAT_C, color="k", ls=":", label="T_sat (49.4 C)")
ax[0,0].set_xlabel("chip power [W]"); ax[0,0].set_ylabel("temperature [°C]")
ax[0,0].set_title("Temperatures"); ax[0,0].legend(fontsize=8); ax[0,0].grid(alpha=0.3)

ax[0,1].plot(Qs, dTsub, "g-", lw=2)
ax[0,1].set_xlabel("chip power [W]"); ax[0,1].set_ylabel("pool subcooling ΔT_sub [K]")
ax[0,1].set_title("Pool subcooling collapses as load rises"); ax[0,1].grid(alpha=0.3)

ax[1,0].plot(Qs, margin, "m-", lw=2); ax[1,0].axhline(1.0, color="r", ls="--", label="CHF")
ax[1,0].set_xlabel("chip power [W]"); ax[1,0].set_ylabel("CHF margin (q''_CHF / q'')")
ax[1,0].set_title("Chip stays far from CHF (condenser-limited)"); ax[1,0].legend(fontsize=8); ax[1,0].grid(alpha=0.3)

ax[1,1].plot(Tin_sweep, cap_sweep, "o-", lw=2, color="darkorange")
ax[1,1].scatter([40],[Q_cap], color="red", zorder=5, s=60)
ax[1,1].set_xlabel("coolant inlet temperature [°C]"); ax[1,1].set_ylabel("chamber capacity [W]")
ax[1,1].set_title("Capacity scales strongly with coolant inlet T"); ax[1,1].grid(alpha=0.3)
fig.suptitle(f"Coupled chamber — water/12 kPa/4 L/min: condenser-limited at {Q_cap:.0f} W "
             f"({Q_cap/(A_CHIP*1e4):.0f} W/cm²)", fontsize=13)
fig.tight_layout(rect=[0,0,1,0.96]); fig.savefig("/home/claude/coupled_chamber.png", dpi=140); plt.close(fig)
print("\nfigure: coupled_chamber.png")
print("="*70)
