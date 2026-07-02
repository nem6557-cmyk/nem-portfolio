#!/bin/sh
# Run ONE chamber42_2d operating point (foreground, no nohup -> no double-launch risk).
# Usage:  ./runpoint.sh <Twall_C> <coeffE> [endTime=0.10] [coeffC=1.0]
# Writes its own subdir runpoint_Tw<..>_E<..>/ and reports the quasi-steady chip flux.
cd "${0%/*}" || exit 1
. "${WM_PROJECT_DIR:?}/bin/tools/RunFunctions"
TwC=${1:?usage: ./runpoint.sh Twall_C coeffE [endTime] [coeffC]}
cE=${2:?usage: ./runpoint.sh Twall_C coeffE [endTime] [coeffC]}
tEnd=${3:-0.10}; cC=${4:-1.0}
TwK=$(awk "BEGIN{printf \"%.2f\", $TwC+273.15}")
S=runpoint_Tw${TwC}_E${cE}
echo ">> $S : Twall=${TwC}C (${TwK}K)  coeffE=${cE}  coeffC=${cC}  endTime=${tEnd}s"
rm -rf "$S"; mkdir -p "$S"; cp -r 0.orig constant system "$S"/; cd "$S"
sed -i "s/value uniform 358/value uniform ${TwK}/" 0.orig/T
cat > constant/phaseChangeProperties <<EOF2
FoamFile { version 2.0; format ascii; class dictionary; object phaseChangeProperties; }
phaseChangeTwoPhaseModel constant;
constantCoeffs { coeffC coeffC [0 0 -1 -1 0 0 0] ${cC}; coeffE coeffE [0 0 -1 -1 0 0 0] ${cE}; }
EOF2
foamDictionary -entry endTime       -set "${tEnd}" system/controlDict >/dev/null
foamDictionary -entry writeInterval  -set "${tEnd}" system/controlDict >/dev/null
runApplication blockMesh
runApplication checkMesh
cp -r 0.orig 0
runApplication setFields
runApplication "$(getApplication)"
echo "----- $S result -----"
python3 - <<'PY'
import numpy as np
rows=[l.split() for l in open("chipHeatFlux.dat") if l.strip() and not l.startswith("#")]
a=np.array(rows,float)
if len(a)<2:
    print("only %d sample(s) in chipHeatFlux.dat -- run longer"%len(a)); raise SystemExit
t,q=a[:,0],a[:,2]; n0=int(len(q)*0.7)
print("steady q'' (last 30%% mean) = %.3f W/cm2   [t=%.4f..%.4f s, %d samples]"%(q[n0:].mean(),t[0],t[-1],len(q)))
print("min q'' over run          = %.3f W/cm2   (collapse toward ~0 => film boiling)"%q.min())
print("last sample q''           = %.3f W/cm2"%q[-1])
PY
