#!/bin/sh
# Build the coarse resolved 3D mesh and open-ready .foam file (NO solver). ~minutes on 1 core.
cd "${0%/*}" || exit 1
. "${WM_PROJECT_DIR:?}/bin/tools/RunFunctions"
cp system/snappyHexMeshDict.coarse system/snappyHexMeshDict
runApplication blockMesh
runApplication surfaceFeatureExtract || echo "(surfaceFeatureExtract skipped; using existing tubes.eMesh)"
runApplication snappyHexMesh -overwrite
runApplication topoSet            || echo "(topoSet skipped)"
runApplication createPatch -overwrite || echo "(createPatch skipped)"
runApplication checkMesh
touch case.foam
echo ""; echo "=== mesh built. Open case.foam in ParaView. Cell count: ==="
grep -m1 "cells:" log.checkMesh || grep -m1 "nCells" log.checkMesh || true
