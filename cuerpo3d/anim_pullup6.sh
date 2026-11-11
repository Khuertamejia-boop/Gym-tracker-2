#!/bin/bash
# final pull-up pipeline: pose frame F of N (pullup6: anatomical arm + CoR shoulder skinning) -> w/NBh<F>.blend
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
set -a; . $S/agarre_final.env; set +a; export SKIN=cor TW=0
F=$1; N=$2; T=$(printf "%02d" $F)
P=$(python3 -c "import math;print(round(0.5-0.5*math.cos(2*math.pi*$F/$N),4))")
P=$P $S/venv/bin/python -I $S/pullup6.py NB_s.blend NBh$T.blend > r/log_NBh$T.txt 2>&1
echo posed $T P=$P
