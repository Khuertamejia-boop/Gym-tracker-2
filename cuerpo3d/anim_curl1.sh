#!/bin/bash
# one-arm dumbbell curl frame F of N (P=0 arm down -> P=1 top): curl1.py + arap2.py -> w/<PFX><F>.blend
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
set -a; . $S/agarre_final.env; set +a
export SHW=${SHW:-0.15} BARUNI=0 SKIN=cor CMASK=0 SPH=1 SR0=0.08 SR1=0.15 TLEAN=0 KNEEF=4 SPEXT=0 NECKT=0 CLR0=0 CLV0=0 CLR1=0 CLV1=0 WPA=4 WFV=1e9 CARRY=0 UAX=0.20 UAXR=0.24 TH0=14
F=$1; N=$2; T=$(printf "%02d" $F); PF=${PFX:-CU1}; B=${BASEB:-NB_mc_row3.blend}
P=${PP:-$(python3 -c "import math;print(round(0.5-0.5*math.cos(2*math.pi*$F/$N),4))")}
P=$P $S/venv/bin/python -I $S/curl1.py $B ${PF}_s$T.blend > r/log_${PF}$T.txt 2>&1
RESTBLEND=$B IT=1 RAD=0.22 RIN=0.12 $S/venv/bin/python -I $S/arap2.py ${PF}_s$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
rm -f ${PF}_s$T.blend; echo done $T P=$P
