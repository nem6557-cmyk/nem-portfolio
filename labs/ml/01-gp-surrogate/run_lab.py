"""ML-1: a Gaussian-process surrogate of the boiling chamber.

Trains a GP on the real 261-point experimental dataset (chip surface
temperature as a function of heat flux, coolant setpoint, condenser
generation, and surface type) and evaluates it the honest way:
5-fold cross-validation, so every prediction is out-of-fold. Two
questions: how close does a pure data model get to the physics-based
gray-box model (in-sample RMSE 4.34 K), and are its uncertainty bars
calibrated, i.e. does a claimed 95% interval actually cover 95%?
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel
from sklearn.model_selection import KFold
from scipy import stats

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
X = np.column_stack([
    df.q_Wcm2, df.coolant_setpoint_C,
    (df.condenser == "42-tube").astype(float),
    (df.chip == "microchannel").astype(float),
])
y = df.Tsurf_C.to_numpy()
mu_x, sd_x = X.mean(0), X.std(0)
Xs = (X - mu_x) / sd_x

kernel = (ConstantKernel(1.0, (0.05, 50))
          * RBF([1.0] * 4, (0.05, 30))
          + WhiteKernel(0.5, (1e-3, 50)))
pred = np.empty_like(y)
sig = np.empty_like(y)
for tr, te in KFold(5, shuffle=True, random_state=0).split(Xs):
    gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True,
                                  n_restarts_optimizer=2, random_state=0)
    gp.fit(Xs[tr], y[tr])
    pred[te], sig[te] = gp.predict(Xs[te], return_std=True)

rmse = float(np.sqrt(np.mean((pred - y) ** 2)))
mae = float(np.abs(pred - y).mean())
r2 = 1 - np.sum((pred - y) ** 2) / np.sum((y - y.mean()) ** 2)
z = (y - pred) / sig
cov95 = float(np.mean(np.abs(z) <= 1.96))
nom = np.linspace(0.05, 0.99, 30)
emp = [float(np.mean(np.abs(z) <= stats.norm.ppf(0.5 + c / 2))) for c in nom]

fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4), dpi=150)
o = np.argsort(y)
axes[0].errorbar(y[o][::4], pred[o][::4], yerr=1.96 * sig[o][::4], fmt="o",
                 ms=3.5, color=TEAL, ecolor=FAINT, elinewidth=0.8, capsize=0,
                 alpha=0.9)
lims = [y.min() - 3, y.max() + 3]
axes[0].plot(lims, lims, "--", color=FG, lw=1)
axes[0].set_xlabel("measured chip temperature (degC)")
axes[0].set_ylabel("GP out-of-fold prediction (degC)")
axes[0].set_title(f"5-fold CV: RMSE {rmse:.2f} K, R2 {r2:.3f}\n"
                  f"(gray-box physics model: 4.34 K in-sample)")
axes[1].plot(nom * 100, np.array(emp) * 100, color=ORANGE, lw=2.2)
axes[1].plot([0, 100], [0, 100], "--", color=FG, lw=1)
axes[1].set_xlabel("nominal interval coverage (%)")
axes[1].set_ylabel("empirical coverage (%)")
axes[1].set_title(f"Uncertainty calibration: 95% interval covers {cov95:.0%}")
fig.tight_layout()
for p in (ASSETS / "ml1-gp-surrogate.png", HERE / "ml1-gp-surrogate.png"):
    fig.savefig(p, bbox_inches="tight")

summary = (f"ML-1 GP surrogate, 5-fold CV on 261 real points: RMSE {rmse:.2f} K, "
           f"MAE {mae:.2f} K, R2 {r2:.3f}; 95% interval empirical coverage "
           f"{cov95:.1%}. Gray-box physics model reference: 4.34 K RMSE "
           f"(in-sample).\n")
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
