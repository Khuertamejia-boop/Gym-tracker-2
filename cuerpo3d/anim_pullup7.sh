#!/bin/bash
# FINAL pull-up frame F of N:
#  1) pullup6.py: anatomical arm (pure-hinge elbow, optimised elbow direction, forearm twist bones), centre-of-rotation
#     skinning around the shoulders with the deltoid cap turning about the real joint centre (SPH)
#  2) arap2.py IT=1: the shoulder skin keeps its REST relief, turned by the blended bone rotations (Laplacian editing),
#     fading out smoothly (RIN -> RAD) -> no crease between the deltoid and the arm, no "shoulder pad"
# output: w/NBk<F>.blend (baked mesh)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
set -a; . $S/agarre_final.env; set +a
export SKIN=cor TW=0 SPH=1 SR0=0.08 SR1=0.15
F=$1; N=$2; T=$(printf "%02d" $F); PF=${PFX:-NBk}
P=${PP:-$(python3 -c "import math;print(round(0.5-0.5*math.cos(2*math.pi*$F/$N),4))")}
P=$P $S/venv/bin/python -I $S/pullup6.py ${BASEB:-NB_s.blend} ${PF}_s$T.blend > r/log_${PF}$T.txt 2>&1
RESTBLEND=${BASEB:-NB_s.blend} IT=1 RAD=${LRAD:-0.22} RIN=${LRIN:-0.12} $S/venv/bin/python -I $S/arap2.py ${PF}_s$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
rm -f ${PF}_s$T.blend
echo done $T P=$P
