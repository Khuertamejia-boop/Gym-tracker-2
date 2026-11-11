#!/bin/bash
# flat barbell bench press frame F of N (P=0 lockout -> P=1 bar on the chest -> back): bench6.py + arap2.py -> w/BPk<F>.blend
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
set -a; . $S/agarre_final.env; set +a
export BARUNI=0 SKIN=cor CMASK=0 SPH=1 SR0=0.08 SR1=0.15
F=$1; N=$2; T=$(printf "%02d" $F); PF=${PFX:-BPk}; B=${BASEB:-NB_mc.blend}
P=${PP:-$(python3 -c "import math;print(round(0.5-0.5*math.cos(2*math.pi*$F/$N),4))")}
P=$P $S/venv/bin/python -I $S/bench6.py $B ${PF}_s$T.blend > r/log_${PF}$T.txt 2>&1
RESTBLEND=$B IT=1 RAD=0.22 RIN=0.12 $S/venv/bin/python -I $S/arap2.py ${PF}_s$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
rm -f ${PF}_s$T.blend; echo done $T P=$P
