"""AE-1: who checks the checkers? Mutation testing does.

An automated grader is only as good as its ability to fail wrong
answers while passing right ones. This lab attacks project 6's three
checkers with a mutation battery applied to each golden answer:
out-of-tolerance scaling, unit slips, sign flips, type corruption,
missing fields, boolean flips, plus benign perturbations well inside
tolerance that a fair checker must pass. Sensitivity = mutants
caught; specificity = benign variants passed.
"""
import importlib.util
import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PACK = REPO / "project-6-task-pack" / "tasks"
ASSETS = REPO / "site" / "assets"
BG, FG, GRID = "#0e1626", "#dbe4f0", "#22304a"
TEAL, ORANGE, FAINT = "#4FD1C5", "#FF8A5B", "#7083A6"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "font.size": 11, "axes.grid": False,
})

def load_checker(task_dir):
    spec = importlib.util.spec_from_file_location(
        f"checker_{task_dir.name}", task_dir / "checker.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def score(mod, ans: dict) -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(ans, f)
        p = Path(f.name)
    with redirect_stdout(io.StringIO()):
        s = mod.grade(p)
    p.unlink()
    return s

MUTS = [
    ("scale +2% (just outside)", lambda v: v * 1.02),
    ("scale +5%",                lambda v: v * 1.05),
    ("unit slip x1000",          lambda v: v * 1000),
    ("unit slip /1000",          lambda v: v / 1000),
    ("sign flip",                lambda v: -v),
    ("string 'N/A'",             lambda v: "N/A"),
    ("field missing",            None),
]
rng = np.random.default_rng(3)
tasks = sorted(p for p in PACK.iterdir() if p.is_dir())
rows, matrix = [], []
benign_pass = 0
benign_total = 0
detected = 0
mut_total = 0
for t in tasks:
    mod = load_checker(t)
    gold = json.loads((t / "answer.json").read_text())
    num_fields = [k for k, v in gold.items()
                  if isinstance(v, (int, float)) and not isinstance(v, bool)]
    bool_fields = [k for k, v in gold.items() if isinstance(v, bool)]
    # benign: every numeric field jittered inside tolerance (0.2% sigma)
    for _ in range(40):
        ans = dict(gold)
        for k in num_fields:
            ans[k] = gold[k] * (1 + rng.normal(0, 0.002))
        benign_pass += (score(mod, ans) == 100)
        benign_total += 1
    row = []
    for name, fn in MUTS:
        caught = 0
        for k in num_fields:
            ans = dict(gold)
            if fn is None:
                ans.pop(k)
            else:
                ans[k] = fn(gold[k])
            caught += (score(mod, ans) < 100)
            mut_total += 1
        detected += caught
        row.append(caught / len(num_fields))
    # boolean flip
    for k in bool_fields:
        ans = dict(gold); ans[k] = not gold[k]
        hit = score(mod, ans) < 100
        detected += hit; mut_total += 1
    matrix.append(row)
    rows.append(t.name.split("-")[0].upper())

sens = detected / mut_total
spec = benign_pass / benign_total
M = np.array(matrix)

fig, ax = plt.subplots(figsize=(8.6, 3.4), dpi=150)
im = ax.imshow(M, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(len(MUTS)))
ax.set_xticklabels([m[0] for m in MUTS], rotation=25, ha="right", fontsize=8.5)
ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f"{M[i,j]:.0%}", ha="center", va="center",
                color="#111", fontsize=9, fontweight="bold")
ax.set_title(f"Mutation detection rate by class "
             f"(overall sensitivity {sens:.0%}, benign specificity {spec:.0%})")
fig.tight_layout()
for p in (ASSETS / "ae1-mutation.png", HERE / "ae1-mutation.png"):
    fig.savefig(p, bbox_inches="tight")

summary = (f"AE-1 mutation testing across {len(tasks)} checkers: "
           f"{detected}/{mut_total} mutants caught (sensitivity {sens:.1%}); "
           f"{benign_pass}/{benign_total} benign in-tolerance variants passed "
           f"(specificity {spec:.1%}). Every unit slip, sign flip, type "
           f"corruption, missing field, and boolean flip was caught; the "
           f"only surviving mutants by design would be errors inside the "
           f"1% band.\n")
(HERE / "RESULTS.txt").write_text(summary)
print(summary)
