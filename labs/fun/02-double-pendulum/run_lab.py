"""FUN-2: the double pendulum, chaos measured not just admired.

Equal-mass, equal-length double pendulum integrated with vectorized
RK4. Three deliverables: (1) a Lyapunov exponent measured by the
Benettin renormalization method on a twin trajectory, (2) the
divergence of two starts separated by one nanoradian, and (3) a
time-to-flip map over a grid of initial angles, the fractal fingerprint
that says which initial conditions lead to a somersault and how soon.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "site" / "assets"
BG, FG, GRID = "#0e1626", "#dbe4f0", "#22304a"
TEAL, ORANGE, FAINT = "#4FD1C5", "#FF8A5B", "#7083A6"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.4,
})
G = 9.81

def deriv(s):
    """s = (4, N): th1, th2, w1, w2. Equal m, equal L = 1."""
    th1, th2, w1, w2 = s
    d = th1 - th2
    cd, sd = np.cos(d), np.sin(d)
    den = 2 - cd * cd
    a1 = (-sd * (w2**2 + w1**2 * cd) - G * (2 * np.sin(th1)
          - np.sin(th2) * cd)) / den
    a2 = (sd * (2 * w1**2 + w2**2 * cd) + G * 2 * (np.sin(th1) * cd
          - np.sin(th2))) / den
    return np.stack([w1, w2, a1, a2])

def rk4(s, dt, steps, record=None):
    out = []
    for k in range(steps):
        k1 = deriv(s); k2 = deriv(s + dt/2 * k1)
        k3 = deriv(s + dt/2 * k2); k4 = deriv(s + dt * k3)
        s = s + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        if record is not None:
            record(k, s)
    return s

dt = 0.002
# ---- Lyapunov via Benettin ------------------------------------------------
def energy(s):
    th1, th2, w1, w2 = s
    T = w1**2 + 0.5 * w2**2 + w1 * w2 * np.cos(th1 - th2)
    V = -G * (2 * np.cos(th1) + np.cos(th2))
    return T + V

s0 = np.array([[2.0], [2.0], [0.0], [0.0]])
E0 = float(energy(s0)[0])
d0 = 1e-9
s = np.concatenate([s0, s0 + np.array([[d0], [0], [0], [0]])], axis=1)
interval, n_int = 0.5, 80
stretches = []
sep_t, sep_v = [], []
for i in range(n_int):
    s = rk4(s, dt, int(interval / dt))
    diff = s[:, 1] - s[:, 0]
    dist = np.linalg.norm(diff)
    stretches.append(np.log(dist / d0))
    sep_t.append((i + 1) * interval); sep_v.append(dist)
    s[:, 1] = s[:, 0] + diff * (d0 / dist)      # renormalize
lam = np.sum(stretches) / (n_int * interval)
E_drift = abs(float(energy(s[:, :1])[0]) - E0) / abs(E0)

# ---- flip map --------------------------------------------------------------
n = 121
th1g, th2g = np.meshgrid(np.linspace(-np.pi, np.pi, n),
                         np.linspace(-np.pi, np.pi, n))
S = np.stack([th1g.ravel(), th2g.ravel(),
              np.zeros(n * n), np.zeros(n * n)])
flip = np.full(n * n, np.nan)
T_MAX, DT2 = 25.0, 0.004
th2_unwrapped = S[1].copy()
def rec(k, s):
    global flip
    new = np.isnan(flip) & (np.abs(s[1] - th2g.ravel()) > np.pi)
    flip[new] = (k + 1) * DT2
rk4(S, DT2, int(T_MAX / DT2), record=rec)
flip = flip.reshape(n, n)

fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.6), dpi=150)
axes[0].semilogy(sep_t, sep_v, color=TEAL, lw=2)
axes[0].semilogy(sep_t, d0 * np.exp(lam * np.array(sep_t)), "--",
                 color=ORANGE, lw=1.6,
                 label=f"exp fit: lambda = {lam:.2f} /s")
axes[0].set_xlabel("time (s)")
axes[0].set_ylabel("separation of twin trajectories (rad)")
axes[0].set_title("One nanoradian apart at t = 0")
axes[0].legend(framealpha=0.15)
im = axes[1].imshow(flip, origin="lower", cmap="turbo",
                    extent=[-np.pi, np.pi, -np.pi, np.pi], aspect="auto")
axes[1].set_xlabel("theta1 (rad)"); axes[1].set_ylabel("theta2 (rad)")
axes[1].set_title("Time until the second arm flips (blank = never in 25 s)")
cb = fig.colorbar(im, ax=axes[1], shrink=0.9)
cb.set_label("s", color=FG); cb.ax.yaxis.set_tick_params(color=FG)
plt.setp(cb.ax.get_yticklabels(), color=FG)
fig.tight_layout()
for p in (ASSETS / "f2-pendulum.png", HERE / "f2-pendulum.png"):
    fig.savefig(p, bbox_inches="tight")

frac = float(np.mean(~np.isnan(flip)))
summary = (f"FUN-2 double pendulum: Lyapunov exponent {lam:.2f} /s (Benettin, "
           f"80 renormalizations), doubling time {np.log(2)/lam:.2f} s; "
           f"{frac:.0%} of the {n}x{n} initial-angle grid flips within 25 s. "
           f"Measured energy drift on the 40 s reference trajectory: "
           f"{E_drift:.2e} relative (RK4, dt = {dt}).\n")
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
