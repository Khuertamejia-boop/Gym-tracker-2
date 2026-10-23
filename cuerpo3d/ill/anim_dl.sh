#!/bin/bash
# Deadlift, final render: frames <PFX>00..10 (made by ../anim_dl.sh) -> 1920x1080, style v8, glutes red through the shorts -> out/pesomuerto.gif
#   env: PFX (default DLe), MAPS (default maps_dl), STYLE (default style_v8), SMP (32), GIFW (GIF width, 960)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w; O=$S/ill/r/dl_final; mkdir -p $O $S/out
PF=${PFX:-DLe}; ST=${STYLE:-style_v8}
for f in 0 1 2 3 4 5 6 7 8 9 10; do T=$(printf "%02d" $f)
  env $(cat $S/ill/$ST.env) THREADS=4 SHRED=${SHRED:-0.7} MAPS=$S/ill/${MAPS:-maps_dl} NPZ=$S/ill/pv/bla_row2.npz YAW=${YAW:-140} PIT=14 TX=0 TY=0 TZ=0.84 OSC=3.4 RX=1920 RY=1080 SMP=${SMP:-32} $S/venv/bin/python -I $S/ill/rendsculpt.py $PF$T.blend $O/f$T 2>&1 | grep -i "traceback" -A3
  echo frame $T
done
W=${GIFW:-960} DUR=90 CROP=0 SHEET=$O/sheet.jpg python3 $S/ill/mkgif.py $S/out/pesomuerto.gif $(for f in 0 1 2 3 4 5 6 7 8 9 10; do printf "$O/f%02d.png " $f; done)
