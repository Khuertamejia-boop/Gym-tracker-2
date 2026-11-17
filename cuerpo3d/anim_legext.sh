#!/bin/bash
# leg extension frame F of N (P=0 knees bent ~95 deg -> P=1 almost straight -> back): legext.py -> w/LEk<F>.blend
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
set -a; . $S/agarre_final.env; set +a
export SKIN=cor CMASK=0 SPH=1 SR0=0.08 SR1=0.15 HY=-0.08
F=$1; N=$2; T=$(printf "%02d" $F); PF=${PFX:-LEk}; B=${BASEB:-NB_mc.blend}
P=${PP:-$(python3 -c "import math;print(round(0.5-0.5*math.cos(2*math.pi*$F/$N),4))")}
P=$P $S/venv/bin/python -I $S/legext.py $B $PF$T.blend > r/log_${PF}$T.txt 2>&1
echo done $T P=$P
