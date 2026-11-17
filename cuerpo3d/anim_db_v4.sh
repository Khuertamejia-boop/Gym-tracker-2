#!/bin/bash
# back double biceps frame F of N (P = F/N, linear; the pose script eases it): P=0 rest -> P=1 full pose
# dblbiceps.py + arap2.py (shoulder skin) [+ untwist.py if UT>0] + deltbulge.py (round shoulders, DBBULGE) -> w/<PFX><F>.blend      base: BASEB (NB_mc_row3.blend = man with face)
S=${GT3D:?set GT3D}; cd $S/w
set -a; . $S/agarre_final.env; set +a
export SHW=${SHW:-0.15} SKIN=cor CMASK=0 SPH=1 SR0=0.08 SR1=0.15 TW=${TW:-1} TW0=${TW0:-0.3} TB=${TB:-0.6}   # TW: the humeral twist spreads along the arm (10-11)
F=$1; N=$2; T=$(printf "%02d" $F); PF=${PFX:-DB}; B=${BASEB:-NB_mc_row3.blend}
P=${PP:-$(python3 -c "print(round($F/$N,4))")}
P=$P $S/venv/bin/python -I $S/dblbiceps.py $B ${PF}_s$T.blend > r/log_${PF}$T.txt 2>&1
RESTBLEND=$B IT=1 RAD=0.22 RIN=0.12 $S/venv/bin/python -I $S/arap2.py ${PF}_s$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
[ "${UT:-0}" != 0 ] && UT=$UT $S/venv/bin/python -I $S/untwist.py $PF$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
[ "${DBBULGE:-0}" != 0 ] && P=$P DBBULGE=$DBBULGE DBSIG=${DBSIG:-0.05} $S/venv/bin/python -I $S/deltbulge.py $PF$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
P=$P K=${SFK:-0.8} DA=0.025 DL=0 RA=0.064 RB=0.064 LOWK=0.2 $S/venv/bin/python -I $S/shoulderfix.py $PF$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1   # round deltoid (10-11)
P=$P RAX=${AXR:-0.045} SM=6 $S/venv/bin/python -I $S/armpitfix.py $PF$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1   # hollow armpit (10-11)
BAMP=${BAMP:-0.016} ESM=20 ER=0.065 EJR=0.045 $S/venv/bin/python -I $S/elbowfix.py $PF$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1   # biceps peak + soft inner elbow (10-11)
rm -f ${PF}_s$T.blend; echo done $T P=$P
