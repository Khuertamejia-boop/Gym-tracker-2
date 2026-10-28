#!/bin/bash
# Face pull, final render: frames <PFX>00..10 (made by ../anim_fp.sh) -> 1920x1080, style v8 -> out/facepull.gif
#   env: PFX (default FPd), MAPS (default maps_fp2), STYLE (default style_v8), SMP (32), GIFW (GIF width, 960)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w; O=$S/ill/r/fp_final; mkdir -p $O $S/out
PF=${PFX:-FPd}; ST=${STYLE:-style_v11}
for f in 0 1 2 3 4 5 6 7 8 9 10; do T=$(printf "%02d" $f)
  env $(cat $S/ill/$ST.env) THREADS=4 MAPS=$S/ill/${MAPS:-maps_fp2} NPZ=$S/ill/pv/bla_row2.npz YAW=${YAW:-152} PIT=10 TX=0.27 TY=-0.745 TZ=0.97 OSC=3.8 RX=1920 RY=1080 SMP=${SMP:-32} $S/venv/bin/python -I $S/ill/rendsculpt.py $PF$T.blend $O/f$T 2>&1 | grep -i "traceback" -A3
  echo frame $T
done
W=${GIFW:-960} DUR=90 CROP=0 SHEET=$O/sheet.jpg python3 $S/ill/mkgif.py $S/out/facepull.gif $(for f in 0 1 2 3 4 5 6 7 8 9 10; do printf "$O/f%02d.png " $f; done)
