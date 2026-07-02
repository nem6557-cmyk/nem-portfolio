"""ML-2: a physics-informed neural network earns its error bars.

Solves 1D transient conduction in a slab with fixed-temperature faces
and a uniform hot initial condition, using the effective thermal
diffusivity tuned in the cardiac-ablation bioheat validation
(alpha = 1.447e-7 m2/s). Three solvers answer the same question:
the exact Fourier series, Crank-Nicolson finite differences, and a
PINN trained only on the PDE residual and boundary/initial data.
The exact solution grades the other two.
"""
from pathlib import Path
import time
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

torch.manual_seed(0)
HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "site" / "assets"
BG, FG, GRID = "#ffffff", "#17212F", "#D9E2EC"
TEAL, ORANGE, FAINT = "#0F766E", "#C2410C", "#8593A8"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.45,
})

ALPHA, L = 1.447e-7, 0.010            # m2/s (bioheat-tuned), 10 mm slab
TAU = L**2 / ALPHA                    # diffusion time 691 s
SNAP = [0.02, 0.10, 0.40]             # in units of tau

def exact(x, tt, n_terms=400):
    """theta(x,t): faces at 0, IC = 1."""
    out = np.zeros_like(x)
    for n in range(1, n_terms + 1, 2):
        out += (4 / (np.pi * n) * np.sin(n * np.pi * x)
                * np.exp(-(n * np.pi) ** 2 * tt))
    return out

# ---- Crank-Nicolson baseline -------------------------------------------
nx, nt = 201, 4000
xg = np.linspace(0, 1, nx); dx = xg[1] - xg[0]
dt = max(SNAP) / nt
r = dt / dx**2
main = np.full(nx, 1 + r); off = np.full(nx - 1, -r / 2)
A = np.diag(main) + np.diag(off, 1) + np.diag(off, -1)
B = np.diag(np.full(nx, 1 - r)) + np.diag(-off, 1) + np.diag(-off, -1)
A[0, :] = 0; A[0, 0] = 1; A[-1, :] = 0; A[-1, -1] = 1
B[0, :] = 0; B[-1, :] = 0
Ainv = np.linalg.inv(A)
u = np.ones(nx); u[0] = u[-1] = 0
cn = {}
t0 = time.time()
tcur = 0.0
for k in range(nt):
    u = Ainv @ (B @ u); tcur += dt
    for s in SNAP:
        if abs(tcur - s) < dt / 2:
            cn[s] = u.copy()
t_cn = time.time() - t0

# ---- PINN ----------------------------------------------------------------
class Net(torch.nn.Module):
    def __init__(s):
        super().__init__()
        s.f = torch.nn.Sequential(
            torch.nn.Linear(2, 64), torch.nn.Tanh(),
            torch.nn.Linear(64, 64), torch.nn.Tanh(),
            torch.nn.Linear(64, 64), torch.nn.Tanh(),
            torch.nn.Linear(64, 1))
    def forward(s, x, t):
        # hard-encode the boundary conditions: theta = x(1-x) * N(x,t)
        return x * (1 - x) * s.f(torch.cat([x, t], 1))

net = Net()
opt = torch.optim.Adam(net.parameters(), lr=2e-3)
t0 = time.time()
for it in range(3000):
    opt.zero_grad()
    x = torch.rand(2048, 1, requires_grad=True)
    t = torch.rand(2048, 1, requires_grad=True) * max(SNAP)
    th = net(x, t)
    dth_t = torch.autograd.grad(th, t, torch.ones_like(th), create_graph=True)[0]
    dth_x = torch.autograd.grad(th, x, torch.ones_like(th), create_graph=True)[0]
    dth_xx = torch.autograd.grad(dth_x, x, torch.ones_like(dth_x),
                                 create_graph=True)[0]
    pde = ((dth_t - dth_xx) ** 2).mean()
    xi = torch.rand(512, 1)
    ic = ((net(xi, torch.zeros_like(xi)) - 1.0) ** 2).mean()
    loss = pde + 20 * ic
    loss.backward(); opt.step()
t_pinn = time.time() - t0

xt = torch.linspace(0, 1, 401).reshape(-1, 1)
pinn = {s: net(xt, torch.full_like(xt, s)).detach().numpy().ravel()
        for s in SNAP}
xg2 = xt.numpy().ravel()

errs = {}
for s in SNAP:
    ex_cn = exact(xg, s); ex_p = exact(xg2, s)
    errs[s] = (np.abs(cn[s] - ex_cn).max(), np.abs(pinn[s] - ex_p).max())

fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.2), dpi=150)
for s, c in zip(SNAP, (TEAL, ORANGE, FAINT)):
    axes[0].plot(xg2, exact(xg2, s), color=c, lw=2.4,
                 label=f"exact, t = {s:.2f} tau")
    axes[0].plot(xg2, pinn[s], "--", color=FG, lw=1.2)
    axes[0].plot(xg[::10], cn[s][::10], "o", color=c, ms=3)
axes[0].set_xlabel("x / L"); axes[0].set_ylabel("theta")
axes[0].set_title("Exact series (solid), PINN (dashed), Crank-Nicolson (dots)")
axes[0].legend(framealpha=0.15, fontsize=9)
labels = [f"t={s:.2f}tau" for s in SNAP]
w = 0.38; xb = np.arange(3)
axes[1].bar(xb - w/2, [errs[s][0] * 1e3 for s in SNAP], w, color=TEAL,
            label=f"Crank-Nicolson ({t_cn:.1f} s)")
axes[1].bar(xb + w/2, [errs[s][1] * 1e3 for s in SNAP], w, color=ORANGE,
            label=f"PINN ({t_pinn:.0f} s train)")
axes[1].set_xticks(xb); axes[1].set_xticklabels(labels)
axes[1].set_ylabel("max abs error (x 1e-3)")
axes[1].set_title("Error vs the exact solution")
axes[1].legend(framealpha=0.15, fontsize=9)
fig.tight_layout()
for p in (ASSETS / "ml2-pinn.png", HERE / "ml2-pinn.png"):
    fig.savefig(p, bbox_inches="tight")

worst_pinn = max(e[1] for e in errs.values())
worst_cn = max(e[0] for e in errs.values())
summary = (f"ML-2 PINN vs exact (alpha = 1.447e-7 m2/s from the bioheat "
           f"validation, 10 mm slab): PINN worst max-error "
           f"{worst_pinn:.2e} in theta, CN baseline {worst_cn:.2e}; "
           f"PINN trained {t_pinn:.0f} s on CPU, CN ran {t_cn:.1f} s. "
           f"Snapshot errors (CN, PINN): "
           + "; ".join(f"t={s:.2f}tau: {errs[s][0]:.1e}, {errs[s][1]:.1e}"
                       for s in SNAP) + "\n")
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
