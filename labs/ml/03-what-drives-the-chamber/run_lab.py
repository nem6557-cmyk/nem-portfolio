"""ML-3: what actually drives chip temperature, asked of the data.

A random forest on the same 261 real points, interrogated with
permutation importance and partial-dependence profiles. The physics
says heat flux should dominate, coolant setpoint second, geometry
third; this lab asks whether the data agrees. Two cross-validations
keep it honest: shuffled folds measure interpolation, and grouped
folds that hold out an entire configuration measure extrapolation.
The first run of this lab used unshuffled folds on the config-ordered
CSV by accident and scored R2 = 0: that pitfall is now the point. Association, not causation, and labeled as such.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance, partial_dependence
from sklearn.model_selection import cross_val_score, KFold, GroupKFold

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ASSETS = REPO / "site" / "assets"
BG, FG, GRID = "#ffffff", "#17212F", "#D9E2EC"
TEAL, ORANGE, FAINT = "#0F766E", "#C2410C", "#8593A8"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.45,
})

df = pd.read_csv(REPO / "research/chamber-model/editable_schematics_and_csv"
                        "/data_csv/experimental_data_all_points.csv")
feats = ["heat flux q''", "coolant setpoint", "condenser gen", "surface type"]
X = np.column_stack([
    df.q_Wcm2, df.coolant_setpoint_C,
    (df.condenser == "42-tube").astype(float),
    (df.chip == "microchannel").astype(float),
])
y = df.Tsurf_C.to_numpy()

rf = RandomForestRegressor(400, random_state=0, min_samples_leaf=2)
cv = cross_val_score(rf, X, y, scoring="r2",
                     cv=KFold(5, shuffle=True, random_state=0))
groups = (df.condenser + "/" + df.chip).to_numpy()
cv_grp = cross_val_score(rf, X, y, scoring="r2", groups=groups,
                         cv=GroupKFold(4))
rf.fit(X, y)
pi = permutation_importance(rf, X, y, n_repeats=30, random_state=0)

fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.0), dpi=150)
order = np.argsort(pi.importances_mean)
axes[0].barh(np.array(feats)[order], pi.importances_mean[order],
             xerr=pi.importances_std[order], color=TEAL, ecolor=FAINT)
axes[0].set_xlabel("permutation importance (delta R2)")
axes[0].set_title(f"What the forest leans on\nshuffled CV R2 "
                  f"{cv.mean():.3f}; leave-config-out {cv_grp.mean():.2f}")
for ax, fi, name, c in ((axes[1], 0, "heat flux (W/cm2)", ORANGE),
                        (axes[2], 1, "coolant setpoint (degC)", TEAL)):
    pd_res = partial_dependence(rf, X, [fi], grid_resolution=40)
    ax.plot(pd_res["grid_values"][0], pd_res["average"][0], color=c, lw=2.4)
    ax.set_xlabel(name); ax.set_ylabel("partial dependence of T_chip (degC)")
axes[1].set_title("Flux drives temperature, sub-linearly")
axes[2].set_title("Coolant shifts the whole curve")
fig.tight_layout()
for p in (ASSETS / "ml3-drivers.png", HERE / "ml3-drivers.png"):
    fig.savefig(p, bbox_inches="tight")

top = np.array(feats)[np.argmax(pi.importances_mean)]
summary = (f"ML-3 drivers, RF on 261 real points: shuffled 5-fold CV R2 "
           f"{cv.mean():.3f} +/- {cv.std():.3f}; leave-one-configuration-out "
           f"R2 {cv_grp.mean():.2f} +/- {cv_grp.std():.2f} (interpolation is "
           f"easy, extrapolating to an unseen configuration is not); "
           f"permutation importance "
           + ", ".join(f"{f}: {m:.3f}" for f, m in
                       zip(feats, pi.importances_mean))
           + f". Dominant driver: {top}. Association, not causation.\n")
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
