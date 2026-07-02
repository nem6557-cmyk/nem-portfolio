"""Finish project 3 after an interrupted run: the shaped policy and its
eval curve already exist (results/p3_shaped_curve.npz, rescued from the
training log); this script trains the sparse arm of the ablation at the
identical budget, then writes the combined p3_curves.npz and summary."""
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_p3 import train, RES, TOTAL_STEPS

if __name__ == "__main__":
    shaped = np.load(RES / "p3_shaped_curve.npz")
    _, s, sr, md = train("sparse")
    out = {
        "shaped_steps": shaped["steps"], "shaped_succ": shaped["succ"],
        "shaped_med_mm": shaped["med_mm"],
        "sparse_steps": s, "sparse_succ": sr, "sparse_med_mm": md,
    }
    np.savez(RES / "p3_curves.npz", **out)
    with open(RES / "summary.txt", "w") as fh:
        fh.write("Project 3 summary: reward shaping ablation\n")
        fh.write(f"training budget per run: {TOTAL_STEPS} steps\n")
        fh.write(f"final eval success, shaped: {out['shaped_succ'][-1]:.1%}\n")
        fh.write(f"final median hold, shaped: {out['shaped_med_mm'][-1]:.1f} mm\n")
        fh.write(f"best eval success, shaped: {out['shaped_succ'].max():.1%}\n")
        fh.write(f"final eval success, sparse: {out['sparse_succ'][-1]:.1%}\n")
        fh.write(f"final median hold, sparse: {out['sparse_med_mm'][-1]:.1f} mm\n")
    print(open(RES / "summary.txt").read())
