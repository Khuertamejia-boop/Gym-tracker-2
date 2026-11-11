#!/bin/bash
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w; mkdir -p $S/ill/r/row
for f in 0 1 2 3 4 5 6 7 8 9 10; do T=$(printf "%02d" $f)
  env $(cat $S/ill/row_style.env) MAPS=$S/ill/maps_bla NPZ=$S/ill/pv/bla_row2.npz $S/venv/bin/python -I $S/ill/rendill2.py BRv$T.blend $S/ill/r/row/f$T 2>&1 | grep -i "error\|traceback" -A3
  echo frame $T
done
DUR=90 SHEET=$S/ill/r/row/sheet.jpg python3 $S/ill/mkgif.py $S/ill/r/row/anim.gif $(for f in 0 1 2 3 4 5 6 7 8 9 10; do printf "$S/ill/r/row/f%02d.png " $f; done)
