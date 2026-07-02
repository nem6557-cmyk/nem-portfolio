#!/bin/sh
# Build coarse mesh, run a SHORT early-transient solve, export VTK + .foam for ParaView.
# Usage: ./run_coarse.sh [endTime=0.0008]
# NOTE: at this mesh/time the boiling is barely developed -- this is an early-transient
# visualisation of the apparatus and initial fields, NOT a converged boiling result.
cd "${0%/*}" || exit 1
. "${WM_PROJECT_DIR:?}/bin/tools/RunFunctions"
tEnd=${1:-0.0008}
cp system/snappyHexMeshDict.coarse system/snappyHexMeshDict
runApplication blockMesh
runApplication surfaceFeatureExtract || echo "(using existing tubes.eMesh)"
runApplication snappyHexMesh -overwrite
runApplication topoSet            || echo "(topoSet skipped)"
runApplication createPatch -overwrite || echo "(createPatch skipped)"
runApplication checkMesh
foamDictionary -entry endTime -set "${tEnd}" system/controlDict >/dev/null
runApplication setFields
runApplication "$(getApplication)"
runApplication foamToVTK
touch case.foam
echo ""; echo "=== done. ParaView: open case.foam, or the VTK/ folder. Times written: ==="
ls -d [0-9]* 2>/dev/null | tr '\n' ' '; echo
