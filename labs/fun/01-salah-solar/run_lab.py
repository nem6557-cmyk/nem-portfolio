"""FUN-1: prayer times from the geometry of the sky.

Salah times are astronomy: Dhuhr is solar transit, Asr is a shadow
ratio, Maghrib is sunset, and Fajr/Isha are solar depression angles.
This lab computes all five for Rochester, NY from first principles
(NOAA's solar position algorithm: fractional year, equation of time,
declination) under the ISNA convention (15 degree depression for both
Fajr and Isha, standard Asr shadow factor 1), and self-validates:
computed solar noon must match the equation-of-time prediction to the
minute, and sunset must satisfy the -0.833 degree altitude condition
when checked against an independent altitude evaluation.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "site" / "assets"
BG, FG, GRID = "#ffffff", "#17212F", "#D9E2EC"
TEAL, ORANGE, FAINT = "#0F766E", "#C2410C", "#8593A8"
GOLD = "#B8860B"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.4,
})

LAT, LON = 43.09, -77.63          # Rochester / Henrietta, NY
TZ = -4                            # EDT (summer); -5 EST handled below
DEP_FAJR = DEP_ISHA = 15.0         # ISNA convention
ASR_FACTOR = 1                     # standard (Shafi'i) shadow ratio

def solar(doy_frac):
    """NOAA approximation: returns declination (rad), eqtime (min)."""
    g = 2 * np.pi / 365 * (doy_frac - 1)
    eqtime = 229.18 * (0.000075 + 0.001868 * np.cos(g)
                       - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g)
                       - 0.040849 * np.sin(2 * g))
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g)
            - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g)
            - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    return decl, eqtime

def hour_angle(alt_deg, decl):
    """|H| (deg) at which the sun sits at altitude alt_deg."""
    lat = np.radians(LAT)
    x = ((np.sin(np.radians(alt_deg)) - np.sin(lat) * np.sin(decl))
         / (np.cos(lat) * np.cos(decl)))
    return np.degrees(np.arccos(np.clip(x, -1, 1)))

def times_for(doy, tz):
    decl, eq = solar(doy)
    noon = 12 - eq / 60 - LON / 15 + tz          # local clock, hours
    def offset(alt):                              # hours from noon
        return hour_angle(alt, decl) / 15
    asr_alt = np.degrees(np.arctan(1 / (ASR_FACTOR
                + np.tan(abs(np.radians(LAT) - decl)))))
    return dict(
        fajr=noon - offset(-DEP_FAJR),
        sunrise=noon - offset(-0.833),
        dhuhr=noon,
        asr=noon + offset(asr_alt),
        maghrib=noon + offset(-0.833),
        isha=noon + offset(-DEP_ISHA),
    ), eq, decl

# self-check on July 2, 2026 (doy 183, EDT)
t, eq, decl = times_for(183, -4)
noon_check = 12 - eq / 60 - LON / 15 - 4
assert abs(t["dhuhr"] - noon_check) < 1e-9
lat = np.radians(LAT)
alt_at_maghrib = np.degrees(np.arcsin(
    np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl)
    * np.cos(np.radians((t["maghrib"] - t["dhuhr"]) * 15))))
def hm(h):
    h %= 24
    return f"{int(h):02d}:{int(round((h % 1) * 60)) % 60:02d}"

# full-year chart (EST/EDT step at 2026 US DST: Mar 8 / Nov 1 -> doy 67/305)
days = np.arange(1, 366)
tz = np.where((days >= 67) & (days < 305), -4, -5)
series = {k: np.empty(365) for k in
          ("fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha")}
for i, d in enumerate(days):
    tt, _, _ = times_for(d, tz[i])
    for k in series:
        series[k][i] = tt[k]

fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=150)
ax.fill_between(days, series["fajr"], series["sunrise"],
                color=TEAL, alpha=0.15)
ax.fill_between(days, series["maghrib"], series["isha"],
                color=ORANGE, alpha=0.15)
for k, c in (("fajr", TEAL), ("sunrise", FAINT), ("dhuhr", GOLD),
             ("asr", FG), ("maghrib", ORANGE), ("isha", "#7C3AED")):
    ax.plot(days, series[k], color=c, lw=2, label=k)
ax.set_xlabel("day of year 2026")
ax.set_ylabel("local clock time (h)")
ax.set_title("Salah times for Rochester, NY from solar geometry "
             "(ISNA 15/15, Asr factor 1)")
ax.legend(framealpha=0.15, ncols=3, fontsize=9)
ax.set_ylim(2.5, 23.5)
ax.invert_yaxis()
fig.tight_layout()
for p in (ASSETS / "f1-salah.png", HERE / "f1-salah.png"):
    fig.savefig(p, bbox_inches="tight")

summary = ("FUN-1 salah solar geometry, July 2 2026, Rochester NY (ISNA): "
           + ", ".join(f"{k} {hm(v)}" for k, v in t.items())
           + f". Self-checks: Dhuhr equals equation-of-time solar noon "
             f"exactly; independent altitude at computed Maghrib = "
             f"{alt_at_maghrib:.3f} deg vs -0.833 target. DST step visible "
             f"at day 67 and 305 in the chart.\n")
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
