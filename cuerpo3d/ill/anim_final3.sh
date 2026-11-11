#!/bin/bash
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w; mkdir -p $S/ill/r/rowf3
for f in 0 1 2 3 4 5 6 7 8 9 10; do T=$(printf "%02d" $f)
  env $(cat $S/ill/style_final3.env) THREADS=4 MAPS=$S/ill/maps_final3 NPZ=$S/ill/pv/bla_row2.npz YAW=135 PIT=20 TZ=0.75 OSC=1.9 RES=1000 SMP=32 $S/venv/bin/python -I $S/ill/rendsculpt.py BRv$T.blend $S/ill/r/rowf3/f$T 2>&1 | grep -i "traceback" -A3
  echo frame $T
done
W=600 DUR=90 SHEET=$S/ill/r/rowf3/sheet.jpg python3 $S/ill/mkgif.py $S/out/remo_barra_v4.gif $(for f in 0 1 2 3 4 5 6 7 8 9 10; do printf "$S/ill/r/rowf3/f%02d.png " $f; done)
