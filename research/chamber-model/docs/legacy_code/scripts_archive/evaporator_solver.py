"""
Evaporator side  --  plain-surface subcooled pool boiling  (Stage 1 verified)
=============================================================================

Steady-state boiling-curve model for a PLAIN copper heated surface (the chip)
in a subcooled pool, built to pair with the condenser solver. Given the working
fluid, chamber pressure (-> T_sat), bulk subcooling, surface orientation, and a
heat flux (or wall superheat), it returns the full boiling curve and the
operating point:

    natural convection  ->  onset of nucleate boiling  ->  nucleate boiling
    (Rohsenow / Cooper)  ->  critical heat flux (Kandlikar 2001 + subcooling)

It also maps surface temperature to the embedded-thermocouple reading through a
1-D conduction offset (your single-chip-node assumption), and exposes a
chamber-balance hook so the evaporator load can be closed against the condenser
duty for the full closed-loop chamber.

Mirrors the verification discipline of the condenser solver.
Units: SI throughout (m, kg, s, K, W).  Heat flux reported in W/m2 (and W/cm2).
"""

import numpy as np
from dataclasses import dataclass, field
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

G = 9.81


# ----------------------------------------------------------------------
# Saturated-fluid property presets  (NOMINAL -- replace with CoolProp/your tables)
# Each preset is at the stated reference state; set P/T_sat for your real point.
# ----------------------------------------------------------------------
@dataclass
class FluidProps:
    name: str
    T_sat: float       # saturation temperature [K] at the reference pressure
    P: float           # pressure [Pa]
    P_crit: float      # critical pressure [Pa]
    rho_l: float       # liquid density [kg/m3]
    rho_v: float       # vapor density [kg/m3]
    h_fg: float        # latent heat [J/kg]
    sigma: float       # surface tension [N/m]
    mu_l: float        # liquid viscosity [Pa s]
    k_l: float         # liquid conductivity [W/mK]
    cp_l: float        # liquid specific heat [J/kgK]
    M: float           # molar mass [g/mol]
    beta_exp: float    # liquid thermal expansion coeff [1/K]
    n_rohsenow: float  # Rohsenow exponent (1.0 water, 1.7 others)

    @property
    def Pr_l(self):
        return self.mu_l * self.cp_l / self.k_l

    @property
    def p_r(self):
        return self.P / self.P_crit

    @property
    def alpha_l(self):
        return self.k_l / (self.rho_l * self.cp_l)

    @property
    def nu_l(self):
        return self.mu_l / self.rho_l


# Water at 12 kPa  (T_sat ~ 49.4 C)  -- consistent with the condenser model
WATER_12kPa = FluidProps(
    name="water @ 12 kPa", T_sat=49.4 + 273.15, P=12.0e3, P_crit=22.064e6,
    rho_l=988.0, rho_v=0.0827, h_fg=2.382e6, sigma=0.0679, mu_l=5.47e-4,
    k_l=0.644, cp_l=4181.0, M=18.015, beta_exp=4.2e-4, n_rohsenow=1.0)

# HFE-7000 at 1 atm  (T_sat ~ 34 C)  -- set your real chamber pressure;
# NOTE at 12 kPa HFE-7000 saturates near -15 C, so it is normally run nearer 1 atm.
HFE7000_1atm = FluidProps(
    name="HFE-7000 @ 1 atm", T_sat=34.0 + 273.15, P=101.3e3, P_crit=2.476e6,
    rho_l=1385.0, rho_v=9.6, h_fg=1.42e5, sigma=0.0124, mu_l=4.5e-4,
    k_l=0.075, cp_l=1300.0, M=200.0, beta_exp=1.8e-3, n_rohsenow=1.7)


@dataclass
class Surface:
    A_chip: float = 1.0e-4      # boiling area [m2]  (10 x 10 mm)        <-- REPLACE
    L_char: float = None        # natural-convection char. length A/P [m]
    tc_depth: float = 3.0e-3    # thermocouple depth below boil surface [m] <-- REPLACE
    k_solid: float = 385.0      # substrate conductivity [W/mK] (copper)
    side: float = None          # square-side, for L_char if not given

    def __post_init__(self):
        if self.side is None:
            self.side = np.sqrt(self.A_chip)
        if self.L_char is None:                    # A/P for a square plate
            self.L_char = self.A_chip / (4 * self.side)


@dataclass
class Operating:
    fluid: FluidProps = field(default_factory=lambda: WATER_12kPa)
    dT_sub: float = 10.0        # bulk liquid subcooling T_sat - T_bulk [K] <-- REPLACE
    phi_deg: float = 0.0        # surface orientation (0 = horizontal up)  <-- REPLACE


@dataclass
class BoilingModel:
    C_sf: float = 0.013         # Rohsenow surface-fluid coeff (water/Cu)  <-- FIT
    Rp_um: float = 2.5          # surface roughness for Cooper [um] (~Ra)  <-- REPLACE
    beta_deg: float = 45.0      # receding contact angle [deg] (Kandlikar) <-- FIT (bounded)
    nucleate: str = "rohsenow"  # "rohsenow" or "cooper"
    subcool_chf: str = "linear" # "linear" (C_sub /K) or "ivey_morris"
    C_sub_perK: float = 0.0535  # linear CHF subcooling slope [1/K] (water/Cu) <-- FIT


# ----------------------------------------------------------------------
# Mechanism sub-models
# ----------------------------------------------------------------------
def natural_convection_q(dT, fl: FluidProps, surf: Surface):
    """Upward-facing heated horizontal plate; q'' from McAdams/Incropera Nu-Ra."""
    dT = np.maximum(dT, 1e-6)
    Ra = G * fl.beta_exp * dT * surf.L_char**3 / (fl.nu_l * fl.alpha_l)
    Nu = np.where(Ra < 1e7, 0.54 * Ra**0.25, 0.15 * Ra**(1.0/3.0))
    Nu = np.maximum(Nu, 0.27 * Ra**0.25)           # floor (cool-plate branch)
    h = Nu * fl.k_l / surf.L_char
    return h * dT, h


def rohsenow_q(dT_sat, fl: FluidProps, bm: BoilingModel):
    """Rohsenow (1952) nucleate pool boiling:  q'' ~ dT_sat^3."""
    dT_sat = np.maximum(dT_sat, 0.0)
    base = np.sqrt(G * (fl.rho_l - fl.rho_v) / fl.sigma)
    brk = fl.cp_l * dT_sat / (bm.C_sf * fl.h_fg * fl.Pr_l**fl.n_rohsenow)
    return fl.mu_l * fl.h_fg * base * brk**3


def cooper_q(dT_sat, fl: FluidProps, bm: BoilingModel):
    """Cooper (1984) reduced-pressure correlation, solved for q''(dT_sat).
       h = A q''^0.67 with A below; q'' = h dT  ->  q'' = (A dT)^(1/0.33)."""
    dT_sat = np.maximum(dT_sat, 1e-9)
    expo = 0.12 - 0.2 * np.log10(bm.Rp_um)
    A = 55.0 * fl.p_r**expo * (-np.log10(fl.p_r))**(-0.55) * fl.M**(-0.5)
    return (A * dT_sat) ** (1.0 / 0.33)


def nucleate_q(dT_sat, fl, bm):
    return rohsenow_q(dT_sat, fl, bm) if bm.nucleate == "rohsenow" else cooper_q(dT_sat, fl, bm)


def chf_saturated(fl: FluidProps, beta_deg, phi_deg):
    """Kandlikar (2001) CHF with receding contact angle beta and orientation phi."""
    b = np.radians(beta_deg); phi = np.radians(phi_deg)
    coeff = (1 + np.cos(b)) / 16.0
    grp = (2.0/np.pi) + (np.pi/4.0) * (1 + np.cos(b)) * np.cos(phi)
    K = coeff * np.sqrt(grp)
    q = K * fl.h_fg * fl.rho_v**0.5 * (fl.sigma * G * (fl.rho_l - fl.rho_v))**0.25
    return q, K


def subcooling_factor(dT_sub, fl: FluidProps, bm: BoilingModel):
    """CHF enhancement multiplier for bulk subcooling."""
    if bm.subcool_chf == "linear":
        return 1.0 + bm.C_sub_perK * dT_sub
    # Ivey-Morris (over-predicts at very low reduced pressure -- see note)
    return 1.0 + 0.1 * (fl.rho_l / fl.rho_v)**0.75 * (fl.cp_l * dT_sub / fl.h_fg)


def chf_total(fl, op: Operating, bm: BoilingModel):
    q_sat, K = chf_saturated(fl, bm.beta_deg, op.phi_deg)
    f = subcooling_factor(op.dT_sub, fl, bm)
    return q_sat * f, q_sat, K, f


# ----------------------------------------------------------------------
# Boiling curve assembly
# ----------------------------------------------------------------------
def boiling_curve(op: Operating, surf: Surface, bm: BoilingModel,
                  dT_max=40.0, n=600):
    fl = op.fluid
    dT = np.linspace(0.05, dT_max, n)              # wall superheat T_w - T_sat
    q_nc, h_nc = natural_convection_q(dT + op.dT_sub, fl, surf)  # NC driven by T_w - T_bulk
    q_nb = nucleate_q(dT, fl, bm)
    q_comb = np.sqrt(q_nc**2 + q_nb**2)            # smooth NC->nucleate blend

    q_chf, q_chf_sat, K, f_sub = chf_total(fl, op, bm)

    # ONB ~ where nucleate overtakes natural convection
    onb_idx = np.argmax(q_nb > q_nc)
    dT_onb = dT[onb_idx]; q_onb = q_comb[onb_idx]

    # CHF superheat ~ where the combined nucleate curve reaches CHF
    chf_idx = np.argmax(q_comb >= q_chf)
    if q_comb[chf_idx] < q_chf:                    # CHF beyond sweep
        chf_idx = n - 1
    dT_chf = dT[chf_idx]
    q_stable = np.minimum(q_comb, q_chf)           # stable branch capped at CHF

    return dict(dT=dT, q_nc=q_nc, q_nb=q_nb, q_comb=q_comb, q_stable=q_stable,
                q_chf=q_chf, q_chf_sat=q_chf_sat, K=K, f_sub=f_sub,
                dT_onb=dT_onb, q_onb=q_onb, dT_chf=dT_chf,
                h_nc=h_nc, fl=fl, op=op, surf=surf, bm=bm)


def surface_to_tc(T_surf, q_flux, surf: Surface):
    """1-D conduction offset: embedded TC sits tc_depth below the boiling surface."""
    return T_surf + q_flux * surf.tc_depth / surf.k_solid


def operating_point(q_target_Wcm2, op, surf, bm):
    """Invert the boiling curve: given an applied heat flux, return the state."""
    q = q_target_Wcm2 * 1e4
    cur = boiling_curve(op, surf, bm)
    if q >= cur["q_chf"]:
        return dict(beyond_chf=True, q_chf_Wcm2=cur["q_chf"]/1e4)
    dT_sat = np.interp(q, cur["q_comb"], cur["dT"])
    T_surf = op.fluid.T_sat + dT_sat
    T_tc = surface_to_tc(T_surf, q, surf)
    h_boil = q / dT_sat
    return dict(beyond_chf=False, q_Wcm2=q_target_Wcm2, dT_sat=dT_sat,
                T_surf_C=T_surf - 273.15, T_tc_C=T_tc - 273.15,
                h_boil=h_boil, margin_to_chf=cur["q_chf"]/q,
                q_chf_Wcm2=cur["q_chf"]/1e4)


# ----------------------------------------------------------------------
# Chamber-loop coupling hook (closes evaporator load against condenser duty)
# ----------------------------------------------------------------------
def chamber_balance(surf, bm, fluid, phi_deg, R_cond_KperW, T_coolant_C,
                    dT_sub_guess=10.0, relax=0.5, iters=60):
    """
    Steady closed-loop point. Condenser is represented by an effective
    resistance R_cond from pool to coolant (e.g. from the condenser solver).
    Energy balance:  Q = q''*A_chip  must be carried by the condenser:
        Q = (T_pool - T_coolant) / R_cond
    and the pool subcooling seen by the evaporator is dT_sub = T_sat - T_pool.
    Iterates q'' (hence T_pool) to self-consistency at a chosen applied flux.
    Returned for a swept applied flux array.
    """
    fl = fluid
    out = []
    for q_Wcm2 in np.linspace(1, 60, 60):
        dT_sub = dT_sub_guess
        for _ in range(iters):
            op = Operating(fluid=fl, dT_sub=dT_sub, phi_deg=phi_deg)
            st = operating_point(q_Wcm2, op, surf, bm)
            if st.get("beyond_chf"):
                dT_sub = None; break
            Q = q_Wcm2 * 1e4 * surf.A_chip
            T_pool = T_coolant_C + Q * R_cond_KperW
            dT_sub_new = (fl.T_sat - 273.15) - T_pool
            if dT_sub_new < 0:
                dT_sub_new = 0.0
            if abs(dT_sub_new - dT_sub) < 1e-4:
                dT_sub = dT_sub_new; break
            dT_sub = relax * dT_sub_new + (1 - relax) * dT_sub
        if dT_sub is None:
            break
        out.append((q_Wcm2, dT_sub, st["T_surf_C"], st["margin_to_chf"]))
    return np.array(out)


# ----------------------------------------------------------------------
# VERIFICATION
# ----------------------------------------------------------------------
def verify():
    print("=" * 72)
    print("EVAPORATOR VERIFICATION SUITE")
    print("=" * 72)

    # (1) Kandlikar CHF coefficient at beta=0, phi=0  -> 0.18572 ; Zuber=0.131
    _, K0 = chf_saturated(WATER_12kPa, 0.0, 0.0)
    err = abs(K0 - 0.18572) / 0.18572
    print(f"(1) Kandlikar CHF coeff @ beta=phi=0 : K = {K0:.5f}  (analytic 0.18572) "
          f"rel err {err*100:.3f}%  [{'PASS' if err < 1e-3 else 'CHECK'}]")
    print(f"      reference coefficients: Zuber 0.131, Lienhard-Dhir 0.149")

    # (2) Water @ 1 atm saturated CHF (beta=0) should land near 1.1-1.6 MW/m2
    water_1atm = FluidProps("water 1atm", 373.15, 101.3e3, 22.064e6, 957.9, 0.5956,
                            2257e3, 0.0589, 2.79e-4, 0.679, 4217.0, 18.015, 7.5e-4, 1.0)
    q0, _ = chf_saturated(water_1atm, 0.0, 0.0)
    q_zuber = 0.131 * water_1atm.h_fg * water_1atm.rho_v**0.5 * \
              (water_1atm.sigma * G * (water_1atm.rho_l - water_1atm.rho_v))**0.25
    print(f"(2) Water 1 atm CHF: Kandlikar(beta=0) {q0/1e6:.3f} MW/m2, "
          f"Zuber {q_zuber/1e6:.3f} MW/m2  (textbook Zuber ~1.11)  "
          f"[{'PASS' if 1.0 < q_zuber/1e6 < 1.2 else 'CHECK'}]")

    # (3) Rohsenow log-log slope must be exactly 3
    bm = BoilingModel(); dT = np.array([5.0, 10.0, 20.0])
    q = rohsenow_q(dT, WATER_12kPa, bm)
    slope = np.polyfit(np.log(dT), np.log(q), 1)[0]
    print(f"(3) Rohsenow log-log slope            : {slope:.4f} (analytic 3.000)  "
          f"[{'PASS' if abs(slope-3) < 1e-6 else 'CHECK'}]")

    # (4) Cooper log-log slope ~ 1/0.33 = 3.03
    qc = cooper_q(dT, WATER_12kPa, bm)
    slope_c = np.polyfit(np.log(dT), np.log(qc), 1)[0]
    print(f"(4) Cooper  log-log slope             : {slope_c:.4f} (analytic 3.030)  "
          f"[{'PASS' if abs(slope_c-3.0303) < 1e-3 else 'CHECK'}]")

    # (5) Boiling curve monotonic up to CHF
    cur = boiling_curve(Operating(), Surface(), bm)
    mono = np.all(np.diff(cur["q_comb"]) > 0)
    print(f"(5) Boiling curve monotonic to CHF    : {mono}  [{'PASS' if mono else 'CHECK'}]")

    # (6) Subcooling models: report both, flag low-p_r blow-up
    lin = subcooling_factor(10.0, WATER_12kPa, BoilingModel(subcool_chf="linear"))
    im  = subcooling_factor(10.0, WATER_12kPa, BoilingModel(subcool_chf="ivey_morris"))
    print(f"(6) CHF subcooling factor @10K        : linear {lin:.3f}, Ivey-Morris {im:.3f}")
    print(f"      (Ivey-Morris inflated by (rho_l/rho_v)^0.75 at 12 kPa -> use linear/fit)")
    print("=" * 72)


# ----------------------------------------------------------------------
# Plots
# ----------------------------------------------------------------------
def make_plots(path="/home/claude"):
    surf = Surface(); bm = BoilingModel()

    # Fig 1: full boiling curve, water @ 12 kPa, plain Cu
    op = Operating(dT_sub=10.0)
    cur = boiling_curve(op, surf, bm)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.loglog(cur["dT"], cur["q_nc"]/1e4, "--", color="tab:green", lw=1.3, label="natural convection")
    ax.loglog(cur["dT"], cur["q_nb"]/1e4, "--", color="tab:orange", lw=1.3, label="nucleate (Rohsenow)")
    ax.loglog(cur["dT"], cur["q_stable"]/1e4, "-", color="tab:blue", lw=2.4, label="boiling curve")
    ax.axhline(cur["q_chf"]/1e4, color="tab:red", ls=":", lw=1.6,
               label=f"CHF subcooled {cur['q_chf']/1e4:.1f} W/cm²")
    ax.axhline(cur["q_chf_sat"]/1e4, color="firebrick", ls="-.", lw=1.0,
               label=f"CHF saturated {cur['q_chf_sat']/1e4:.1f} W/cm²")
    ax.plot(cur["dT_onb"], cur["q_onb"]/1e4, "ko", ms=7); ax.annotate("ONB",
            (cur["dT_onb"], cur["q_onb"]/1e4), textcoords="offset points", xytext=(6, -10))
    ax.plot(cur["dT_chf"], cur["q_chf"]/1e4, "rs", ms=9); ax.annotate("CHF",
            (cur["dT_chf"], cur["q_chf"]/1e4), textcoords="offset points", xytext=(-28, 6))
    ax.axhline(208, color="gray", ls=(0, (1, 1)), lw=1.0, alpha=0.8,
               label="~208 W/cm² (your enhanced result)")
    ax.set_xlabel("wall superheat  ΔT_sat = T_wall − T_sat  [K]")
    ax.set_ylabel("heat flux  q''  [W/cm²]")
    ax.set_title("Plain-surface subcooled pool boiling — water @ 12 kPa, β=45°, ΔT_sub=10 K")
    ax.legend(fontsize=8, loc="lower right"); ax.grid(which="both", alpha=0.25)
    ax.set_xlim(1, 40); ax.set_ylim(0.1, 300)
    fig.tight_layout(); fig.savefig(f"{path}/ev_fig1_boiling_curve.png", dpi=140); plt.close(fig)

    # Fig 2: subcooling family (CHF rises with subcooling)
    fig, ax = plt.subplots(figsize=(8, 5))
    for dsub, c in zip([0, 5, 10, 20], plt.cm.viridis(np.linspace(0.2, 0.85, 4))):
        cc = boiling_curve(Operating(dT_sub=dsub), surf, bm)
        ax.loglog(cc["dT"], cc["q_stable"]/1e4, color=c, lw=2, label=f"ΔT_sub = {dsub} K")
        ax.plot(cc["dT_chf"], cc["q_chf"]/1e4, "o", color=c, ms=6)
    ax.set_xlabel("ΔT_sat [K]"); ax.set_ylabel("q'' [W/cm²]")
    ax.set_title("Effect of bulk subcooling on the boiling curve and CHF (water @ 12 kPa)")
    ax.legend(fontsize=9); ax.grid(which="both", alpha=0.25); ax.set_xlim(1, 40)
    fig.tight_layout(); fig.savefig(f"{path}/ev_fig2_subcooling.png", dpi=140); plt.close(fig)

    # Fig 3: CHF vs receding contact angle (the fitted parameter)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    betas = np.linspace(1, 90, 200)
    for fl, lbl in [(WATER_12kPa, "water @ 12 kPa"), (HFE7000_1atm, "HFE-7000 @ 1 atm")]:
        q = np.array([chf_saturated(fl, b, 0.0)[0] for b in betas]) / 1e4
        ax.plot(betas, q, lw=2, label=lbl)
    ax.axvspan(3, 15, alpha=0.12, color="tab:blue", label="HFE-7000 β bound (3–15°)")
    ax.axvspan(20, 70, alpha=0.12, color="tab:orange", label="water β bound (20–70°)")
    ax.set_xlabel("receding contact angle  β  [deg]")
    ax.set_ylabel("saturated CHF  [W/cm²]")
    ax.set_title("Kandlikar CHF sensitivity to contact angle (the bounded fitted parameter)")
    ax.legend(fontsize=8); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(f"{path}/ev_fig3_chf_contact_angle.png", dpi=140); plt.close(fig)

    # Fig 4: water vs HFE-7000 boiling curves (each at its preset state)
    fig, ax = plt.subplots(figsize=(8, 5))
    cw = boiling_curve(Operating(fluid=WATER_12kPa, dT_sub=10), surf,
                       BoilingModel(C_sf=0.013))
    ch = boiling_curve(Operating(fluid=HFE7000_1atm, dT_sub=10), surf,
                       BoilingModel(C_sf=0.004, beta_deg=8.0, C_sub_perK=0.03))
    ax.loglog(cw["dT"], cw["q_stable"]/1e4, lw=2.2, label="water @ 12 kPa (C_sf=0.013, β=45°)")
    ax.loglog(ch["dT"], ch["q_stable"]/1e4, lw=2.2, label="HFE-7000 @ 1 atm (C_sf=0.004, β=8°)")
    ax.plot(cw["dT_chf"], cw["q_chf"]/1e4, "o", ms=6)
    ax.plot(ch["dT_chf"], ch["q_chf"]/1e4, "o", ms=6)
    ax.set_xlabel("ΔT_sat [K]"); ax.set_ylabel("q'' [W/cm²]")
    ax.set_title("Working-fluid comparison, plain copper (ΔT_sub = 10 K)")
    ax.legend(fontsize=8); ax.grid(which="both", alpha=0.25); ax.set_xlim(1, 40)
    fig.tight_layout(); fig.savefig(f"{path}/ev_fig4_fluids.png", dpi=140); plt.close(fig)

    # Fig 5: surface vs thermocouple temperature (1-D conduction offset)
    fig, ax = plt.subplots(figsize=(8, 5))
    q_arr = np.linspace(1, cur["q_chf"]/1e4 * 0.98, 100)
    Tsurf, Ttc = [], []
    for qv in q_arr:
        st = operating_point(qv, op, surf, bm)
        Tsurf.append(st["T_surf_C"]); Ttc.append(st["T_tc_C"])
    ax.plot(Tsurf, q_arr, lw=2.2, label="boiling surface T_surf")
    ax.plot(Ttc, q_arr, lw=2.2, ls="--", label=f"thermocouple ({surf.tc_depth*1e3:.0f} mm deep)")
    ax.axvline(op.fluid.T_sat - 273.15, color="r", ls=":", label="T_sat")
    ax.set_xlabel("temperature [°C]"); ax.set_ylabel("applied q'' [W/cm²]")
    ax.set_title("1-D chip-node conduction offset: T_surf vs embedded TC reading")
    ax.legend(fontsize=9); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(f"{path}/ev_fig5_tc_mapping.png", dpi=140); plt.close(fig)

    return [f"{path}/ev_fig1_boiling_curve.png", f"{path}/ev_fig2_subcooling.png",
            f"{path}/ev_fig3_chf_contact_angle.png", f"{path}/ev_fig4_fluids.png",
            f"{path}/ev_fig5_tc_mapping.png"]


# ----------------------------------------------------------------------
if __name__ == "__main__":
    surf = Surface(); bm = BoilingModel(); op = Operating(dT_sub=10.0)
    fl = op.fluid
    print("\nEVAPORATOR  --  plain copper, subcooled pool boiling")
    print("-" * 72)
    print(f"Fluid: {fl.name}  | T_sat {fl.T_sat-273.15:.1f} C | p_r {fl.p_r:.2e} | Pr_l {fl.Pr_l:.2f}")
    print(f"Surface: {surf.side*1e3:.0f}x{surf.side*1e3:.0f} mm, TC depth {surf.tc_depth*1e3:.0f} mm Cu | "
          f"subcooling {op.dT_sub:.0f} K | orientation {op.phi_deg:.0f} deg")
    print(f"Model: nucleate={bm.nucleate}, C_sf={bm.C_sf}, beta={bm.beta_deg} deg, "
          f"Rp={bm.Rp_um} um, CHF subcool={bm.subcool_chf} ({bm.C_sub_perK}/K)")

    cur = boiling_curve(op, surf, bm)
    print(f"\nBoiling curve:")
    print(f"  ONB onset superheat        : {cur['dT_onb']:.2f} K  at {cur['q_onb']/1e4:.2f} W/cm²")
    print(f"  CHF (saturated, Kandlikar) : {cur['q_chf_sat']/1e4:.2f} W/cm²  (coeff K={cur['K']:.4f})")
    print(f"  CHF (subcooled x{cur['f_sub']:.3f})    : {cur['q_chf']/1e4:.2f} W/cm²  at ΔT_sat≈{cur['dT_chf']:.1f} K")

    print(f"\nOperating points (applied flux -> wall state, with TC offset):")
    print(f"   {'q[W/cm2]':>9} {'dTsat[K]':>9} {'Tsurf[C]':>9} {'Ttc[C]':>8} {'h[W/m2K]':>10} {'CHF margin':>11}")
    for qv in [5, 10, 20, 30, 40]:
        st = operating_point(qv, op, surf, bm)
        if st.get("beyond_chf"):
            print(f"   {qv:9.1f}   ---- beyond CHF ({st['q_chf_Wcm2']:.1f} W/cm²) ----")
        else:
            print(f"   {qv:9.1f} {st['dT_sat']:9.2f} {st['T_surf_C']:9.2f} {st['T_tc_C']:8.2f} "
                  f"{st['h_boil']:10.0f} {st['margin_to_chf']:11.2f}")

    verify()

    # quick closed-loop demo using the condenser resistance from the earlier model
    print("\nClosed-loop demo (condenser R = 0.04 K/W, coolant 40 C):")
    arr = chamber_balance(surf, bm, fl, op.phi_deg, R_cond_KperW=0.04, T_coolant_C=40.0)
    if len(arr):
        for q, ds, ts, m in arr[::12]:
            print(f"   q={q:4.0f} W/cm²  ->  pool subcooling {ds:5.2f} K, "
                  f"T_surf {ts:5.1f} C, CHF margin {m:4.2f}")

    figs = make_plots()
    print("\nFigures:", *figs, sep="\n  ")
    print("\nDone.")
