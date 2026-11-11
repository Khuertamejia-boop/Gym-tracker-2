#!/bin/bash
# Deadlift, final render: frames <PFX>00..<NF-1> (bottom -> top, made by ../anim_dl.sh F 2*(NF-1)) -> 1920x1080, style v8,
# glutes red through the shorts -> out/pesomuerto.gif (fast up, slow down, pauses: ill/mkgif2.py)
#   env: PFX (DLf), NF (31), MAPS (maps_dl), STYLE (style_v8), SMP (32), UP/DOWN/HOLDT/HOLDB (GIF timing, ms)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w; O=$S/ill/r/dl_final; mkdir -p $O $S/out
PF=${PFX:-DLf}; ST=${STYLE:-style_v14}; NF=${NF:-31}
for f in $(seq 0 $((NF-1))); do T=$(printf "%02d" $f)
  [ -f $O/f$T.png ] && [ "${REDO:-0}" != 1 ] && continue
  env $(cat $S/ill/$ST.env) THREADS=4 SHRED=${SHRED:-0.7} MAPS=$S/ill/${MAPS:-maps_dl} NPZ=$S/ill/pv/bla_row2.npz YAW=${YAW:-140} PIT=14 TX=0 TY=0 TZ=0.84 OSC=3.4 RX=1920 RY=1080 SMP=${SMP:-32} $S/venv/bin/python -I $S/ill/rendsculpt.py $PF$T.blend $O/f$T 2>&1 | grep -i "traceback" -A3
  echo frame $T
done
SHEET=$O/sheet.jpg python3 $S/ill/mkgif2.py $S/out/pesomuerto.gif $(for f in $(seq 0 $((NF-1))); do printf "$O/f%02d.png " $f; done)
