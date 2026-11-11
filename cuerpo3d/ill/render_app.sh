#!/bin/bash
# App background animation frames: poses w/<PFX>00..NN, app style (style_app.env), portrait 1200x1600, transparent,
# same camera as the «Hoy» still (back view).   ill/render_app.sh <PFX> <MAPS folder> <NAME>  -> ill/r/app_<NAME>/fNN.png
#   env: NF (31), SMP (32), YAW (180) PIT (4) TZ (0.875) OSC (1.95), REDO=1
S=${GT3D:?set GT3D}; cd $S/w
PF=$1; MP=$2; NAME=$3; NF=${NF:-31}; O=$S/ill/r/app_$NAME; mkdir -p $O
for f in $(seq 0 $((NF-1))); do T=$(printf "%02d" $f)
  [ -f $O/f$T.png ] && [ "${REDO:-0}" != 1 ] && continue
  env $(cat $S/ill/${STYLE:-style_app}.env) THREADS=4 SHOWBAR=0 HIDEBANCO=1 MAPS=$S/ill/$MP NPZ=$S/ill/pv/bla_row2.npz \
      YAW=${YAW:-180} PIT=${PIT:-4} TX=0 TY=0 TZ=${TZ:-0.875} OSC=${OSC:-1.95} RX=1200 RY=1600 SMP=${SMP:-32} \
      $S/venv/bin/python -I $S/ill/rendsculpt.py $PF$T.blend $O/f$T 2>&1 | grep -i "traceback" -A3
  echo frame $T
done
