#!/bin/bash
# pull-up (dominada) frame F of N with the current man (face, v17 neck), 15-11-2026:
#   pullup6.py (anatomical arm, wide overhand grip on the bar, CoR skinning) -> arap2.py (shoulder skin keeps its relief)
#   -> dominadas_geo.py (pull-up station)          P = 0.5 - 0.5 cos(2 pi F / N): 0 dead hang -> 1 chin over the bar
# output: w/<PFX><F>.blend     base: BASEB (NB_mc_row3.blend)
S=${GT3D:?set GT3D}; cd $S/w
set -a; . $S/agarre_final.env; set +a
export SKIN=cor TW=0 SPH=1 SR0=0.08 SR1=0.15 CMASK=0
F=$1; N=$2; T=$(printf "%02d" $F); PF=${PFX:-DM}; B=${BASEB:-NB_mc_row3.blend}; PY="$S/venv/bin/python -I"
P=${PP:-$(python3 -I -c "import math;print(round(0.5-0.5*math.cos(2*math.pi*$F/$N),4))")}
P=$P $PY $S/pullup6.py $B ${PF}_s$T.blend > r/log_${PF}$T.txt 2>&1
RESTBLEND=$B IT=1 RAD=${LRAD:-0.22} RIN=${LRIN:-0.12} $PY $S/arap2.py ${PF}_s$T.blend ${PF}_a$T.blend >> r/log_${PF}$T.txt 2>&1
$PY $S/dominadas_geo.py ${PF}_a$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
rm -f ${PF}_s$T.blend ${PF}_a$T.blend; echo done $T P=$P
