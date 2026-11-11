#!/bin/bash
# one curl frame: pose (athletic body, approved grip) + two views (three-quarter front, side)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
set -a; . $S/agarre_final.env; set +a
F=$1; N=$2
P=$(python3 -c "print(round($F/($N-1),4))")
T=$(printf "%02d" $F)
HEADR=0.047 HEADT=0.06 HANDLE=0.13 ELBIT=30 SHIT=120 P=$P $S/venv/bin/python -I $S/curl.py ${BASE:-NB_w.blend} ${PFX:-NBc}$T.blend > r/log_${PFX:-NBc}$T.txt 2>&1
R="SHOWBAR=1 GG=0.35 GP=1.0 AOD=0.06 AOP=2.0 LK=0.6 AMB=0.14 RES=600 SMP=10 VIEWS=cus REDIDS=-5 LNK=0.3 SHV=0.04"
env $R PIT=5 YAW=-25 TX=0 TY=-0.05 TZ=1.15 OSC=1.0 $S/venv/bin/python -I $S/rendarm.py ${PFX:-NBc}$T.blend r/${PFX:-NBc}${T}_f > /dev/null 2>&1
env $R PIT=3 YAW=-80 TX=0.18 TY=-0.08 TZ=1.22 OSC=0.65 $S/venv/bin/python -I $S/rendarm.py ${PFX:-NBc}$T.blend r/${PFX:-NBc}${T}_s > /dev/null 2>&1
echo done $T
