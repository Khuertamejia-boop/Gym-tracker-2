#!/bin/bash
# Final render of any exercise made of NF poses w/<PFX>00..NN (bottom -> top), standard look (style v8, 1920x1080),
# then the approved rhythm (fast up, slow down, pauses) as GIF + MP4:  out/<NAME>.gif, out/<NAME>.mp4
#   ill/render31.sh <PFX> <MAPS folder> <NAME>      env: YAW PIT TX TY TZ OSC (camera), SHRED (red through the shorts),
#   NF (31), SMP (32), REDO=1 (re-render existing PNGs)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
PF=$1; MP=$2; NAME=$3; NF=${NF:-31}; O=$S/ill/r/final_$NAME; mkdir -p $O $S/out
for f in $(seq 0 $((NF-1))); do T=$(printf "%02d" $f)
  [ -f $O/f$T.png ] && [ "${REDO:-0}" != 1 ] && continue
  env $(cat $S/ill/${STYLE:-style_v14}.env) THREADS=4 SHRED=${SHRED:-0} MAPS=$S/ill/$MP NPZ=$S/ill/pv/bla_row2.npz \
      YAW=${YAW:-40} PIT=${PIT:-8} TX=${TX:-0} TY=${TY:-0} TZ=${TZ:-0.86} OSC=${OSC:-3.3} RX=1920 RY=1080 SMP=${SMP:-32} \
      $S/venv/bin/python -I $S/ill/rendsculpt.py $PF$T.blend $O/f$T 2>&1 | grep -i "traceback" -A3
done
FR=$(for f in $(seq 0 $((NF-1))); do printf "$O/f%02d.png " $f; done)
SHEET=$O/sheet.jpg python3 $S/ill/mkgif2.py $S/out/$NAME.gif $FR
python3 $S/ill/mkmp4.py $S/out/$NAME.mp4 $FR
