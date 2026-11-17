#!/bin/bash
# render posed frames PREFIX00..PREFIX10 (in w/) with the anatomy-plate shader, then a ping-pong GIF
#   STYLE=style.npz OUT=name [VIEW env: YAW PIT TX TY TZ OSC] ill/anim_ill.sh PREFIX "0 1 2 ... 10"
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
P=$1; FR=${2:-"0 1 2 3 4 5 6 7 8 9 10"}; mkdir -p $S/ill/r/$OUT
for f in $FR; do T=$(printf "%02d" $f)
  NPZ=$STYLE THREADS=${THREADS:-2} $S/venv/bin/python -I $S/ill/rendill2.py $P$T.blend $S/ill/r/$OUT/f$T 2>&1 | grep -i "error\|traceback" -A3
done
python3 $S/ill/mkgif.py $S/ill/r/$OUT/anim.gif $(for f in $FR; do printf "$S/ill/r/$OUT/f%02d.png " $f; done)
