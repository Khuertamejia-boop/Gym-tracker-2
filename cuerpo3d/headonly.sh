#!/bin/bash
# usage: headonly.sh <srcSM tag> <newtag>  (needs HX env) -> head + pose + close-ups
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
(eval "$HX"; $S/venv/bin/python -I scripts/headnew.py SM_$1.blend SMH_$2.blend 2>&1 | grep -i Traceback -A4)
(eval "$PX"; ROLL=-20 $S/venv/bin/python -I $S/posearm.py SMH_$2.blend PSM_$2.blend 2>&1 | grep -i Traceback -A4)
rm -f SMH_$2.blend; cd $S; ./headshots.sh PSM_$2.blend $2
