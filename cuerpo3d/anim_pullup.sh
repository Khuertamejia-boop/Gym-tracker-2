#!/bin/bash
# one frame: pose + render two views.  usage: anim_pullup.sh <frame> <nframes>
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
F=$1; N=$2
P=$(python3 -c "import math;print(round(0.5-0.5*math.cos(2*math.pi*$F/$N),4))")
T=$(printf "%02d" $F)
P=$P $S/venv/bin/python -I $S/pullup.py SMH_g.blend PSM_pa$T.blend >/dev/null 2>&1
for Y in -35 -90; do
 NODISC=1 SHOWBAR=1 GG=0.35 GP=1.0 AOD=0.06 AOP=2.0 LK=0.6 AMB=0.14 PIT=3 YAW=$Y RES=640 SMP=8 VIEWS=cus TZ=1.25 OSC=2.4 REDIDS=-5 LNK=0.3 SHV=0.04 $S/venv/bin/python -I $S/rendarm.py PSM_pa$T.blend r/pa${T}_$Y >/dev/null 2>&1
done
rm -f PSM_pa$T.blend
echo done $T
