#!/bin/bash
# double biceps frame F of N (P = F/N, linear; the pose script eases it): P=0 rest -> P=1 full pose  -> w/<PFX><F>.blend
# base: BASEB (NB_mc_row3.blend = man with face, armpit weights of armpitweights.py)
# chain (v5, 11-11-2026): dblbiceps.py (CoR skinning, humeral twist spread along the arm) -> arap2.py (relaxed armpit)
#   -> capkeep.py (the top of the shoulder keeps the skinned dome: round deltoid) -> elbowfix.py (biceps peak, soft elbow)
#   optional, off by default: shoulderfix.py (SFK>0), armpitfix.py (AXK>0).  v4 chain: anim_db_v4.sh
S=${GT3D:?set GT3D}; cd $S/w
set -a; . $S/agarre_final.env; set +a
export DBFX=${DBFX:-0.65}   # forearms lean ~33 deg towards the head (11-11, as in the reference photos; before 0.42)
export SHW=${SHW:-0.15} SKIN=cor CMASK=0 SPH=1 SR0=0.08 SR1=0.15 TW=${TW:-1} TW0=${TW0:-0} TB=${TB:-0.7}
F=$1; N=$2; T=$(printf "%02d" $F); PF=${PFX:-DB}; B=${BASEB:-NB_mc_row3.blend}; PY="$S/venv/bin/python -I"
P=${PP:-$(python3 -I -c "print(round($F/$N,4))")}
P=$P $PY $S/dblbiceps.py $B ${PF}_s$T.blend > r/log_${PF}$T.txt 2>&1
RESTBLEND=$B IT=1 RAD=0.22 RIN=0.12 $PY $S/arap2.py ${PF}_s$T.blend ${PF}_a$T.blend >> r/log_${PF}$T.txt 2>&1
$PY $S/capkeep.py ${PF}_s$T.blend ${PF}_a$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
[ "${SFK:-0}" != 0 ] && P=$P K=$SFK DA=0.025 DL=0 RA=0.064 RB=0.064 LOWK=0.2 $PY $S/shoulderfix.py $PF$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
[ "${AXK:-0}" != 0 ] && P=$P K=$AXK RAX=${AXR:-0.045} SM=6 $PY $S/armpitfix.py $PF$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
BAMP=${BAMP:-0.034} BS0=${BS0:-0.55} BSA=${BSA:-0.15} BSB=${BSB:-0.12} BCP=${BCP:-1} BMED=${BMED:-0.9} FAMP=${FAMP:-0.011} ESM=20 ER=0.065 EJR=0.045 $PY $S/elbowfix.py $PF$T.blend $PF$T.blend >> r/log_${PF}$T.txt 2>&1
rm -f ${PF}_s$T.blend ${PF}_a$T.blend; echo done $T P=$P
