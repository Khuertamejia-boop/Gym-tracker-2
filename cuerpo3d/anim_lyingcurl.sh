#!/bin/bash
# lying leg curl frame F of N (P=0 legs almost straight -> P=1 heels up -> back): lyingcurl.py -> w/LYk<F>.blend
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
set -a; . $S/agarre_final.env; set +a
export SKIN=cor CMASK=0 SPH=1 SR0=0.08 SR1=0.15 HYD=1.1 FLEXA=105 HXD=0.12
F=$1; N=$2; T=$(printf "%02d" $F); PF=${PFX:-LYk}; B=${BASEB:-NB_mc_hs.blend}
P=${PP:-$(python3 -c "import math;print(round(0.5-0.5*math.cos(2*math.pi*$F/$N),4))")}
P=$P $S/venv/bin/python -I $S/lyingcurl.py $B $PF$T.blend > r/log_${PF}$T.txt 2>&1
echo done $T P=$P
