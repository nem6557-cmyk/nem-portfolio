#!/bin/sh
# Quick sanity check for chamber42_2d: builds the mesh, checks it, runs the solver
# for a very short time, and verifies the chip heat-flux probe writes output.
# Runs in a throwaway sibling dir (../chamber42_2d_smoke) so the base case stays clean.
cd "${0%/*}" || exit 1
. "${WM_PROJECT_DIR:?}/bin/tools/RunFunctions"

S=../chamber42_2d_smoke
echo ">> setting up throwaway copy at $S"
rm -rf "$S"; mkdir -p "$S"
cp -r 0.orig constant system "$S"/
cd "$S"

runApplication blockMesh
runApplication checkMesh
cp -r 0.orig 0
runApplication setFields
# short run: enough steps to load the phase-change model, compile the coded probe, take a few steps
foamDictionary -entry endTime       -set 2e-4 system/controlDict >/dev/null
foamDictionary -entry writeInterval  -set 2e-4 system/controlDict >/dev/null
APP=$(getApplication)
runApplication "$APP"

echo ""
echo "================== SMOKE RESULT =================="
[ -f log.blockMesh ] && { grep -q "^End" log.blockMesh && echo "[ok]   blockMesh built the mesh" || echo "[FAIL] blockMesh -- see $S/log.blockMesh"; }
if [ -f log.checkMesh ]; then
    if grep -q "Mesh OK" log.checkMesh; then echo "[ok]   checkMesh: Mesh OK"
    else echo "[warn] checkMesh flagged something -- see $S/log.checkMesh"; fi
fi
[ -f "log.$APP" ] && { grep -q "^End" "log.$APP" && echo "[ok]   solver started and reached the short End" || echo "[FAIL] solver did not finish -- tail -40 $S/log.$APP"; }
if [ -f chipHeatFlux.dat ]; then
    echo "[ok]   chipHeatFlux.dat written ( time  q[W/m2]  q[W/cm2]  Q[W] ):"
    head -2 chipHeatFlux.dat | sed 's/^/         /'
    echo "         ..."
    tail -2 chipHeatFlux.dat | sed 's/^/         /'
else
    echo "[FAIL] chipHeatFlux.dat NOT written -- the coded probe likely failed to compile;"
    echo "       look for 'codeWrite' errors near the top of $S/log.$APP"
fi
echo "================================================="
echo "(throwaway copy left at $S for inspection; delete with: rm -rf $S)"
