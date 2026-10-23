#!/bin/bash
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
BASE="GG=0.4 GP=1.0 AOD=0.06 AOP=2.5 LK=0.6 AMB=0.14 PIT=3 RES=1400 SMP=24 VIEWS=full LNK=0.3 SHV=0.04 REDC=0.82,0.10,0.02"
for spec in "fin_f PSM_s18 0 -" "fin_s PSM_s18 90 -" "fin_b PSM_s18 180 -"; do set -- $spec
  (env $BASE YAW=$3 REDIDS=-5 $S/venv/bin/python -I $S/rendarm.py $2.blend r/$1 2>&1 | grep Traceback) &
done; wait
(env $BASE YAW=0 HL=1 REDIDS=-5 $S/venv/bin/python -I $S/rendarm.py HLF.blend r/hlf 2>&1 | grep Traceback) &
(env $BASE YAW=180 HL=1 REDIDS=-5 $S/venv/bin/python -I $S/rendarm.py HLB.blend r/hlb 2>&1 | grep Traceback) &
wait
