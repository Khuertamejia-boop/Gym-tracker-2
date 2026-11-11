#!/bin/bash
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S
export TLEAN=60 KNEEF=50 SPEXT=22 NECKT=-40 CLR0=2 ATMAX=70 PFX=BRe
for f in 0 1 2 3 4 5 6 7 8 9 10; do ./anim_row.sh $f 20; done
grep -h "elbow flex\|thigh" w/r/log_BRe10.txt
