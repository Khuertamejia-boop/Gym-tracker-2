#!/bin/bash
# one pull-up frame with the body's own hands: pose + two full views (+ hand close-ups on frames 0 and 10)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
F=$1; N=$2
P=$(python3 -c "import math;print(round(0.5-0.5*math.cos(2*math.pi*$F/$N),4))")
T=$(printf "%02d" $F)
GTA=45,35,35 TOPP=-15 P=$P $S/venv/bin/python -I $S/pullup3.py SMH_w.blend PSM_pc$T.blend >/dev/null 2>&1
for Y in -35 -90; do
 NODISC=1 SHOWBAR=1 GG=0.35 GP=1.0 AOD=0.06 AOP=2.0 LK=0.6 AMB=0.14 PIT=3 YAW=$Y RES=640 SMP=8 VIEWS=cus TZ=1.25 OSC=2.4 REDIDS=-5 LNK=0.3 SHV=0.04 $S/venv/bin/python -I $S/rendarm.py PSM_pc$T.blend r/pc${T}_$Y >/dev/null 2>&1
done
if [ "$F" = "0" ] || [ "$F" = "10" ]; then
 for Y in 0 -40; do NODISC=1 SHOWBAR=1 GG=0.35 GP=1.0 AOD=0.06 AOP=2.0 LK=0.6 AMB=0.14 PIT=3 YAW=$Y RES=700 SMP=12 VIEWS=cus TX=0.30 TY=-0.03 TZ=2.11 OSC=0.30 REDIDS=-5 LNK=0.3 SHV=0.04 $S/venv/bin/python -I $S/rendarm.py PSM_pc$T.blend r/pch${T}_$Y >/dev/null 2>&1; done
fi
echo done $T
