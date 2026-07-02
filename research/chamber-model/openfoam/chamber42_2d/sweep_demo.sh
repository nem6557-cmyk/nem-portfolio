#!/bin/sh
# Fixed-duration nucleate-branch sweep for the chamber42_2d DEMONSTRATION.
# Runs every wall temperature for the SAME sim time at one coeffE, and records the
# chip flux at that fixed time. These are explicitly NOT converged boiling-curve
# points -- the bulk pool warm-up is a seconds-scale transient (see report) -- they
# demonstrate the sweep mechanism and the correct monotonic trend vs the measured curve.
# Usage:  ./sweep_demo.sh <coeffE> [endTime=0.10] [coeffC=1.0]
cd "${0%/*}" || exit 1
. "${WM_PROJECT_DIR:?}/bin/tools/RunFunctions"
cE=${1:?usage: ./sweep_demo.sh coeffE [endTime] [coeffC]}
tEnd=${2:-0.10}; cC=${3:-1.0}
WALLS="52 58 65 72 78"          # nucleate branch, below the ~79C / 65 W/cm2 CHF ceiling
OUT=sweep_demo_E${cE}.csv
echo "# chamber42_2d fixed-time sweep  coeffE=${cE} coeffC=${cC} endTime=${tEnd}s" > "$OUT"
echo "# Twall_C,q_Wcm2_at_tEnd,min_q_Wcm2,n_samples  (NON-converged, fixed sim time)" >> "$OUT"
for Tw in $WALLS; do
    echo "================ sweep point Twall=${Tw}C ================"
    ./runpoint.sh "$Tw" "$cE" "$tEnd" "$cC"
    D=runpoint_Tw${Tw}_E${cE}
    python3 - "$D/chipHeatFlux.dat" "$Tw" >> "$OUT" <<'PY'
import sys, numpy as np
dat, Tw = sys.argv[1], sys.argv[2]
a=np.array([l.split() for l in open(dat) if l.strip() and not l.startswith("#")],float)
q=a[:,2]; n0=int(len(q)*0.7)
print("%s,%.3f,%.3f,%d"%(Tw, q[n0:].mean(), q.min(), len(q)))
PY
done
echo ""; echo "=== sweep complete -> $OUT ==="; cat "$OUT"
