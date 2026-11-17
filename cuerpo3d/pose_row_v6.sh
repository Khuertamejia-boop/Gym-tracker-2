#!/bin/bash
# bent-over barbell row v6 (28-10-2026): 31 poses w/<PFX>00..30 (P 0 arms hanging -> 1 bar at the lower chest), new body,
# neutral neck (NECKT=0; -40 looked at the feet), the bar never goes into the legs (barrow.py LEGPUSH) and touches higher
# (TOUCHZ 1.05; at 1.02 it was squeezed between the belly and the thighs)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S
export TLEAN=60 KNEEF=50 SPEXT=22 NECKT=0 CLR0=2 ATMAX=70 PFX=${PFX:-BRh}
for g in $(seq 0 4 30); do for f in $(seq $g $((g+3))); do [ $f -le 30 ] && ./anim_row.sh $f 60 & done; wait; done
